from PIL import Image
from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from .models import UserProfile

ALLOWED_CONTENT_TYPES = {
    "image/gif",
    "image/jpeg",
    "image/png",
    "image/webp",
}


def validate_uploaded_image(uploaded_file):
    if not uploaded_file:
        return uploaded_file

    content_type = getattr(uploaded_file, "content_type", "")
    if content_type and content_type not in ALLOWED_CONTENT_TYPES:
        raise ValidationError("Допустимы только изображения JPG, PNG, WEBP или GIF.")

    try:
        image = Image.open(uploaded_file)
        image.verify()
        uploaded_file.seek(0)
    except Exception as exc:
        raise ValidationError("Загрузите корректный файл изображения.") from exc

    return uploaded_file


class SignUpForm(UserCreationForm):
    email = forms.EmailField(
        label="Электронная почта",
        widget=forms.EmailInput(
            attrs={
                "class": "form-input",
                "placeholder": "traveler@example.com",
            }
        ),
    )
    age = forms.IntegerField(
        label="Возраст",
        min_value=18,
        max_value=100,
        widget=forms.NumberInput(
            attrs={
                "class": "form-input",
                "placeholder": "18+",
            }
        ),
    )
    profile_image = forms.ImageField(
        label="Фото профиля",
        required=False,
        widget=forms.ClearableFileInput(
            attrs={
                "class": "form-input file-input",
                "accept": "image/jpeg,image/png,image/webp,image/gif",
                "data-preview-input": "register",
            }
        ),
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email", "age", "profile_image", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = "Имя пользователя"
        self.fields["username"].widget.attrs.update(
            {
                "class": "form-input",
                "placeholder": "space_cadet",
            }
        )
        self.fields["password1"].label = "Пароль"
        self.fields["password1"].widget.attrs.update(
            {
                "class": "form-input",
                "placeholder": "Придумайте пароль",
            }
        )
        self.fields["password2"].label = "Подтверждение пароля"
        self.fields["password2"].widget.attrs.update(
            {
                "class": "form-input",
                "placeholder": "Повторите пароль",
            }
        )
        self.fields["password1"].help_text = "Используйте надежный пароль длиной не менее 8 символов."
        self.fields["password2"].help_text = "Повторите пароль, чтобы завершить регистрацию."

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("Пользователь с такой почтой уже существует.")
        return email

    def clean_profile_image(self):
        return validate_uploaded_image(self.cleaned_data.get("profile_image"))

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]

        if commit:
            user.save()
            profile = user.profile
            profile.age = self.cleaned_data["age"]

            image = self.cleaned_data.get("profile_image")
            if image:
                profile.profile_image = image

            profile.save()

        return user


class StyledAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        label="Имя пользователя",
        widget=forms.TextInput(
            attrs={
                "class": "form-input",
                "placeholder": "Введите имя пользователя",
                "autocomplete": "username",
            }
        ),
    )
    password = forms.CharField(
        label="Пароль",
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "class": "form-input",
                "placeholder": "Введите пароль",
                "autocomplete": "current-password",
            }
        ),
    )


class ProfileImageForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ("profile_image",)
        widgets = {
            "profile_image": forms.ClearableFileInput(
                attrs={
                    "class": "form-input file-input",
                    "accept": "image/jpeg,image/png,image/webp,image/gif",
                    "data-preview-input": "dashboard",
                }
            )
        }
        labels = {
            "profile_image": "Новое фото профиля",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["profile_image"].required = True
        self.fields["profile_image"].help_text = "Поддерживаются только файлы JPG, PNG, WEBP и GIF."

    def clean_profile_image(self):
        return validate_uploaded_image(self.cleaned_data.get("profile_image"))
