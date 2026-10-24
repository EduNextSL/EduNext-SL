from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("register/student/", views.StudentRegisterView.as_view(), name="register-student"),
    path("register/company/", views.CompanyRegisterView.as_view(), name="register-company"),
    path("login/", views.LoginView.as_view(), name="login"),
    path("refresh/", views.RefreshView.as_view(), name="refresh"),
    path("logout/", views.LogoutView.as_view(), name="logout"),
    path("me/", views.MeView.as_view(), name="me"),
    path(
        "password-reset/request/",
        views.PasswordResetRequestView.as_view(),
        name="password-reset-request",
    ),
    path(
        "password-reset/confirm/",
        views.PasswordResetConfirmView.as_view(),
        name="password-reset-confirm",
    ),
    path("providers/", views.ProvidersView.as_view(), name="providers"),
    path("social/<str:provider>/", views.SocialLoginView.as_view(), name="social-login"),
]
