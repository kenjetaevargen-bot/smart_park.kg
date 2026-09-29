from django.urls import path

from parking import views

urlpatterns = [
    path("", views.index, name="index"),
    path("api/bootstrap/", views.bootstrap, name="bootstrap"),
    path("api/login/", views.login, name="login"),
    path("api/logout/", views.logout, name="logout"),
    path("api/register/", views.register, name="register"),
    path("api/account/", views.update_account, name="update_account"),
    path("api/profile/", views.profile, name="profile"),
    path("api/reservations/", views.reservations, name="reservations"),
    path("api/reservations/create/", views.create_reservation, name="create_reservation"),
    path("api/reservations/<int:reservation_id>/cancel/", views.cancel_reservation, name="cancel_reservation"),
]