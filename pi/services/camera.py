import subprocess
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_IMAGE_DIR = Path(__file__).resolve().parents[1] / "data" / "images"


class CameraCaptureError(RuntimeError):
    pass


def image_filename(captured_at: datetime | None = None) -> str:
    captured_at = captured_at or datetime.now(timezone.utc)
    return f"fridge-{captured_at.astimezone(timezone.utc):%Y%m%dT%H%M%SZ}.jpg"


def capture_image(
    output_dir: Path = DEFAULT_IMAGE_DIR,
    captured_at: datetime | None = None,
    runner: Callable = subprocess.run,
) -> Path:
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
                "1920",
                "--height",
                "1080",
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

    print(f"Image captured: {output_path}", flush=True)
    return output_path
