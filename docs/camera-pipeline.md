# Camera image pipeline

The Camera Module 3 pipeline is independent from ESP32 serial logging and
SQLite. It captures a JPEG with `rpicam-still`, uploads it to the public
Supabase Storage bucket `fridge-images`, and keeps only the newest three remote
images.

## Configuration

The root `.env` file must contain:

```text
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SECRET_KEY=your-server-only-secret
CAMERA_CAPTURE_INTERVAL_SECONDS=600
CAMERA_IMAGE_WIDTH=1280
CAMERA_IMAGE_HEIGHT=720
CAMERA_JPEG_QUALITY=75
```

Never commit `.env` or expose the secret key in the web application.

The default interval is 600 seconds (10 minutes). For a 30-second demo, either
change the environment value or pass `--interval 30`.

## Install

Use a Raspberry Pi OS virtual environment that can access system packages:

```bash
python3 -m venv --system-site-packages venv
source venv/bin/activate
python3 -m pip install -r requirements.txt
```

## Capture one image now

```bash
python3 pi/camera_pipeline.py --once
```

The command prints the public URL after a successful upload.

## Run periodically

Production interval from `.env`:

```bash
python3 pi/camera_pipeline.py
```

Thirty-second demo interval:

```bash
python3 pi/camera_pipeline.py --interval 30
```

You can also override image settings for a test. The defaults are deliberately
web-friendly: 1280x720 JPEG at quality 75 with no embedded thumbnail.

```bash
python3 pi/camera_pipeline.py --interval 30 --width 1280 --height 720 --quality 75
```

Stop the scheduler with `Ctrl+C`.

Images use UTC names such as `fridge-20260920T190500Z.jpg`. Successfully
uploaded local files are removed. If capture succeeds but upload fails, the
JPEG remains under `pi/data/images/` for inspection and the next scheduled
capture still runs.

The pipeline creates `fridge-images` as a public JPEG-only bucket when it does
not exist. If that bucket already exists but is private, make it public in the
Supabase Dashboard so the displayed URL works in a browser.

## Inspect or clear cloud images

The pipeline automatically deletes images older than the newest three, so the
bucket does not grow indefinitely. List the managed images with:

```bash
python3 pi/manage_images.py list
```

To permanently delete all timestamped FridgeGuard images from `fridge-images`:

```bash
python3 pi/manage_images.py clear --yes
```

The clear command intentionally ignores any object that does not match the
pipeline's `fridge-YYYYMMDDTHHMMSSZ.jpg` naming convention.
