"""Read/update backend/.env in place, preserving comments and ordering.

Lets the Settings page persist API keys and email config without a database
migration — matches how config already works everywhere else in this app.
Not suitable for a Docker deployment where .env is baked into the image
rather than mounted as a live volume (see SETUP.md).
"""

from pathlib import Path

ENV_PATH = Path(__file__).resolve().parent.parent.parent / ".env"


def update_env_file(updates: dict[str, str]) -> None:
    lines = ENV_PATH.read_text(encoding="utf-8").splitlines() if ENV_PATH.exists() else []

    remaining = dict(updates)
    new_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and "=" in stripped:
            key = stripped.split("=", 1)[0]
            if key in remaining:
                new_lines.append(f"{key}={remaining.pop(key)}")
                continue
        new_lines.append(line)

    for key, value in remaining.items():
        new_lines.append(f"{key}={value}")

    ENV_PATH.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
