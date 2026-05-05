from django.contrib import admin

from .models import (
    Achievement,
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


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "age", "has_custom_photo", "created_at")
    list_filter = ("created_at", "updated_at")
    search_fields = ("user__username", "user__email")
    readonly_fields = ("created_at", "updated_at")
    filter_horizontal = ("achievements",)

    @admin.display(boolean=True, description="Есть фото")
    def has_custom_photo(self, obj):
        return bool(obj.profile_image)


@admin.register(StarSystem)
class StarSystemAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(ActivityTag)
class ActivityTagAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ("title",)
    search_fields = ("title", "description")


class TourPackageInline(admin.TabularInline):
    model = TourPackage
    extra = 1
    fields = ("class_type", "price", "features")


@admin.register(Destination)
class DestinationAdmin(admin.ModelAdmin):
    list_display = ("title", "object_type", "system", "packages_count")
    list_filter = ("system", "object_type", "tags")
    search_fields = ("title", "description", "system__name", "tags__name")
    filter_horizontal = ("tags",)
    inlines = (TourPackageInline,)

    @admin.display(description="Тарифов")
    def packages_count(self, obj):
        return obj.packages.count()


@admin.register(TourPackage)
class TourPackageAdmin(admin.ModelAdmin):
    list_display = ("destination", "class_type", "price")
    list_filter = ("class_type", "destination__system", "destination__object_type")
    search_fields = ("destination__title", "features")


@admin.register(FlightSchedule)
class FlightScheduleAdmin(admin.ModelAdmin):
    list_display = ("destination", "departure_at", "available_seats")
    list_filter = ("destination__system", "destination__object_type", "departure_at")
    search_fields = ("destination__title",)
    date_hierarchy = "departure_at"


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ("ticket_number", "user", "package", "flight_schedule", "status", "created_at")
    list_filter = ("status", "package__class_type", "flight_schedule__departure_at")
    search_fields = ("ticket_number", "user__username", "user__email", "package__destination__title", "cancellation_reason")
    readonly_fields = ("ticket_number", "qr_code", "created_at", "updated_at")


@admin.register(PassengerDocument)
class PassengerDocumentAdmin(admin.ModelAdmin):
    list_display = ("user", "passport_number", "citizenship", "updated_at")
    search_fields = ("user__username", "user__email", "passport_number", "citizenship")
    readonly_fields = ("created_at", "updated_at")


@admin.register(MedicalQuestionnaire)
class MedicalQuestionnaireAdmin(admin.ModelAdmin):
    list_display = ("user", "height_cm", "weight_kg", "has_chronic_diseases", "clearance_status", "updated_at")
    list_filter = ("clearance_status", "has_chronic_diseases")
    search_fields = ("user__username", "user__email")
    readonly_fields = ("created_at", "updated_at")


@admin.register(PreparationTask)
class PreparationTaskAdmin(admin.ModelAdmin):
    list_display = ("title", "ticket", "user", "is_completed", "updated_at")
    list_filter = ("is_completed", "ticket__status")
    search_fields = ("title", "ticket__ticket_number", "ticket__user__username", "ticket__user__email")
    readonly_fields = ("created_at", "updated_at")

    @admin.display(description="Пользователь")
    def user(self, obj):
        return obj.ticket.user


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("user", "short_text", "is_read", "created_at")
    list_filter = ("is_read", "created_at")
    search_fields = ("user__username", "user__email", "text")
    readonly_fields = ("created_at",)

    @admin.display(description="Текст")
    def short_text(self, obj):
        return obj.text[:80]


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("destination", "user", "rating", "created_at")
    list_filter = ("rating", "created_at", "destination__system")
    search_fields = ("destination__title", "user__username", "user__email", "text")
    readonly_fields = ("created_at",)


@admin.register(SpaceTour)
class SpaceTourAdmin(admin.ModelAdmin):
    list_display = ("title", "planet", "price", "is_active")
    list_filter = ("is_active", "planet")
    search_fields = ("title", "planet", "description")
