from django.apps import AppConfig
from django.conf import settings


class MediaConfig(AppConfig):
    name = "apps.media"
    label = "media"

    def ready(self):
        if settings.CLOUDINARY_ENABLED:
            import cloudinary

            cloudinary.config(
                cloud_name=settings.CLOUDINARY_NAME,
                api_key=settings.CLOUDINARY_API_KEY,
                api_secret=settings.CLOUDINARY_API_SECRET,
                secure=True,
            )
