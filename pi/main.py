import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parents[1]
PI_DIR = ROOT_DIR / "pi"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the FridgeGuard Pi services.")
    parser.add_argument(
        "--camera-interval",
        type=float,
        help="Override the camera interval in seconds (for example, 30).",
    )
    parser.add_argument(
        "--no-camera",
        action="store_true",
        help="Run without the camera capture service.",
    )
    parser.add_argument(
        "--no-alerts",
        action="store_true",
        help="Run without the Discord alert monitor.",
    )
    return parser.parse_args()


def service_commands(args: argparse.Namespace) -> list[tuple[str, list[str]]]:
    python = sys.executable
    commands = [
        ("serial logger", [python, "-u", str(PI_DIR / "serial_test.py")]),
        ("local API", [python, "-u", str(PI_DIR / "api.py")]),
    ]

    if not args.no_camera:
        camera_command = [python, "-u", str(PI_DIR / "camera_pipeline.py")]
        if args.camera_interval is not None:
            if args.camera_interval <= 0:
                raise RuntimeError("--camera-interval must be greater than zero.")
            camera_command.extend(["--interval", str(args.camera_interval)])
        commands.append(("camera pipeline", camera_command))

    webhook_configured = bool(os.getenv("DISCORD_WEBHOOK_URL", "").strip())
    if not args.no_alerts and webhook_configured:
        commands.append(
            ("Discord alerts", [python, "-u", str(PI_DIR / "alert_monitor.py")])
        )
    elif not args.no_alerts:
        print("Discord alerts disabled: DISCORD_WEBHOOK_URL is not configured.")

    return commands


def stop_services(processes: list[tuple[str, subprocess.Popen]]) -> None:
    for name, process in processes:
        if process.poll() is None:
            print(f"Stopping {name}...", flush=True)
            process.terminate()

    for _, process in processes:
        if process.poll() is not None:
            continue
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()


def main() -> None:
    load_dotenv(ROOT_DIR / ".env")
    args = parse_args()
    try:
        commands = service_commands(args)
    except RuntimeError as error:
        raise SystemExit(error) from error

    processes: list[tuple[str, subprocess.Popen]] = []
    failed = False
    try:
        for name, command in commands:
            print(f"Starting {name}...", flush=True)
            process = subprocess.Popen(command, cwd=ROOT_DIR)
            processes.append((name, process))

        print("FridgeGuard is running. Press Ctrl+C to stop all services.", flush=True)
        while True:
            for name, process in processes:
                exit_code = process.poll()
                if exit_code is not None:
                    raise RuntimeError(
                        f"{name} stopped unexpectedly with exit code {exit_code}."
                    )
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping FridgeGuard...", flush=True)
    except RuntimeError as error:
        print(error, flush=True)
        failed = True
    finally:
        stop_services(processes)

    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
