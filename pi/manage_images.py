import argparse

from services.image_storage import ImageStorageService
from services.supabase_api import load_supabase_config


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Manage FridgeGuard cloud images.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("list", help="List timestamped FridgeGuard images.")
    clear_parser = subparsers.add_parser(
        "clear", help="Delete all timestamped FridgeGuard images."
    )
    clear_parser.add_argument(
        "--yes",
        action="store_true",
        help="Confirm permanent deletion.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.command == "clear" and not args.yes:
        raise SystemExit(
            "This permanently deletes the FridgeGuard images. Add --yes to confirm."
        )

    try:
        supabase_url, secret_key = load_supabase_config()
        storage = ImageStorageService(supabase_url, secret_key)

        if args.command == "list":
            names = storage.list_image_names()
            if not names:
                print("No FridgeGuard images found.")
                return
            for name in names:
                print(name)
            print(f"Total: {len(names)}")
            return

        removed = storage.clear_images()
        print(f"Cleared {removed} FridgeGuard image(s).")
    except RuntimeError as error:
        raise SystemExit(error) from error
    except Exception as error:
        raise SystemExit(f"Supabase image command failed: {error}") from error


if __name__ == "__main__":
    main()
