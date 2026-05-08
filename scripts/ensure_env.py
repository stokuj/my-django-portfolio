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
