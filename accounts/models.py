from io import BytesIO
from pathlib import Path
from uuid import uuid4

import qrcode
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.core.validators import (
    FileExtensionValidator,
    MaxValueValidator,
    MinValueValidator,
)
from django.db import models


def profile_image_upload_to(instance, filename):
    extension = Path(filename).suffix.lower() or ".png"
    return f"profile_photos/user_{instance.user_id}/{uuid4().hex}{extension}"


def ticket_qr_upload_to(instance, filename):
    extension = Path(filename).suffix.lower() or ".png"
    return f"ticket_qr/user_{instance.user_id}/{instance.ticket_number}{extension}"


class Achievement(models.Model):
    """Бейдж-достижение, которое может быть выдано пользователю."""

    title = models.CharField(max_length=120, unique=True, verbose_name="Название")
    description = models.TextField(verbose_name="Описание")
    icon = models.ImageField(
        upload_to="achievements/",
        blank=True,
        null=True,
        verbose_name="Иконка",
    )

    class Meta:
        ordering = ("title",)
        verbose_name = "Достижение"
        verbose_name_plural = "Достижения"

    def __str__(self):
        return self.title


class UserProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile",
        verbose_name="Пользователь",
    )
    age = models.PositiveSmallIntegerField(
        default=18,
        validators=[MinValueValidator(18), MaxValueValidator(100)],
        verbose_name="Возраст",
    )
    profile_image = models.ImageField(
        upload_to=profile_image_upload_to,
        blank=True,
        null=True,
        validators=[FileExtensionValidator(["jpg", "jpeg", "png", "webp", "gif"])],
        verbose_name="Фото профиля",
    )
    achievements = models.ManyToManyField(
        Achievement,
        related_name="profiles",
        blank=True,
        verbose_name="Достижения",
    )
    psych_quiz_passed = models.BooleanField(
        default=False,
        verbose_name="Психологический тест пройден",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создан")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлен")

    class Meta:
        verbose_name = "Профиль пользователя"
        verbose_name_plural = "Профили пользователей"

    def __str__(self):
        return f"Профиль {self.user.username}"


class StarSystem(models.Model):
    """Звездная система или регион для группировки направлений."""

    name = models.CharField(max_length=120, unique=True, verbose_name="Название")

    class Meta:
        ordering = ("name",)
        verbose_name = "Звездная система"
        verbose_name_plural = "Звездные системы"

    def __str__(self):
        return self.name


class ActivityTag(models.Model):
    """Тип активности, доступный в космическом туре."""

    name = models.CharField(max_length=80, unique=True, verbose_name="Название")

    class Meta:
        ordering = ("name",)
        verbose_name = "Тип активности"
        verbose_name_plural = "Типы активности"

    def __str__(self):
        return self.name


class Destination(models.Model):
    """Космическое направление: планета, спутник, станция или астероид."""

    class ObjectType(models.TextChoices):
        PLANET = "planet", "Планета"
        SATELLITE = "satellite", "Спутник"
        ORBITAL_STATION = "orbital_station", "Орбитальная станция"
        ASTEROID = "asteroid", "Астероид"

    title = models.CharField(max_length=160, verbose_name="Название")
    description = models.TextField(verbose_name="Описание")
    image = models.ImageField(upload_to="destinations/", verbose_name="Фото")
    object_type = models.CharField(
        max_length=32,
        choices=ObjectType.choices,
        verbose_name="Тип объекта",
    )
    system = models.ForeignKey(
        StarSystem,
        on_delete=models.PROTECT,
        related_name="destinations",
        verbose_name="Звездная система",
    )
    tags = models.ManyToManyField(
        ActivityTag,
        related_name="destinations",
        blank=True,
        verbose_name="Типы активности",
    )

    class Meta:
        ordering = ("title",)
        verbose_name = "Направление"
        verbose_name_plural = "Направления"

    def __str__(self):
        return self.title


class TourPackage(models.Model):
    """Тариф обслуживания для конкретного направления."""

    class ClassType(models.TextChoices):
        ECONOMY = "economy", "Economy"
        EXPLORER = "explorer", "Explorer"
        FIRST_CLASS = "first_class", "First Class"

    destination = models.ForeignKey(
        Destination,
        on_delete=models.CASCADE,
        related_name="packages",
        verbose_name="Направление",
    )
    class_type = models.CharField(
        max_length=24,
        choices=ClassType.choices,
        verbose_name="Класс обслуживания",
    )
    price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Цена",
    )
    features = models.TextField(verbose_name="Преимущества тарифа")

    class Meta:
        ordering = ("price",)
        verbose_name = "Пакет обслуживания"
        verbose_name_plural = "Пакеты обслуживания"

    def __str__(self):
        return f"{self.destination} - {self.get_class_type_display()}"


class FlightSchedule(models.Model):
    """Расписание рейса к конкретному направлению."""

    destination = models.ForeignKey(
        Destination,
        on_delete=models.CASCADE,
        related_name="flight_schedules",
        verbose_name="Направление",
    )
    departure_at = models.DateTimeField(verbose_name="Дата и время вылета")
    available_seats = models.PositiveIntegerField(default=0, verbose_name="Доступно мест")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлено")

    class Meta:
        ordering = ("departure_at",)
        verbose_name = "Расписание рейса"
        verbose_name_plural = "Расписание рейсов"

    def __str__(self):
        return f"{self.destination} - {self.departure_at:%d.%m.%Y %H:%M}"


