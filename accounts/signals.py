from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Achievement, Ticket, UserProfile


ACHIEVEMENT_RULES = {
    "first_flight": {
        "title": "Первый старт",
        "description": "Первый оформленный билет Travel X.",
        "icon": "achievements/first-start.png",
    },
    "mars": {
        "title": "Покоритель Марса",
        "description": "Билет на марсианское направление забронирован.",
        "icon": "achievements/mars-conqueror.png",
    },
    "vip": {
        "title": "VIP-путешественник",
        "description": "Больше пяти оплаченных билетов в истории профиля.",
        "icon": "achievements/vip-traveller.png",
    },
}


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


def grant_achievement(profile, rule_key):
    rule = ACHIEVEMENT_RULES[rule_key]
    achievement, _ = Achievement.objects.get_or_create(
        title=rule["title"],
        defaults={
            "description": rule["description"],
            "icon": rule["icon"],
        },
    )
    profile.achievements.add(achievement)


@receiver(post_save, sender=Ticket)
def award_ticket_achievements(sender, instance, **kwargs):
    if instance.status != Ticket.TicketStatus.PAID:
        return

    profile, _ = UserProfile.objects.get_or_create(user=instance.user)
    paid_tickets = Ticket.objects.filter(
        user=instance.user,
        status=Ticket.TicketStatus.PAID,
    )

    grant_achievement(profile, "first_flight")

    destination_title = instance.flight_schedule.destination.title.lower()
    if "марс" in destination_title or "mars" in destination_title:
        grant_achievement(profile, "mars")

    if paid_tickets.count() > 5:
        grant_achievement(profile, "vip")
