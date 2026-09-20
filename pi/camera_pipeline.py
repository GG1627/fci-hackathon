import argparse
import os
import time

from services.camera import (
    DEFAULT_IMAGE_HEIGHT,
    DEFAULT_IMAGE_WIDTH,
    DEFAULT_JPEG_QUALITY,
    CameraCaptureError,
    capture_image,
)
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


def configured_int(
    name: str,
    default: int,
    minimum: int,
    maximum: int | None = None,
) -> int:
    value = os.getenv(name, str(default))
    try:
        parsed = int(value)
    except ValueError as error:
        raise RuntimeError(f"{name} must be a whole number.") from error
    if parsed < minimum or (maximum is not None and parsed > maximum):
        range_text = (
            f"{minimum} to {maximum}"
            if maximum is not None
            else f"at least {minimum}"
        )
        raise RuntimeError(f"{name} must be {range_text}.")
    return parsed


def capture_and_upload(
    storage: ImageStorageService,
    width: int,
    height: int,
    quality: int,
) -> str | None:
    try:
        image_path = capture_image(width=width, height=height, quality=quality)
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
    parser.add_argument("--width", type=int, help="Captured image width in pixels.")
    parser.add_argument("--height", type=int, help="Captured image height in pixels.")
    parser.add_argument("--quality", type=int, help="JPEG quality from 1 to 100.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    try:
        supabase_url, secret_key = load_supabase_config()
        interval = args.interval if args.interval is not None else configured_interval()
        if interval <= 0:
            raise RuntimeError("Camera capture interval must be greater than zero.")
        width = (
            args.width
            if args.width is not None
            else configured_int("CAMERA_IMAGE_WIDTH", DEFAULT_IMAGE_WIDTH, 1)
        )
        height = (
            args.height
            if args.height is not None
            else configured_int("CAMERA_IMAGE_HEIGHT", DEFAULT_IMAGE_HEIGHT, 1)
        )
        quality = (
            args.quality
            if args.quality is not None
            else configured_int("CAMERA_JPEG_QUALITY", DEFAULT_JPEG_QUALITY, 1, 100)
        )
        if width <= 0 or height <= 0 or not 1 <= quality <= 100:
            raise RuntimeError("Width/height must be positive and quality must be 1 to 100.")
    except RuntimeError as error:
        raise SystemExit(error) from error

    storage = ImageStorageService(supabase_url, secret_key)

    if args.once:
        if capture_and_upload(storage, width, height, quality) is None:
            raise SystemExit(1)
        return

    print(
        f"Camera pipeline running every {interval:g} seconds at "
        f"{width}x{height}, JPEG quality {quality}. Press Ctrl+C to stop."
    )
    try:
        while True:
            capture_and_upload(storage, width, height, quality)
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\nCamera pipeline stopped.")


if __name__ == "__main__":
    main()
