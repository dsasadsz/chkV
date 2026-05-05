import json
from datetime import timedelta
from io import BytesIO
from pathlib import Path

import qrcode
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Avg, Q
from django.http import Http404, HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from .forms import ProfileImageForm, SignUpForm, StyledAuthenticationForm
from .models import (
    ActivityTag,
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

TRAVEL_FEATURES = [
    {
        "icon": "rocket",
        "title": "Безопасные перелеты",
        "description": "Полетные маршруты и подготовка путешественников рассчитаны на комфортное и безопасное путешествие.",
    },
    {
        "icon": "sparkles",
        "title": "Премиальный сервис",
        "description": "Панорамные каюты, космический консьерж и сопровождение на каждом этапе путешествия.",
    },
    {
        "icon": "globe",
        "title": "Редкие направления",
        "description": "Марс, орбита Юпитера, кольца Сатурна и другие направления для будущих космотуристов.",
    },
]

QUIZ_QUESTIONS = [
    {
        "title": "Что вы сделаете, если связь с центром временно пропадет?",
        "options": [
            {"label": "Начну паниковать", "score": 0},
            {"label": "Буду ждать без действий", "score": 0},
            {"label": "Перейду к резервному протоколу и инструкции", "score": 1},
            {"label": "Открою шлюз вручную", "score": 0},
        ],
    },
    {
        "title": "Как вы ведете себя в ограниченном пространстве во время долгого полета?",
        "options": [
            {"label": "Сохраняю спокойствие и режим", "score": 1},
            {"label": "Раздражаюсь на всех вокруг", "score": 0},
            {"label": "Игнорирую команду", "score": 0},
            {"label": "Постоянно нарушаю инструкции", "score": 0},
        ],
    },
    {
        "title": "Что важнее во время миссии?",
        "options": [
            {"label": "Импровизация без правил", "score": 0},
            {"label": "Командная координация и дисциплина", "score": 1},
            {"label": "Только личный комфорт", "score": 0},
            {"label": "Полный отказ от плана", "score": 0},
        ],
    },
    {
        "title": "Если вы почувствуете перегрузку, как поступите?",
        "options": [
            {"label": "Скрою проблему", "score": 0},
            {"label": "Сообщу инструктору и выполню рекомендации", "score": 1},
            {"label": "Попробую резко встать", "score": 0},
            {"label": "Ничего не буду делать", "score": 0},
        ],
    },
    {
        "title": "Как вы относитесь к чек-листам безопасности?",
        "options": [
            {"label": "Следую им внимательно", "score": 1},
            {"label": "Считаю их лишними", "score": 0},
            {"label": "Читаю только в конце", "score": 0},
            {"label": "Передаю эту задачу другим", "score": 0},
        ],
    },
    {
        "title": "Если в команде возник спор, что вы сделаете?",
        "options": [
            {"label": "Усиливаю конфликт", "score": 0},
            {"label": "Помогаю спокойно договориться", "score": 1},
            {"label": "Игнорирую ситуацию", "score": 0},
            {"label": "Ухожу без объяснений", "score": 0},
        ],
    },
    {
        "title": "Что для вас главное в космическом путешествии?",
        "options": [
            {"label": "Ответственность, впечатления и соблюдение правил", "score": 1},
            {"label": "Риск ради острых ощущений", "score": 0},
            {"label": "Нарушение маршрута", "score": 0},
            {"label": "Отказ от инструктажа", "score": 0},
        ],
    },
]


def get_pdf_font_name():
    """Возвращает шрифт с поддержкой кириллицы, если он доступен в системе."""

    font_name = "TravelXPdfFont"
    if font_name in pdfmetrics.getRegisteredFontNames():
        return font_name

    for font_path in (
        Path("C:/Windows/Fonts/arial.ttf"),
        Path("C:/Windows/Fonts/dejavusans.ttf"),
    ):
        if font_path.exists():
            pdfmetrics.registerFont(TTFont(font_name, str(font_path)))
            return font_name

    return "Helvetica"


def get_preparation_progress_percent(user):
    tasks = PreparationTask.objects.filter(ticket__user=user)
    total_tasks = tasks.count()
    if total_tasks == 0:
        return 0

    completed_tasks = tasks.filter(is_completed=True).count()
    return round(completed_tasks / total_tasks * 100)


def get_public_stats():
    return {
        "travellers_count": User.objects.count(),
        "photos_count": UserProfile.objects.filter(profile_image__isnull=False).exclude(profile_image="").count(),
    }


def create_paid_ticket_for_booking(user, package_id, schedule_id):
    """Создает оплаченный билет и атомарно списывает одно свободное место."""

    if not package_id or not schedule_id:
        raise ValueError("Выберите тариф и рейс для оформления билета.")

    with transaction.atomic():
        package = get_object_or_404(TourPackage.objects.select_related("destination"), pk=package_id)
        schedule = get_object_or_404(
            FlightSchedule.objects.select_for_update().select_related("destination"),
            pk=schedule_id,
        )

        if package.destination_id != schedule.destination_id:
            raise ValueError("Выбранный тариф не относится к этому рейсу.")

        if schedule.available_seats <= 0:
            raise ValueError("На выбранный рейс больше нет свободных мест.")

        schedule.available_seats -= 1
        schedule.save(update_fields=["available_seats", "updated_at"])

        return Ticket.objects.create(
            user=user,
            package=package,
            flight_schedule=schedule,
            status=Ticket.TicketStatus.PAID,
        )


def calculate_quiz_score(post_data):
    """Считает баллы психо-теста и проверяет, что пользователь ответил на все вопросы."""

    score = 0
    for index, _question in enumerate(QUIZ_QUESTIONS):
        raw_answer = post_data.get(f"q{index}")
        if raw_answer is None:
            raise ValueError("Ответьте на все вопросы теста.")

        try:
            score += int(raw_answer)
        except (TypeError, ValueError):
            raise ValueError("В тесте найден некорректный ответ.")

    return score


def home(request):
    popular_destinations = (
        Destination.objects.annotate(avg_rating=Avg("reviews__rating"))
        .filter(avg_rating__isnull=False)
        .select_related("system")
        .order_by("-avg_rating", "title")[:3]
    )
    for destination in popular_destinations:
        rounded_rating = round(destination.avg_rating or 0)
        destination.rating_stars = "★" * rounded_rating + "☆" * (5 - rounded_rating)

    context = {
        **get_public_stats(),
        "features": TRAVEL_FEATURES,
        "popular_destinations": popular_destinations,
    }
    return render(request, "accounts/public_home.html", context)


def destinations_view(request):
    # Базовый QuerySet сразу подготавливает связанные данные для карточек тура.
    destinations = (
        Destination.objects.annotate(avg_rating=Avg("reviews__rating"))
        .prefetch_related(
            "packages",
            "tags",
            "flight_schedules",
            "reviews__user",
        )
        .select_related("system")
        .all()
    )
    selected_filters = {
        "system": request.GET.get("system", ""),
        "tag": request.GET.get("tag", ""),
        "object_type": request.GET.get("object_type", ""),
    }

    # Фильтры применяются только если соответствующий GET-параметр передан.
    if selected_filters["system"]:
        system_filter = selected_filters["system"]
        if system_filter.isdigit():
            destinations = destinations.filter(system_id=system_filter)
        else:
            destinations = destinations.filter(
                Q(system__name__icontains=system_filter)
                | Q(title__icontains=system_filter)
            )
    if selected_filters["tag"]:
        destinations = destinations.filter(tags__id=selected_filters["tag"])
    if selected_filters["object_type"]:
        destinations = destinations.filter(object_type=selected_filters["object_type"])

    flown_destination_ids = set()
    if request.user.is_authenticated:
        flown_destination_ids = set(
            Ticket.objects.filter(user=request.user)
            .values_list("flight_schedule__destination_id", flat=True)
            .distinct()
        )

    # Флаг нужен только для шаблона: сама защита отзыва остается во view add_review.
    for destination in destinations:
        rounded_rating = round(destination.avg_rating or 0)
        destination.rating_stars = "★" * rounded_rating + "☆" * (5 - rounded_rating)
        destination.user_can_review = destination.id in flown_destination_ids
        destination.has_available_seats = any(
            schedule.available_seats > 0 for schedule in destination.flight_schedules.all()
        )

    context = {
        "destinations": destinations,
        "systems": StarSystem.objects.all(),
        "tags": ActivityTag.objects.all(),
        "object_types": Destination.ObjectType.choices,
        "selected_filters": selected_filters,
        "quiz_questions": QUIZ_QUESTIONS,
    }
    return render(request, "accounts/destinations.html", context)


def tour_detail_view(request, tour_id):
    tour = get_object_or_404(SpaceTour, pk=tour_id, is_active=True)
    return render(request, "accounts/tour_detail.html", {"tour": tour})


@login_required
def registration_success_view(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    return render(request, "accounts/registration_success.html", {"profile": profile})


@login_required
def staff_home(request):
    if not request.user.is_staff:
        raise PermissionDenied

    recent_users = User.objects.select_related("profile").order_by("-date_joined")[:6]
    context = {
        **get_public_stats(),
        "recent_users": recent_users,
        "profiles_with_photo": UserProfile.objects.filter(profile_image__isnull=False).exclude(profile_image="").order_by("-updated_at")[:6],
    }
    return render(request, "accounts/home.html", context)


def register_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        form = SignUpForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Аккаунт создан. Добро пожаловать в Travel X.")
            return redirect("registration_success")
    else:
        form = SignUpForm()

    return render(request, "accounts/register.html", {"form": form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        form = StyledAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            messages.success(request, "Вход выполнен успешно.")
            return redirect(request.POST.get("next") or request.GET.get("next") or "dashboard")
    else:
        form = StyledAuthenticationForm(request)

    return render(request, "accounts/login.html", {"form": form})


@login_required
def dashboard_view(request):
    profile, _ = UserProfile.objects.prefetch_related("achievements").get_or_create(user=request.user)
    ticket_history = (
        Ticket.objects.filter(user=request.user)
        .select_related("package__destination", "flight_schedule__destination")
        .order_by("-created_at")
    )
    unread_notifications = Notification.objects.filter(user=request.user, is_read=False)
    medical_questionnaire = MedicalQuestionnaire.objects.filter(user=request.user).first()
    passenger_document = PassengerDocument.objects.filter(user=request.user).first()

    context = {
        "profile": profile,
        "photo_form": ProfileImageForm(),
        "tickets": ticket_history,
        "ticket_history": ticket_history,
        "unread_notifications": unread_notifications,
        "medical_questionnaire": medical_questionnaire,
        "passenger_document": passenger_document,
        "preparation_progress_percent": get_preparation_progress_percent(request.user),
    }
    return render(request, "accounts/dashboard.html", context)


@login_required
@require_POST
def cancel_ticket(request, ticket_id):
    ticket = get_object_or_404(
        Ticket.objects.select_related("flight_schedule"),
        pk=ticket_id,
        user=request.user,
    )
    ticket.status = Ticket.TicketStatus.CANCELLED
    ticket.cancellation_reason = request.POST.get("cancellation_reason", "").strip()
    ticket.save(update_fields=["status", "cancellation_reason", "updated_at"])

    if ticket.flight_schedule.departure_at - timezone.now() < timedelta(days=7):
        Notification.objects.create(
            user=request.user,
            text="Бронирование отменено менее чем за 7 дней до вылета: возврат средств составит 50%.",
        )

    messages.success(request, "Бронирование отменено.")
    return redirect("dashboard")


@require_POST
def book_tour_api(request):
    """Create a paid ticket from an async one-click booking request."""

    if not request.user.is_authenticated:
        return JsonResponse(
            {
                "status": "error",
                "message": "Авторизуйтесь, чтобы забронировать тур.",
                "login_url": reverse("login"),
            },
            status=401,
        )

    if request.content_type == "application/json":
        try:
            payload = json.loads(request.body.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            return JsonResponse(
                {"status": "error", "message": "Некорректный JSON в запросе."},
                status=400,
            )
    else:
        payload = request.POST

    package_id = (
        payload.get("package_id")
        or payload.get("tariff_id")
        or payload.get("tour_package_id")
    )
    schedule_id = payload.get("schedule_id")

    try:
        ticket = create_paid_ticket_for_booking(request.user, package_id, schedule_id)
    except ValueError as error:
        return JsonResponse({"status": "error", "message": str(error)}, status=400)
    except Http404:
        return JsonResponse(
            {"status": "error", "message": "Выбранный тур или рейс не найден."},
            status=404,
        )

    return JsonResponse(
        {
            "status": "success",
            "message": "Тур успешно забронирован! Билет добавлен в личный кабинет",
            "ticket_id": ticket.id,
            "ticket_number": str(ticket.ticket_number),
            "dashboard_url": reverse("dashboard"),
        }
    )


@login_required
def download_ticket_pdf(request, ticket_id):
    ticket = get_object_or_404(
        Ticket.objects.select_related("user", "package__destination", "flight_schedule"),
        pk=ticket_id,
        user=request.user,
        status=Ticket.TicketStatus.PAID,
    )

    response = HttpResponse(content_type="application/pdf")
    filename = f"travelx-ticket-{ticket.ticket_number}.pdf"
    response["Content-Disposition"] = f'attachment; filename="{filename}"'

    pdf = canvas.Canvas(response, pagesize=A4)
    font_name = get_pdf_font_name()
    passenger_name = ticket.user.get_full_name().strip() or ticket.user.username
    destination_title = ticket.package.destination.title
    departure_at = timezone.localtime(ticket.flight_schedule.departure_at).strftime("%d.%m.%Y %H:%M")

    pdf.setTitle(f"Travel X Ticket {ticket.ticket_number}")
    pdf.setFont(font_name, 18)
    pdf.drawString(24 * mm, 270 * mm, "Travel X")
    pdf.setFont(font_name, 13)
    pdf.drawString(24 * mm, 252 * mm, f"Пассажир: {passenger_name}")
    pdf.drawString(24 * mm, 240 * mm, f"Направление: {destination_title}")
    pdf.drawString(24 * mm, 228 * mm, f"Дата вылета: {departure_at}")
    pdf.drawString(24 * mm, 216 * mm, f"ID билета: {ticket.ticket_number}")

    qr_image = qrcode.make(str(ticket.ticket_number))
    qr_buffer = BytesIO()
    qr_image.save(qr_buffer, format="PNG")
    qr_buffer.seek(0)
    pdf.drawImage(ImageReader(qr_buffer), 24 * mm, 140 * mm, width=52 * mm, height=52 * mm)

    pdf.setFont(font_name, 10)
    pdf.drawString(24 * mm, 130 * mm, "QR-код содержит уникальный ID билета.")
    pdf.showPage()
    pdf.save()

    return response


@login_required
@require_POST
def book_ticket(request):
    package_id = request.POST.get("package_id")
    schedule_id = request.POST.get("schedule_id")
    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    # Первый билет требует серверного психо-теста. Выбор пользователя сохраняется в сессии
    # и будет оформлен сразу после успешной сдачи.
    is_first_purchase = not Ticket.objects.filter(user=request.user).exists()
    if is_first_purchase and not profile.psych_quiz_passed:
        request.session["pending_booking"] = {
            "package_id": package_id,
            "schedule_id": schedule_id,
        }
        messages.info(request, "Перед первой покупкой пройдите психологический тест космотуриста.")
        return redirect("psych_quiz")

    try:
        create_paid_ticket_for_booking(request.user, package_id, schedule_id)
    except ValueError as error:
        messages.error(request, str(error))
        return redirect("destinations")

    messages.success(request, "Билет успешно оформлен. Посадочный талон уже доступен в личном кабинете.")
    return redirect("dashboard")


@login_required
def psych_quiz_view(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    required_score = 5
    context = {"quiz_questions": QUIZ_QUESTIONS, "required_score": required_score}

    if request.method == "POST":
        try:
            score = calculate_quiz_score(request.POST)
        except ValueError as error:
            messages.error(request, str(error))
            return render(request, "accounts/psych_quiz.html", context)

        if score < required_score:
            messages.error(
                request,
                f"Тест не пройден: нужно набрать минимум {required_score} из {len(QUIZ_QUESTIONS)} баллов.",
            )
            return render(request, "accounts/psych_quiz.html", context)

        profile.psych_quiz_passed = True
        profile.save(update_fields=["psych_quiz_passed", "updated_at"])

        pending_booking = request.session.get("pending_booking")
        if pending_booking:
            try:
                create_paid_ticket_for_booking(
                    request.user,
                    pending_booking.get("package_id"),
                    pending_booking.get("schedule_id"),
                )
            except ValueError as error:
                messages.error(request, str(error))
                return redirect("destinations")

            del request.session["pending_booking"]
            messages.success(
                request,
                "Тест пройден. Билет успешно оформлен и доступен в личном кабинете.",
            )
            return redirect("dashboard")

        messages.success(request, "Тест пройден. Теперь можно оформлять первый билет.")
        return redirect("destinations")

    return render(request, "accounts/psych_quiz.html", context)


@login_required
@require_POST
def add_review(request, destination_id):
    destination = get_object_or_404(Destination, pk=destination_id)
    has_flown = Ticket.objects.filter(
        user=request.user,
        flight_schedule__destination=destination,
    ).exists()

    if not has_flown:
        messages.error(request, "Отзыв можно оставить только после покупки билета на это направление.")
        return redirect("destinations")

    text = request.POST.get("text", "").strip()
    rating = request.POST.get("rating")

    if not text:
        messages.error(request, "Напишите текст отзыва.")
        return redirect("destinations")

    try:
        rating = int(rating)
    except (TypeError, ValueError):
        messages.error(request, "Выберите рейтинг от 1 до 5.")
        return redirect("destinations")

    if rating < 1 or rating > 5:
        messages.error(request, "Рейтинг должен быть от 1 до 5.")
        return redirect("destinations")

    Review.objects.create(
        user=request.user,
        destination=destination,
        text=text,
        rating=rating,
    )
    messages.success(request, "Отзыв опубликован. Спасибо за впечатления.")
    return redirect("destinations")


@login_required
@require_POST
def update_profile_photo(request):
    profile = get_object_or_404(UserProfile, user=request.user)
    form = ProfileImageForm(request.POST, request.FILES)

    if form.is_valid():
        new_image = form.cleaned_data["profile_image"]
        old_image = profile.profile_image

        if old_image and old_image.name != new_image.name:
            old_image.delete(save=False)

        profile.profile_image = new_image
        profile.save(update_fields=["profile_image", "updated_at"])
        messages.success(request, "Фото профиля обновлено.")
    else:
        messages.error(request, "Загрузите изображение в формате JPG, PNG, WEBP или GIF.")

    return HttpResponseRedirect(reverse("dashboard"))


@require_POST
def logout_view(request):
    logout(request)
    messages.info(request, "Вы вышли из аккаунта.")
    return redirect("home")
