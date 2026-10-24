"""Django file storage backed by Cloudinary (images, video and any other file type).

Use it as `default_storage` (configured automatically when Cloudinary credentials are
present) so `FileField`/`ImageField` work unchanged. Stored names look like
"<resource_type>/<public_id>", e.g. "image/edunext/media/ab12cd".
"""

import cloudinary.api
import cloudinary.uploader
import cloudinary.utils
from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible

CHUNKED_UPLOAD_THRESHOLD = 20 * 1024 * 1024  # bytes


@deconstructible
class CloudinaryStorage(Storage):
    def __init__(self, folder: str = "edunext/media"):
        self.folder = folder

    @staticmethod
    def _split(name: str) -> tuple[str, str]:
        resource_type, _, public_id = name.partition("/")
        return resource_type, public_id

    def _save(self, name, content):
        upload = (
            cloudinary.uploader.upload_large
            if getattr(content, "size", 0) > CHUNKED_UPLOAD_THRESHOLD
            else cloudinary.uploader.upload
        )
        result = upload(content, folder=self.folder, resource_type="auto", use_filename=False)
        return f"{result['resource_type']}/{result['public_id']}"

    def url(self, name):
        resource_type, public_id = self._split(name)
        return cloudinary.utils.cloudinary_url(public_id, resource_type=resource_type, secure=True)[
            0
        ]

    def delete(self, name):
        resource_type, public_id = self._split(name)
        cloudinary.uploader.destroy(public_id, resource_type=resource_type)

    def exists(self, name):
        return False  # Cloudinary always assigns a new unique public_id

    def size(self, name):
        resource_type, public_id = self._split(name)
        return cloudinary.api.resource(public_id, resource_type=resource_type)["bytes"]

    def _open(self, name, mode="rb"):
        raise NotImplementedError("Cloudinary files are read through their URL.")
