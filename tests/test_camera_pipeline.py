import sys
import stat as stat_module
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch


ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR / "pi"))

from services.camera import capture_image, image_filename  # noqa: E402
from services.image_storage import ImageStorageService  # noqa: E402


class FakeBucket:
    def __init__(self, names: list[str]) -> None:
        self.names = names
        self.removed: list[str] = []

    def upload(self, path, file, file_options):
        if path not in self.names:
            self.names.append(path)

    def get_public_url(self, path):
        return f"https://example.test/fridge-images/{path}"

    def list(self, path, options):
        names = sorted(self.names)
        start = options["offset"]
        end = start + options["limit"]
        return [{"name": name} for name in names[start:end]]

    def remove(self, paths):
        self.removed.extend(paths)
        self.names = [name for name in self.names if name not in paths]


class FakeStorage:
    def __init__(self, bucket: FakeBucket) -> None:
        self.bucket = bucket

    def from_(self, name):
        return self.bucket


class FakeClient:
    def __init__(self, bucket: FakeBucket) -> None:
        self.storage = FakeStorage(bucket)


class CameraServiceTests(unittest.TestCase):
    def test_timestamped_filename_is_utc(self):
        captured_at = datetime(2026, 9, 20, 19, 5, tzinfo=timezone.utc)
        self.assertEqual(
            image_filename(captured_at),
            "fridge-20260920T190500Z.jpg",
        )

    def test_capture_invokes_rpicam_and_creates_jpeg(self):
        data_dir = ROOT_DIR / "pi" / "data"
        data_dir.mkdir(exist_ok=True)
        commands = []

        def fake_runner(command, **kwargs):
            commands.append(command)

        captured_at = datetime(2026, 9, 20, 19, 5, tzinfo=timezone.utc)
        with patch.object(Path, "is_file", return_value=True), patch.object(
            Path, "stat"
        ) as stat:
            stat.return_value.st_mode = stat_module.S_IFDIR
            stat.return_value.st_size = 8
            image_path = capture_image(
                data_dir,
                captured_at=captured_at,
                runner=fake_runner,
            )

        self.assertEqual(image_path.name, "fridge-20260920T190500Z.jpg")
        self.assertEqual(commands[0][0], "rpicam-still")
        self.assertIn("--nopreview", commands[0])
        self.assertEqual(commands[0][commands[0].index("--width") + 1], "1280")
        self.assertEqual(commands[0][commands[0].index("--height") + 1], "720")
        self.assertEqual(commands[0][commands[0].index("--quality") + 1], "75")
        self.assertEqual(commands[0][commands[0].index("--thumb") + 1], "none")


class ImageStorageTests(unittest.TestCase):
    def test_upload_keeps_only_newest_three_images(self):
        names = [
            "fridge-20260920T190000Z.jpg",
            "fridge-20260920T190100Z.jpg",
            "fridge-20260920T190200Z.jpg",
        ]
        bucket = FakeBucket(names)
        service = ImageStorageService("url", "key", client=FakeClient(bucket))
        service._bucket_ready = True

        image_path = Path("fridge-20260920T190300Z.jpg")
        public_url = service.upload_image(image_path)

        self.assertEqual(
            public_url,
            "https://example.test/fridge-images/fridge-20260920T190300Z.jpg",
        )
        self.assertEqual(bucket.removed, ["fridge-20260920T190000Z.jpg"])
        self.assertEqual(len(bucket.names), 3)

    def test_clear_removes_only_timestamped_fridge_images(self):
        names = [
            "fridge-20260920T190000Z.jpg",
            "fridge-20260920T190100Z.jpg",
            "do-not-delete.jpg",
        ]
        bucket = FakeBucket(names)
        service = ImageStorageService("url", "key", client=FakeClient(bucket))
        service._bucket_ready = True

        removed = service.clear_images()

        self.assertEqual(removed, 2)
        self.assertEqual(
            bucket.removed,
            [
                "fridge-20260920T190000Z.jpg",
                "fridge-20260920T190100Z.jpg",
            ],
        )
        self.assertEqual(bucket.names, ["do-not-delete.jpg"])


if __name__ == "__main__":
    unittest.main()
