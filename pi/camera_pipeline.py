import argparse
import os
import time

from services.camera import CameraCaptureError, capture_image
from services.image_storage import ImageStorageService
from services.supabase_api import load_supabase_config


DEFAULT_INTERVAL_SECONDS = 600


def configured_interval() -> float:
    value = os.getenv("CAMERA_CAPTURE_INTERVAL_SECONDS", str(DEFAULT_INTERVAL_SECONDS))
    try:
        interval = float(value)
    except ValueError as error:
        raise RuntimeError("CAMERA_CAPTURE_INTERVAL_SECONDS must be a number.") from error
    if interval <= 0:
        raise RuntimeError("Camera capture interval must be greater than zero.")
    return interval


def capture_and_upload(storage: ImageStorageService) -> str | None:
    try:
        image_path = capture_image()
    except CameraCaptureError as error:
        print(error, flush=True)
        return None

    try:
        public_url = storage.upload_image(image_path)
    except Exception as error:
        print(f"Image upload failed: {error}", flush=True)
        print(f"Local image kept at: {image_path}", flush=True)
        return None

    image_path.unlink(missing_ok=True)
    return public_url


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Capture and upload fridge images.")
    parser.add_argument(
        "--once",
        action="store_true",
        help="Capture and upload one image immediately, then exit.",
    )
    parser.add_argument(
        "--interval",
        type=float,
        help="Seconds between captures (overrides CAMERA_CAPTURE_INTERVAL_SECONDS).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    try:
        supabase_url, secret_key = load_supabase_config()
        interval = args.interval if args.interval is not None else configured_interval()
        if interval <= 0:
            raise RuntimeError("Camera capture interval must be greater than zero.")
    except RuntimeError as error:
        raise SystemExit(error) from error

    storage = ImageStorageService(supabase_url, secret_key)

    if args.once:
        if capture_and_upload(storage) is None:
            raise SystemExit(1)
        return

    print(f"Camera pipeline running every {interval:g} seconds. Press Ctrl+C to stop.")
    try:
        while True:
            capture_and_upload(storage)
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\nCamera pipeline stopped.")


if __name__ == "__main__":
    main()
