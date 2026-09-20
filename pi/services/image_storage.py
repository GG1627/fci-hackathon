import re
from pathlib import Path

from supabase import Client, create_client


BUCKET_NAME = "fridge-images"
MAX_REMOTE_IMAGES = 3
IMAGE_NAME_PATTERN = re.compile(r"^fridge-\d{8}T\d{6}Z\.jpg$")


class ImageStorageService:
    def __init__(
        self,
        supabase_url: str,
        secret_key: str,
        client: Client | None = None,
    ) -> None:
        self.client: Client = client or create_client(supabase_url, secret_key)
        self._bucket_ready = False

    def ensure_public_bucket(self) -> None:
        if self._bucket_ready:
            return

        buckets = self.client.storage.list_buckets()
        bucket = next(
            (item for item in buckets if getattr(item, "id", None) == BUCKET_NAME),
            None,
        )

        if bucket is None:
            print(f"Creating public Supabase bucket: {BUCKET_NAME}", flush=True)
            self.client.storage.create_bucket(
                BUCKET_NAME,
                options={
                    "public": True,
                    "allowed_mime_types": ["image/jpeg"],
                },
            )
        elif not getattr(bucket, "public", False):
            raise RuntimeError(
                f"Supabase bucket {BUCKET_NAME!r} must be public to provide a public URL."
            )

        self._bucket_ready = True

    def upload_image(self, image_path: Path) -> str:
        self.ensure_public_bucket()
        bucket = self.client.storage.from_(BUCKET_NAME)

        print("Uploading...", flush=True)
        bucket.upload(
            path=image_path.name,
            file=image_path,
            file_options={
                "content-type": "image/jpeg",
                "cache-control": "3600",
                "upsert": "true",
            },
        )

        public_url = bucket.get_public_url(image_path.name)
        print("Upload successful", flush=True)
        print(f"Public URL: {public_url}", flush=True)

        try:
            self.remove_old_images()
        except Exception as error:
            print(f"Could not remove old images: {error}", flush=True)

        return public_url

    def list_image_names(self) -> list[str]:
        bucket = self.client.storage.from_(BUCKET_NAME)
        names: list[str] = []
        offset = 0
        page_size = 100

        while True:
            items = bucket.list(
                path="",
                options={
                    "limit": page_size,
                    "offset": offset,
                    "sortBy": {"column": "name", "order": "asc"},
                },
            )
            names.extend(
                item["name"]
                for item in items
                if IMAGE_NAME_PATTERN.fullmatch(item.get("name", ""))
            )
            if len(items) < page_size:
                break
            offset += page_size

        return sorted(names)

    def remove_old_images(self) -> None:
        names = self.list_image_names()
        old_names = names[:-MAX_REMOTE_IMAGES]
        if not old_names:
            return

        self.client.storage.from_(BUCKET_NAME).remove(old_names)
        for name in old_names:
            print(f"Removed old image: {name}", flush=True)
