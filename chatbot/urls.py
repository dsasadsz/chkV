from django.urls import path

from chatbot import views

app_name = "chatbot"

urlpatterns = [
    path("", views.chat_page, name="chat_page"),
    path("message/", views.chat_message, name="chat_message"),
    path("transcribe/", views.transcribe_audio, name="transcribe_audio"),
]
