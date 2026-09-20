import subprocess
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_IMAGE_DIR = Path(__file__).resolve().parents[1] / "data" / "images"
DEFAULT_IMAGE_WIDTH = 1280
DEFAULT_IMAGE_HEIGHT = 720
DEFAULT_JPEG_QUALITY = 75


class CameraCaptureError(RuntimeError):
    pass


def image_filename(captured_at: datetime | None = None) -> str:
    captured_at = captured_at or datetime.now(timezone.utc)
    return f"fridge-{captured_at.astimezone(timezone.utc):%Y%m%dT%H%M%SZ}.jpg"


def capture_image(
    output_dir: Path = DEFAULT_IMAGE_DIR,
    captured_at: datetime | None = None,
    width: int = DEFAULT_IMAGE_WIDTH,
    height: int = DEFAULT_IMAGE_HEIGHT,
    quality: int = DEFAULT_JPEG_QUALITY,
    runner: Callable = subprocess.run,
) -> Path:
    if width <= 0 or height <= 0:
        raise ValueError("Image width and height must be greater than zero.")
    if not 1 <= quality <= 100:
        raise ValueError("JPEG quality must be between 1 and 100.")

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / image_filename(captured_at)

    print("Capturing image...", flush=True)
    try:
        runner(
            [
                "rpicam-still",
                "--output",
                str(output_path),
                "--encoding",
                "jpg",
                "--width",
                str(width),
                "--height",
                str(height),
                "--quality",
                str(quality),
                "--thumb",
                "none",
                "--timeout",
                "2000",
                "--nopreview",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError) as error:
        details = getattr(error, "stderr", "") or str(error)
        raise CameraCaptureError(f"Camera capture failed: {details.strip()}") from error

    if not output_path.is_file() or output_path.stat().st_size == 0:
        raise CameraCaptureError("Camera command completed without creating an image.")

    size_kb = output_path.stat().st_size / 1024
    print(f"Image captured: {output_path} ({size_kb:.1f} KB)", flush=True)
    return output_path
