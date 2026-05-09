import argparse
import sys
from pathlib import Path


def ensure_env(env_path: Path, example_path: Path, create_if_missing: bool) -> bool:
    if env_path.exists():
        return False

    if not example_path.exists():
        raise FileNotFoundError(f"Missing example env file: {example_path}")

    if not create_if_missing:
        raise FileNotFoundError(f"Missing env file: {env_path}")

    env_path.write_text(example_path.read_text(encoding="utf-8"), encoding="utf-8")
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["dev", "prod"])
    parser.add_argument("--env-file", default=".env")
    parser.add_argument("--example-file", default=".env.example")
    args = parser.parse_args()

    try:
        created = ensure_env(
            env_path=Path(args.env_file),
            example_path=Path(args.example_file),
            create_if_missing=args.mode == "dev",
        )
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if created:
        print(f"Created {args.env_file} from {args.example_file}.")
    else:
        print(f"Using existing {args.env_file}.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
