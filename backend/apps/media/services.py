"""Signed direct-upload parameters.

Browsers upload straight to Cloudinary (keeping large videos off the web dynos) using a
short-lived signature minted here. The signature covers the folder and allowed formats,
so a client cannot upload outside its own folder or with other file types.
"""

import time
from dataclasses import dataclass

import cloudinary.utils
from django.conf import settings

MB = 1024 * 1024


@dataclass(frozen=True)
class UploadPolicy:
    allowed_formats: tuple[str, ...]
    max_bytes: int


UPLOAD_POLICIES: dict[str, UploadPolicy] = {
    "image": UploadPolicy(("jpg", "jpeg", "png", "webp", "gif"), 10 * MB),
    "video": UploadPolicy(("mp4", "mov", "webm", "mkv"), 200 * MB),
    "raw": UploadPolicy(
        ("pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx", "txt", "csv", "zip"), 25 * MB
    ),
}


class MediaNotConfigured(Exception):
    pass


def build_upload_signature(user, resource_type: str) -> dict:
    if not settings.CLOUDINARY_ENABLED:
        raise MediaNotConfigured
    policy = UPLOAD_POLICIES[resource_type]
    params = {
        "allowed_formats": ",".join(policy.allowed_formats),
        "folder": f"edunext/users/{user.pk}/{resource_type}",
        "timestamp": int(time.time()),
    }
    signature = cloudinary.utils.api_sign_request(params, settings.CLOUDINARY_API_SECRET)
    return {
        "upload_url": (
            f"https://api.cloudinary.com/v1_1/{settings.CLOUDINARY_NAME}/{resource_type}/upload"
        ),
        "api_key": settings.CLOUDINARY_API_KEY,
        "signature": signature,
        "form_fields": params,  # send exactly these, unchanged, as form fields
        "max_bytes": policy.max_bytes,  # enforce in the client before uploading
    }
