from django.templatetags.static import static

from .models import UserProfile


def nav_profile(request):
    if not request.user.is_authenticated:
        return {"nav_profile": None}

    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    avatar_url = profile.profile_image.url if profile.profile_image else static("images/default-avatar.svg")

    return {
        "nav_profile": {
            "username": request.user.username,
            "avatar_url": avatar_url,
            "is_staff": request.user.is_staff,
        }
    }
