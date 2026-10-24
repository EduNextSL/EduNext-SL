from django.urls import path

from . import views

app_name = "media"

urlpatterns = [
    path("signature/", views.UploadSignatureView.as_view(), name="signature"),
]
