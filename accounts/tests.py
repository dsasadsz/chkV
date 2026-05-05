import shutil
import tempfile
from datetime import timedelta
from io import BytesIO
from pathlib import Path

from PIL import Image
from django.contrib.admin.sites import site
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .models import (
    ActivityTag,
    Achievement,
    Destination,
    FlightSchedule,
    MedicalQuestionnaire,
    Notification,
    PassengerDocument,
    PreparationTask,
    Review,
    SpaceTour,
    StarSystem,
    Ticket,
    TourPackage,
    UserProfile,
)

TEST_MEDIA_ROOT = Path(tempfile.mkdtemp())


def generate_test_image(name="avatar.png", image_format="PNG"):
    buffer = BytesIO()
    image = Image.new("RGB", (120, 120), color="#3b82f6")
    image.save(buffer, format=image_format)
    return SimpleUploadedFile(
        name,
        buffer.getvalue(),
        content_type=f"image/{image_format.lower()}",
    )


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class AccountsFlowTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEST_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        # Тесты создают собственные направления, поэтому стартовые данные миграции очищаются.
        Destination.objects.all().delete()
        ActivityTag.objects.all().delete()
        StarSystem.objects.all().delete()

    def test_home_page_loads(self):
        response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Travel X")
        self.assertContains(response, "Войти")
        self.assertContains(response, "Регистрация")

    def test_authenticated_navigation_shows_dashboard_and_logout(self):
        user = User.objects.create_user(username="nav-user", password="OrbitPass123!")
        self.client.force_login(user)

        response = self.client.get(reverse("dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Личный кабинет")
        self.assertContains(response, "Выйти")

    def test_destinations_page_loads(self):
        response = self.client.get(reverse("destinations"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Космические направления")

    def test_destinations_page_uses_database_destinations_with_packages(self):
        system = StarSystem.objects.create(name="Inner planets")
        tag = ActivityTag.objects.create(name="Research")
        destination = Destination.objects.create(
            title="Mars Valley",
            description="Guided canyon expedition.",
            image="destinations/mars.jpg",
            object_type=Destination.ObjectType.PLANET,
            system=system,
        )
        destination.tags.add(tag)
        TourPackage.objects.create(
            destination=destination,
            class_type=TourPackage.ClassType.EXPLORER,
            price="120000.00",
            features="Habitat stay, rover route, science guide.",
        )

        response = self.client.get(reverse("destinations"))

        self.assertEqual(response.status_code, 200)
        self.assertQuerySetEqual(response.context["destinations"], [destination])
        self.assertContains(response, "Mars Valley")
        self.assertContains(response, "Explorer")
        self.assertContains(response, "120000,00")

    def test_destination_relations_are_available_from_orm(self):
        system = StarSystem.objects.create(name="Gas giants")
        tag = ActivityTag.objects.create(name="Relax")
        destination = Destination.objects.create(
            title="Saturn Rings",
            description="Observation cruise.",
            image="destinations/saturn.jpg",
            object_type=Destination.ObjectType.ORBITAL_STATION,
            system=system,
        )
        destination.tags.add(tag)
        package = TourPackage.objects.create(
            destination=destination,
            class_type=TourPackage.ClassType.FIRST_CLASS,
            price="500000.00",
            features="Panoramic cabin, concierge, chef menu.",
        )

        loaded_destination = Destination.objects.select_related("system").prefetch_related("tags", "packages").get()

        self.assertEqual(loaded_destination.system, system)
        self.assertQuerySetEqual(loaded_destination.tags.all(), [tag])
        self.assertQuerySetEqual(loaded_destination.packages.all(), [package])

    def test_destinations_page_filters_by_system_tag_and_object_type(self):
        inner_system = StarSystem.objects.create(name="Inner planets")
        deep_system = StarSystem.objects.create(name="Deep space")
        research_tag = ActivityTag.objects.create(name="Research")
        relax_tag = ActivityTag.objects.create(name="Relax")
        matching_destination = Destination.objects.create(
            title="Moon Base",
            description="Calm research route.",
            image="destinations/moon.jpg",
            object_type=Destination.ObjectType.SATELLITE,
            system=inner_system,
        )
        matching_destination.tags.add(research_tag)
        non_matching_destination = Destination.objects.create(
            title="Alpha Centauri",
            description="Long-range expedition.",
            image="destinations/alpha.jpg",
            object_type=Destination.ObjectType.PLANET,
            system=deep_system,
        )
        non_matching_destination.tags.add(relax_tag)

        response = self.client.get(
            reverse("destinations"),
            {
                "system": str(inner_system.pk),
                "tag": str(research_tag.pk),
                "object_type": Destination.ObjectType.SATELLITE,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertQuerySetEqual(response.context["destinations"], [matching_destination])
        self.assertQuerySetEqual(response.context["systems"], [deep_system, inner_system])
        self.assertQuerySetEqual(response.context["tags"], [relax_tag, research_tag])
        self.assertEqual(response.context["object_types"], Destination.ObjectType.choices)
        self.assertEqual(
            response.context["selected_filters"],
            {
                "system": str(inner_system.pk),
                "tag": str(research_tag.pk),
                "object_type": Destination.ObjectType.SATELLITE,
            },
        )
        self.assertContains(response, "Moon Base")
        self.assertNotContains(response, "Alpha Centauri")
        self.assertContains(response, 'option value="satellite" selected')

    def test_destinations_page_accepts_text_system_alias_from_solar_scene(self):
        system = StarSystem.objects.create(name="Inner planets")
        mars_destination = Destination.objects.create(
            title="Mars Valley",
            description="Mars route.",
            image="destinations/mars.jpg",
            object_type=Destination.ObjectType.PLANET,
            system=system,
        )
        Destination.objects.create(
            title="Moon Base",
            description="Moon route.",
            image="destinations/moon.jpg",
            object_type=Destination.ObjectType.SATELLITE,
            system=system,
        )

        response = self.client.get(reverse("destinations"), {"system": "mars"})

        self.assertEqual(response.status_code, 200)
        self.assertQuerySetEqual(response.context["destinations"], [mars_destination])
        self.assertContains(response, "Mars Valley")
        self.assertNotContains(response, "Moon Base")

    def test_space_tour_detail_page_loads_active_tour(self):
        tour = SpaceTour.objects.create(
            title="Марсианский рассвет",
            planet="Марс",
            price="125000.00",
            description="Экспедиционный тур к марсианским каньонам.",
            is_active=True,
        )

        response = self.client.get(reverse("tour_detail", args=[tour.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Марсианский рассвет")
        self.assertContains(response, "Марс")
        self.assertContains(response, "125000,00")
        self.assertContains(response, "Экспедиционный тур")
        self.assertEqual(str(tour), "Марсианский рассвет — Марс")

    def test_register_creates_user_profile_and_logs_user_in(self):
        response = self.client.post(
            reverse("register"),
            {
                "username": "spacepilot",
                "email": "spacepilot@example.com",
                "age": 24,
                "password1": "OrbitPass123!",
                "password2": "OrbitPass123!",
                "profile_image": generate_test_image(),
            },
            follow=True,
        )

        self.assertRedirects(response, reverse("registration_success"))
        user = User.objects.get(username="spacepilot")

        self.assertTrue(UserProfile.objects.filter(user=user, age=24).exists())
        self.assertTrue(user.profile.profile_image.name.startswith(f"profile_photos/user_{user.id}/"))
        self.assertEqual(int(self.client.session["_auth_user_id"]), user.id)

    def test_authenticated_user_can_update_profile_photo(self):
        User.objects.create_user(
            username="marsuser",
            email="marsuser@example.com",
            password="OrbitPass123!",
        )
        self.client.login(username="marsuser", password="OrbitPass123!")

        response = self.client.post(
            reverse("update_profile_photo"),
            {"profile_image": generate_test_image(name="profile.webp", image_format="WEBP")},
            follow=True,
        )

        user = User.objects.get(username="marsuser")
        self.assertRedirects(response, reverse("dashboard"))
        self.assertTrue(user.profile.profile_image.name.endswith(".webp"))
        self.assertContains(response, "Фото профиля обновлено")

    def test_staff_page_is_forbidden_for_regular_user(self):
        User.objects.create_user(
            username="traveler",
            email="traveler@example.com",
            password="OrbitPass123!",
        )
        self.client.login(username="traveler", password="OrbitPass123!")

        response = self.client.get(reverse("staff_home"))

        self.assertEqual(response.status_code, 403)

    def test_staff_page_loads_for_admin(self):
        User.objects.create_superuser(
            username="chief",
            email="chief@example.com",
            password="OrbitPass123!",
        )
        self.client.login(username="chief", password="OrbitPass123!")

        response = self.client.get(reverse("staff_home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Конфиденциальная панель")

    def test_authenticated_user_can_book_ticket_and_get_qr_code(self):
        user = User.objects.create_user(
            username="ticketuser",
            email="ticketuser@example.com",
            password="OrbitPass123!",
        )
        user.profile.psych_quiz_passed = True
        user.profile.save(update_fields=["psych_quiz_passed"])
        system = StarSystem.objects.create(name="Inner planets")
        destination = Destination.objects.create(
            title="Moon Base",
            description="Training route.",
            image="destinations/moon.jpg",
            object_type=Destination.ObjectType.SATELLITE,
            system=system,
        )
        package = TourPackage.objects.create(
            destination=destination,
            class_type=TourPackage.ClassType.EXPLORER,
            price="85000.00",
            features="Base landing and personal instructor.",
        )
        schedule = FlightSchedule.objects.create(
            destination=destination,
            departure_at="2026-06-10T09:30:00+05:00",
            available_seats=2,
        )
        self.client.force_login(user)

        response = self.client.post(
            reverse("book_ticket"),
            {"package_id": package.pk, "schedule_id": schedule.pk},
            follow=True,
        )

        ticket = Ticket.objects.get(user=user)
        schedule.refresh_from_db()
        self.assertRedirects(response, reverse("dashboard"))
        self.assertEqual(ticket.status, Ticket.TicketStatus.PAID)
        self.assertEqual(ticket.package, package)
        self.assertEqual(ticket.flight_schedule, schedule)
        self.assertEqual(schedule.available_seats, 1)
        self.assertTrue(ticket.qr_code.name.startswith(f"ticket_qr/user_{user.id}/"))
        self.assertTrue((TEST_MEDIA_ROOT / ticket.qr_code.name).exists())
        self.assertContains(response, "Билет успешно оформлен")
        self.assertContains(response, "Moon Base")

    def test_book_tour_api_requires_authenticated_user(self):
        response = self.client.post(reverse("book_tour_api"), {"package_id": 1, "schedule_id": 1})

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["status"], "error")
        self.assertIn("login_url", response.json())

    def test_book_tour_api_creates_paid_ticket(self):
        user = User.objects.create_user(
            username="api-ticket-user",
            email="api-ticket@example.com",
            password="OrbitPass123!",
        )
        system = StarSystem.objects.create(name="API system")
        destination = Destination.objects.create(
            title="API Moon Base",
            description="One-click booking route.",
            image="destinations/api-moon.jpg",
            object_type=Destination.ObjectType.SATELLITE,
            system=system,
        )
        package = TourPackage.objects.create(
            destination=destination,
            class_type=TourPackage.ClassType.EXPLORER,
            price="87000.00",
            features="Fast booking package.",
        )
        schedule = FlightSchedule.objects.create(
            destination=destination,
            departure_at=timezone.now() + timedelta(days=30),
            available_seats=2,
        )
        self.client.force_login(user)

        response = self.client.post(
            reverse("book_tour_api"),
            {"package_id": package.pk, "schedule_id": schedule.pk},
        )

        data = response.json()
        ticket = Ticket.objects.get(user=user)
        schedule.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["ticket_id"], ticket.id)
        self.assertEqual(ticket.status, Ticket.TicketStatus.PAID)
        self.assertEqual(ticket.package, package)
        self.assertEqual(ticket.flight_schedule, schedule)
        self.assertEqual(schedule.available_seats, 1)

    def test_first_ticket_requires_psych_quiz_then_books_pending_choice(self):
        user = User.objects.create_user(
            username="quiz-ticket-user",
            email="quiz-ticket@example.com",
            password="OrbitPass123!",
        )
        system = StarSystem.objects.create(name="Quiz system")
        destination = Destination.objects.create(
            title="Europa Training Orbit",
            description="Psychological readiness route.",
            image="destinations/europa-training.jpg",
            object_type=Destination.ObjectType.SATELLITE,
            system=system,
        )
        package = TourPackage.objects.create(
            destination=destination,
            class_type=TourPackage.ClassType.EXPLORER,
            price="99000.00",
            features="Training orbit and instructor.",
        )
        schedule = FlightSchedule.objects.create(
            destination=destination,
            departure_at=timezone.now() + timedelta(days=45),
            available_seats=2,
        )
        self.client.force_login(user)

        first_response = self.client.post(
            reverse("book_ticket"),
            {"package_id": package.pk, "schedule_id": schedule.pk},
        )

        self.assertRedirects(first_response, reverse("psych_quiz"))
        self.assertFalse(Ticket.objects.filter(user=user).exists())
        schedule.refresh_from_db()
        self.assertEqual(schedule.available_seats, 2)

        quiz_response = self.client.post(
            reverse("psych_quiz"),
            {f"q{index}": "1" for index in range(7)},
            follow=True,
        )

        ticket = Ticket.objects.get(user=user)
        schedule.refresh_from_db()
        user.profile.refresh_from_db()
        self.assertRedirects(quiz_response, reverse("dashboard"))
        self.assertTrue(user.profile.psych_quiz_passed)
        self.assertEqual(ticket.status, Ticket.TicketStatus.PAID)
        self.assertEqual(ticket.package, package)
        self.assertEqual(ticket.flight_schedule, schedule)
        self.assertEqual(schedule.available_seats, 1)
        self.assertContains(quiz_response, "Тест пройден")

    def test_psych_quiz_rejects_low_score_and_keeps_booking_pending(self):
        user = User.objects.create_user(username="low-score-user", password="OrbitPass123!")
        session = self.client.session
        session["pending_booking"] = {"package_id": 10, "schedule_id": 20}
        session.save()
        self.client.force_login(user)

        response = self.client.post(
            reverse("psych_quiz"),
            {f"q{index}": "0" for index in range(7)},
            follow=True,
        )

        user.profile.refresh_from_db()
        self.assertFalse(user.profile.psych_quiz_passed)
        self.assertEqual(self.client.session["pending_booking"], {"package_id": 10, "schedule_id": 20})
        self.assertContains(response, "нужно набрать минимум")

    def test_destinations_page_shows_available_seats_badge_and_sold_out_button(self):
        user = User.objects.create_user(username="seat-viewer", password="OrbitPass123!")
        user.profile.psych_quiz_passed = True
        user.profile.save(update_fields=["psych_quiz_passed"])
        system = StarSystem.objects.create(name="Seat system")
        destination = Destination.objects.create(
            title="Ganymede Dock",
            description="Seats route.",
            image="destinations/ganymede.jpg",
            object_type=Destination.ObjectType.SATELLITE,
            system=system,
        )
        package = TourPackage.objects.create(
            destination=destination,
            class_type=TourPackage.ClassType.ECONOMY,
            price="50000.00",
            features="Dock transfer.",
        )
        FlightSchedule.objects.create(
            destination=destination,
            departure_at=timezone.now() + timedelta(days=10),
            available_seats=0,
        )
        self.client.force_login(user)

        response = self.client.get(reverse("destinations"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Осталось мест: 0")
        self.assertContains(response, "Sold Out")
        self.assertContains(response, 'class="seat-badge is-empty"')

    def test_dashboard_passes_user_tickets(self):
        user = User.objects.create_user(
            username="dashboard-ticket-user",
            email="dashboard@example.com",
            password="OrbitPass123!",
        )
        other_user = User.objects.create_user(
            username="other-ticket-user",
            email="other@example.com",
            password="OrbitPass123!",
        )
        system = StarSystem.objects.create(name="Deep space")
        destination = Destination.objects.create(
            title="Alpha Station",
            description="Orbital stay.",
            image="destinations/alpha.jpg",
            object_type=Destination.ObjectType.ORBITAL_STATION,
            system=system,
        )
        package = TourPackage.objects.create(
            destination=destination,
            class_type=TourPackage.ClassType.FIRST_CLASS,
            price="1500000.00",
            features="Private cabin.",
        )
        schedule = FlightSchedule.objects.create(
            destination=destination,
            departure_at="2026-07-01T14:00:00+05:00",
            available_seats=5,
        )
        ticket = Ticket.objects.create(
            user=user,
            package=package,
            flight_schedule=schedule,
            status=Ticket.TicketStatus.PAID,
        )
        Ticket.objects.create(
            user=other_user,
            package=package,
            flight_schedule=schedule,
            status=Ticket.TicketStatus.PAID,
        )
        self.client.force_login(user)

        response = self.client.get(reverse("dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertQuerySetEqual(response.context["tickets"], [ticket])
        self.assertContains(response, "Alpha Station")
        self.assertContains(response, "Посадочный талон")

    def test_cancel_ticket_marks_ticket_cancelled_and_notifies_close_departure(self):
        user = User.objects.create_user(username="cancel-user", password="OrbitPass123!")
        system = StarSystem.objects.create(name="Refund system")
        destination = Destination.objects.create(
            title="Near Moon Transfer",
            description="Short notice flight.",
            image="destinations/near-moon.jpg",
            object_type=Destination.ObjectType.SATELLITE,
            system=system,
        )
        package = TourPackage.objects.create(
            destination=destination,
            class_type=TourPackage.ClassType.EXPLORER,
            price="90000.00",
            features="Quick launch.",
        )
        schedule = FlightSchedule.objects.create(
            destination=destination,
            departure_at=timezone.now() + timedelta(days=3),
            available_seats=4,
        )
        ticket = Ticket.objects.create(
            user=user,
            package=package,
            flight_schedule=schedule,
            status=Ticket.TicketStatus.PAID,
        )
        self.client.force_login(user)

        response = self.client.post(
            reverse("cancel_ticket", args=[ticket.pk]),
            {"cancellation_reason": "Изменились планы"},
        )

        ticket.refresh_from_db()
        self.assertRedirects(response, reverse("dashboard"))
        self.assertEqual(ticket.status, Ticket.TicketStatus.CANCELLED)
        self.assertEqual(ticket.cancellation_reason, "Изменились планы")
        self.assertTrue(
            Notification.objects.filter(
                user=user,
                text__icontains="возврат средств составит 50%",
            ).exists()
        )

    def test_download_ticket_pdf_requires_paid_ticket_and_returns_attachment(self):
        user = User.objects.create_user(
            username="pdf-user",
            first_name="Ada",
            last_name="Astra",
            password="OrbitPass123!",
        )
        system = StarSystem.objects.create(name="PDF system")
        destination = Destination.objects.create(
            title="Mars Gate",
            description="PDF route.",
            image="destinations/pdf-mars.jpg",
            object_type=Destination.ObjectType.PLANET,
            system=system,
        )
        package = TourPackage.objects.create(
            destination=destination,
            class_type=TourPackage.ClassType.FIRST_CLASS,
            price="250000.00",
            features="PDF boarding.",
        )
        schedule = FlightSchedule.objects.create(
            destination=destination,
            departure_at=timezone.now() + timedelta(days=30),
            available_seats=2,
        )
        paid_ticket = Ticket.objects.create(
            user=user,
            package=package,
            flight_schedule=schedule,
            status=Ticket.TicketStatus.PAID,
        )
        pending_ticket = Ticket.objects.create(
            user=user,
            package=package,
            flight_schedule=schedule,
            status=Ticket.TicketStatus.PENDING,
        )
        self.client.force_login(user)

        response = self.client.get(reverse("download_ticket_pdf", args=[paid_ticket.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertIn("attachment", response["Content-Disposition"])
        self.assertIn(str(paid_ticket.ticket_number), response["Content-Disposition"])
        self.assertTrue(response.content.startswith(b"%PDF"))

        blocked_response = self.client.get(reverse("download_ticket_pdf", args=[pending_ticket.pk]))
        self.assertEqual(blocked_response.status_code, 404)

    def test_user_can_review_destination_only_after_ticket_purchase(self):
        user = User.objects.create_user(
            username="reviewer",
            email="reviewer@example.com",
            password="OrbitPass123!",
        )
        system = StarSystem.objects.create(name="Review system")
        destination = Destination.objects.create(
            title="Europa Ice Route",
            description="Ice field expedition.",
            image="destinations/europa.jpg",
            object_type=Destination.ObjectType.SATELLITE,
            system=system,
        )
        package = TourPackage.objects.create(
            destination=destination,
            class_type=TourPackage.ClassType.EXPLORER,
            price="99000.00",
            features="Subsurface ocean briefing.",
        )
        schedule = FlightSchedule.objects.create(
            destination=destination,
            departure_at="2026-08-05T11:00:00+05:00",
            available_seats=3,
        )
        self.client.force_login(user)

        blocked_response = self.client.post(
            reverse("add_review", args=[destination.pk]),
            {"rating": 5, "text": "Fantastic route."},
            follow=True,
        )

        self.assertFalse(Review.objects.filter(user=user, destination=destination).exists())
        self.assertContains(blocked_response, "Отзыв можно оставить только после покупки билета")

        Ticket.objects.create(
            user=user,
            package=package,
            flight_schedule=schedule,
            status=Ticket.TicketStatus.PAID,
        )
        allowed_response = self.client.post(
            reverse("add_review", args=[destination.pk]),
            {"rating": 5, "text": "Fantastic route."},
            follow=True,
        )

        review = Review.objects.get(user=user, destination=destination)
        self.assertRedirects(allowed_response, reverse("destinations"))
        self.assertEqual(review.rating, 5)
        self.assertEqual(review.text, "Fantastic route.")
        self.assertContains(allowed_response, "Отзыв опубликован")

    def test_home_shows_top_three_destinations_by_average_rating(self):
        system = StarSystem.objects.create(name="Rated system")
        user_one = User.objects.create_user(username="one", password="OrbitPass123!")
        user_two = User.objects.create_user(username="two", password="OrbitPass123!")
        ratings = [
            ("Mars", [5, 5]),
            ("Moon", [4, 5]),
            ("Venus", [3, 4]),
            ("Asteroid", [1, 2]),
        ]
        destinations = []
        for title, destination_ratings in ratings:
            destination = Destination.objects.create(
                title=title,
                description=f"{title} route.",
                image=f"destinations/{title.lower()}.jpg",
                object_type=Destination.ObjectType.PLANET,
                system=system,
            )
            destinations.append(destination)
            Review.objects.create(user=user_one, destination=destination, rating=destination_ratings[0], text="Good.")
            Review.objects.create(user=user_two, destination=destination, rating=destination_ratings[1], text="Nice.")

        response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 200)
        self.assertQuerySetEqual(
            response.context["popular_destinations"],
            destinations[:3],
            transform=lambda destination: destination,
        )
        self.assertContains(response, "Популярные направления")
        self.assertContains(response, "★★★★★")
        self.assertContains(response, "Mars")
        self.assertNotContains(response, "Asteroid")

    def test_paid_mars_ticket_awards_first_flight_and_mars_achievements(self):
        user = User.objects.create_user(username="mars-achiever", password="OrbitPass123!")
        system = StarSystem.objects.create(name="Inner planets")
        destination = Destination.objects.create(
            title="Долина Маринер на Марсе",
            description="Mars canyon expedition.",
            image="destinations/mars.jpg",
            object_type=Destination.ObjectType.PLANET,
            system=system,
        )
        package = TourPackage.objects.create(
            destination=destination,
            class_type=TourPackage.ClassType.EXPLORER,
            price="120000.00",
            features="Rover route.",
        )
        schedule = FlightSchedule.objects.create(
            destination=destination,
            departure_at="2026-09-01T10:00:00+05:00",
            available_seats=8,
        )

        Ticket.objects.create(
            user=user,
            package=package,
            flight_schedule=schedule,
            status=Ticket.TicketStatus.PAID,
        )

        achievement_titles = set(user.profile.achievements.values_list("title", flat=True))
        self.assertIn("Первый старт", achievement_titles)
        self.assertIn("Покоритель Марса", achievement_titles)

    def test_six_paid_tickets_award_vip_achievement(self):
        user = User.objects.create_user(username="vip-achiever", password="OrbitPass123!")
        system = StarSystem.objects.create(name="VIP routes")
        destination = Destination.objects.create(
            title="Лунная база Альфа",
            description="Moon route.",
            image="destinations/moon.jpg",
            object_type=Destination.ObjectType.SATELLITE,
            system=system,
        )
        package = TourPackage.objects.create(
            destination=destination,
            class_type=TourPackage.ClassType.ECONOMY,
            price="50000.00",
            features="Orbital pass.",
        )
        schedule = FlightSchedule.objects.create(
            destination=destination,
            departure_at="2026-10-01T09:00:00+05:00",
            available_seats=10,
        )

        for _ in range(6):
            Ticket.objects.create(
                user=user,
                package=package,
                flight_schedule=schedule,
                status=Ticket.TicketStatus.PAID,
            )

        self.assertTrue(user.profile.achievements.filter(title="VIP-путешественник").exists())

    def test_dashboard_shows_user_achievement_badges(self):
        user = User.objects.create_user(username="badge-user", password="OrbitPass123!")
        achievement = Achievement.objects.create(
            title="Первый старт",
            description="Первый оформленный билет Travel X.",
            icon="achievements/first-start.png",
        )
        user.profile.achievements.add(achievement)
        self.client.force_login(user)

        response = self.client.get(reverse("dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Мои достижения")
        self.assertContains(response, "Первый старт")
        self.assertContains(response, "Первый оформленный билет Travel X.")

    def test_post_purchase_models_store_passenger_preparation_and_notifications(self):
        user = User.objects.create_user(username="post-purchase-user", password="OrbitPass123!")
        system = StarSystem.objects.create(name="Cabinet routes")
        destination = Destination.objects.create(
            title="Orbital Hotel",
            description="Orbital stay.",
            image="destinations/orbit.jpg",
            object_type=Destination.ObjectType.ORBITAL_STATION,
            system=system,
        )
        package = TourPackage.objects.create(
            destination=destination,
            class_type=TourPackage.ClassType.FIRST_CLASS,
            price="200000.00",
            features="Full training package.",
        )
        schedule = FlightSchedule.objects.create(
            destination=destination,
            departure_at="2026-11-01T09:00:00+05:00",
            available_seats=3,
        )
        ticket = Ticket.objects.create(user=user, package=package, flight_schedule=schedule)

        document = PassengerDocument.objects.create(
            user=user,
            passport_number="PX1234567",
            citizenship="Kazakhstan",
        )
        questionnaire = MedicalQuestionnaire.objects.create(
            user=user,
            height_cm=180,
            weight_kg=78,
            has_chronic_diseases=False,
        )
        task = PreparationTask.objects.create(
            ticket=ticket,
            title="Пройти центрифугу",
            is_completed=True,
        )
        notification = Notification.objects.create(
            user=user,
            text="Ваш медицинский опросник отправлен на проверку.",
        )

        self.assertEqual(ticket.status, Ticket.TicketStatus.PENDING)
        self.assertEqual(ticket.cancellation_reason, "")
        self.assertEqual(str(document), "Документы post-purchase-user: PX1234567")
        self.assertEqual(questionnaire.clearance_status, MedicalQuestionnaire.ClearanceStatus.PENDING)
        self.assertEqual(str(task), "Пройти центрифугу - выполнено")
        self.assertFalse(notification.is_read)

    def test_dashboard_passes_post_purchase_context(self):
        user = User.objects.create_user(username="dashboard-context-user", password="OrbitPass123!")
        system = StarSystem.objects.create(name="Context routes")
        destination = Destination.objects.create(
            title="Lunar Lab",
            description="Context route.",
            image="destinations/lunar-lab.jpg",
            object_type=Destination.ObjectType.SATELLITE,
            system=system,
        )
        package = TourPackage.objects.create(
            destination=destination,
            class_type=TourPackage.ClassType.EXPLORER,
            price="99000.00",
            features="Training context.",
        )
        schedule = FlightSchedule.objects.create(
            destination=destination,
            departure_at=timezone.now() + timedelta(days=20),
            available_seats=5,
        )
        ticket = Ticket.objects.create(
            user=user,
            package=package,
            flight_schedule=schedule,
            status=Ticket.TicketStatus.PAID,
        )
        PassengerDocument.objects.create(user=user, passport_number="TRX777", citizenship="Kazakhstan")
        questionnaire = MedicalQuestionnaire.objects.create(
            user=user,
            height_cm=172,
            weight_kg=70,
            has_chronic_diseases=False,
            clearance_status=MedicalQuestionnaire.ClearanceStatus.APPROVED,
        )
        unread_notification = Notification.objects.create(user=user, text="Новая задача подготовки.")
        Notification.objects.create(user=user, text="Старое уведомление.", is_read=True)
        PreparationTask.objects.create(ticket=ticket, title="Пройти центрифугу", is_completed=True)
        PreparationTask.objects.create(ticket=ticket, title="Сдать анализы", is_completed=True)
        PreparationTask.objects.create(ticket=ticket, title="Инструктаж", is_completed=False)
        self.client.force_login(user)

        response = self.client.get(reverse("dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertQuerySetEqual(response.context["ticket_history"], [ticket])
        self.assertQuerySetEqual(response.context["unread_notifications"], [unread_notification])
        self.assertEqual(response.context["medical_questionnaire"], questionnaire)
        self.assertEqual(response.context["preparation_progress_percent"], 67)

    def test_post_purchase_models_are_registered_in_admin(self):
        self.assertIn(PassengerDocument, site._registry)
        self.assertIn(MedicalQuestionnaire, site._registry)
        self.assertIn(PreparationTask, site._registry)
        self.assertIn(Notification, site._registry)