class Ticket(models.Model):
    """Посадочный билет пользователя с QR-кодом."""

    class TicketStatus(models.TextChoices):
        PENDING = "pending", "Ожидает оплаты"
        PAID = "paid", "Оплачен"
        CANCELLED = "cancelled", "Отменен"

    # Совместимость для старого кода, который обращался к Ticket.PaymentStatus.
    PaymentStatus = TicketStatus

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="tickets",
        verbose_name="Пользователь",
    )
    package = models.ForeignKey(
        TourPackage,
        on_delete=models.PROTECT,
        related_name="tickets",
        verbose_name="Тариф",
    )
    flight_schedule = models.ForeignKey(
        FlightSchedule,
        on_delete=models.PROTECT,
        related_name="tickets",
        verbose_name="Расписание рейса",
    )
    ticket_number = models.UUIDField(
        default=uuid4,
        unique=True,
        editable=False,
        verbose_name="Номер билета",
    )
    qr_code = models.ImageField(
        upload_to=ticket_qr_upload_to,
        blank=True,
        null=True,
        verbose_name="QR-код",
    )
    status = models.CharField(
        max_length=16,
        choices=TicketStatus.choices,
        default=TicketStatus.PENDING,
        verbose_name="Статус билета",
    )
    cancellation_reason = models.TextField(
        blank=True,
        verbose_name="Причина отмены",
        help_text="Заполняется, если билет был отменен.",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создан")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлен")

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "Билет"
        verbose_name_plural = "Билеты"

    def save(self, *args, **kwargs):
        if not self.qr_code:
            qr_image = qrcode.make(str(self.ticket_number))
            buffer = BytesIO()
            qr_image.save(buffer, format="PNG")
            self.qr_code.save(
                f"{self.ticket_number}.png",
                ContentFile(buffer.getvalue()),
                save=False,
            )

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Билет {self.ticket_number} - {self.user.username}"


class PassengerDocument(models.Model):
    """Паспортные данные пассажира для подготовки к космическому перелету."""

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="passenger_document",
        verbose_name="Пользователь",
    )
    passport_number = models.CharField(
        max_length=32,
        verbose_name="Номер паспорта",
    )
    citizenship = models.CharField(
        max_length=120,
        verbose_name="Гражданство",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлено")

    class Meta:
        ordering = ("user__username",)
        verbose_name = "Паспортные данные пассажира"
        verbose_name_plural = "Паспортные данные пассажиров"

    def __str__(self):
        return f"Документы {self.user.username}: {self.passport_number}"


class MedicalQuestionnaire(models.Model):
    """Медицинская анкета пользователя для допуска к полету."""

    class ClearanceStatus(models.TextChoices):
        PENDING = "pending", "Ожидает проверки"
        APPROVED = "approved", "Допущен"
        REJECTED = "rejected", "Отклонен"

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="medical_questionnaire",
        verbose_name="Пользователь",
    )
    height_cm = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(300)],
        verbose_name="Рост, см",
    )
    weight_kg = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(500)],
        verbose_name="Вес, кг",
    )
    has_chronic_diseases = models.BooleanField(
        default=False,
        verbose_name="Есть хронические заболевания",
    )
    clearance_status = models.CharField(
        max_length=16,
        choices=ClearanceStatus.choices,
        default=ClearanceStatus.PENDING,
        verbose_name="Статус допуска",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создана")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлена")

    class Meta:
        ordering = ("user__username",)
        verbose_name = "Медицинская анкета"
        verbose_name_plural = "Медицинские анкеты"

    def __str__(self):
        return f"Меданкета {self.user.username}: {self.get_clearance_status_display()}"


class PreparationTask(models.Model):
    """Задача подготовки пассажира, привязанная к конкретному билету."""

    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.CASCADE,
        related_name="preparation_tasks",
        verbose_name="Билет",
    )
    title = models.CharField(
        max_length=160,
        verbose_name="Название задачи",
    )
    is_completed = models.BooleanField(
        default=False,
        verbose_name="Выполнено",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создана")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлена")

    class Meta:
        ordering = ("ticket", "title")
        verbose_name = "Задача подготовки"
        verbose_name_plural = "Задачи подготовки"

    def __str__(self):
        status = "выполнено" if self.is_completed else "не выполнено"
        return f"{self.title} - {status}"


class Notification(models.Model):
    """Уведомление пользователя в личном кабинете."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="notifications",
        verbose_name="Пользователь",
    )
    text = models.TextField(verbose_name="Текст уведомления")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    is_read = models.BooleanField(default=False, verbose_name="Прочитано")

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "Уведомление"
        verbose_name_plural = "Уведомления"

    def __str__(self):
        return f"Уведомление для {self.user.username}: {self.text[:50]}"


class Review(models.Model):
    """Отзыв пользователя о направлении, доступный после покупки билета."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="reviews",
        verbose_name="Пользователь",
    )
    destination = models.ForeignKey(
        Destination,
        on_delete=models.CASCADE,
        related_name="reviews",
        verbose_name="Направление",
    )
    text = models.TextField(verbose_name="Текст отзыва")
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="Рейтинг",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "Отзыв"
        verbose_name_plural = "Отзывы"

    def __str__(self):
        return f"{self.destination} - {self.rating}/5 от {self.user.username}"


class SpaceTour(models.Model):
    """Учебная модель космического тура для демонстрации работы с БД."""

    title = models.CharField(max_length=160, verbose_name="Название")
    planet = models.CharField(max_length=120, verbose_name="Планета назначения")
    price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Цена",
    )
    description = models.TextField(verbose_name="Описание")
    is_active = models.BooleanField(default=True, verbose_name="Доступен")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создан")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлен")

    class Meta:
        ordering = ("title",)
        verbose_name = "Космический тур"
        verbose_name_plural = "Космические туры"

    def __str__(self):
        return f"{self.title} — {self.planet}"
