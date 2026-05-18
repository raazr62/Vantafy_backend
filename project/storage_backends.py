from __future__ import annotations

from django.conf import settings
from django.core.files.storage import FileSystemStorage

try:
    from storages.backends.s3boto3 import S3Boto3Storage
except Exception as exc:  # pragma: no cover
    raise ImportError(
        "django-storages must be installed to use S3 storage backends"
    ) from exc


# Media Storage
class HybridMediaStorage(S3Boto3Storage):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._local_storage = FileSystemStorage(
            location=settings.MEDIA_ROOT,
            base_url=settings.MEDIA_URL,
        )

    def _exists_in_s3(self, name: str) -> bool:
        try:
            return super().exists(name)
        except Exception:
            return False

    def exists(self, name: str) -> bool:
        return self._exists_in_s3(name) or self._local_storage.exists(name)

    def open(self, name: str, mode: str = "rb"):
        if self._exists_in_s3(name):
            return super().open(name, mode)
        return self._local_storage.open(name, mode)

    def url(self, name: str, parameters=None, expire=None, http_method=None):
        if self._exists_in_s3(name):
            return super().url(
                name,
                parameters=parameters,
                expire=expire,
                http_method=http_method,
            )
        return self._local_storage.url(name)
