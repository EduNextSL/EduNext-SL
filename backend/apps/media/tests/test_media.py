from unittest import mock

import cloudinary.utils
from django.test import override_settings
from django.urls import reverse

from apps.accounts.tests.helpers import ApiTestCase, make_user
from apps.media.storage import CloudinaryStorage

CLOUD = {
    "CLOUDINARY_ENABLED": True,
    "CLOUDINARY_NAME": "demo-cloud",
    "CLOUDINARY_API_KEY": "key123",
    "CLOUDINARY_API_SECRET": "secret456",
}


class UploadSignatureTests(ApiTestCase):
    url = "/api/v1/media/signature/"

    def request(self, resource_type="image", **extra):
        return self.client.post(self.url, {"resource_type": resource_type, **extra}, format="json")

    def test_requires_authentication(self):
        self.assertEqual(self.request().status_code, 401)

    def test_not_configured_returns_501(self):
        self.auth_as(make_user())
        response = self.request()
        self.assertEqual(response.status_code, 501)
        self.assertEqual(response.json()["code"], "NOT_IMPLEMENTED")

    @override_settings(**CLOUD)
    def test_signature_is_valid_and_scoped_to_the_user(self):
        user = make_user()
        self.auth_as(user)
        response = self.request("video")
        self.assertEqual(response.status_code, 200)
        data = response.json()["data"]

        self.assertEqual(
            data["upload_url"], "https://api.cloudinary.com/v1_1/demo-cloud/video/upload"
        )
        self.assertEqual(data["api_key"], "key123")
        self.assertEqual(data["form_fields"]["folder"], f"edunext/users/{user.pk}/video")
        self.assertIn("mp4", data["form_fields"]["allowed_formats"])
        expected = cloudinary.utils.api_sign_request(data["form_fields"], "secret456")
        self.assertEqual(data["signature"], expected)
        self.assertNotIn("secret456", response.content.decode())

    @override_settings(**CLOUD)
    def test_client_cannot_choose_folder_or_formats(self):
        user = make_user()
        self.auth_as(user)
        data = self.request(
            "image", folder="edunext/users/someone-else", allowed_formats="exe"
        ).json()["data"]
        self.assertEqual(data["form_fields"]["folder"], f"edunext/users/{user.pk}/image")
        self.assertNotIn("exe", data["form_fields"]["allowed_formats"])

    @override_settings(**CLOUD)
    def test_unknown_resource_type_rejected(self):
        self.auth_as(make_user())
        self.assertEqual(self.request("auto").status_code, 400)
        self.assertEqual(self.client.post(self.url, {}, format="json").status_code, 400)

    @override_settings(**CLOUD)
    def test_each_user_gets_their_own_folder(self):
        alice, bob = make_user("alice@example.com"), make_user("bob@example.com")
        self.auth_as(alice)
        a = self.request().json()["data"]["form_fields"]["folder"]
        self.client.credentials()
        self.auth_as(bob)
        b = self.request().json()["data"]["form_fields"]["folder"]
        self.assertNotEqual(a, b)


class CloudinaryStorageTests(ApiTestCase):
    def test_save_returns_typed_name_and_uploads_to_folder(self):
        storage = CloudinaryStorage(folder="edunext/media")
        fake = mock.Mock(size=1024)
        with mock.patch(
            "apps.media.storage.cloudinary.uploader.upload",
            return_value={"resource_type": "image", "public_id": "edunext/media/abc"},
        ) as upload:
            name = storage._save("photo.png", fake)
        self.assertEqual(name, "image/edunext/media/abc")
        self.assertEqual(upload.call_args.kwargs["folder"], "edunext/media")
        self.assertEqual(upload.call_args.kwargs["resource_type"], "auto")

    def test_large_files_use_chunked_upload(self):
        storage = CloudinaryStorage()
        big = mock.Mock(size=50 * 1024 * 1024)
        with mock.patch(
            "apps.media.storage.cloudinary.uploader.upload_large",
            return_value={"resource_type": "video", "public_id": "edunext/media/vid"},
        ) as upload_large:
            self.assertEqual(storage._save("clip.mp4", big), "video/edunext/media/vid")
        upload_large.assert_called_once()

    def test_delete_uses_the_stored_resource_type(self):
        with mock.patch("apps.media.storage.cloudinary.uploader.destroy") as destroy:
            CloudinaryStorage().delete("video/edunext/media/vid")
        destroy.assert_called_once_with("edunext/media/vid", resource_type="video")

    def test_url_is_https(self):
        with mock.patch(
            "apps.media.storage.cloudinary.utils.cloudinary_url",
            return_value=("https://res.cloudinary.com/x/image/upload/a", {}),
        ) as build:
            url = CloudinaryStorage().url("image/a")
        self.assertTrue(url.startswith("https://"))
        self.assertEqual(build.call_args.kwargs["resource_type"], "image")


class HealthTests(ApiTestCase):
    def test_health_reports_database_ok(self):
        response = self.client.get(reverse("health"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})
