from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("destinations/", views.destinations_view, name="destinations"),
    path("tour/<int:tour_id>/", views.tour_detail_view, name="tour_detail"),
    path("register/", views.register_view, name="register"),
    path("success/", views.registration_success_view, name="registration_success"),
    path("login/", views.login_view, name="login"),
    path("staff-home/", views.staff_home, name="staff_home"),
    path("dashboard/", views.dashboard_view, name="dashboard"),
    path("psych-quiz/", views.psych_quiz_view, name="psych_quiz"),
    path("api/book/", views.book_tour_api, name="book_tour_api"),
    path("tickets/book/", views.book_ticket, name="book_ticket"),
    path("tickets/<int:ticket_id>/cancel/", views.cancel_ticket, name="cancel_ticket"),
    path("tickets/<int:ticket_id>/download-pdf/", views.download_ticket_pdf, name="download_ticket_pdf"),
    path("destinations/<int:destination_id>/reviews/add/", views.add_review, name="add_review"),
    path("dashboard/photo/", views.update_profile_photo, name="update_profile_photo"),
    path("logout/", views.logout_view, name="logout"),
]
