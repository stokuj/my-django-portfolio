from __future__ import annotations

import argparse
import json
import subprocess
import sys


def build_status_table(rows: list[dict[str, str]]) -> str:
    if not rows:
        return "No matching containers found."

    headers = ["NAME", "STATUS", "IMAGE", "PORTS"]
    widths = {
        "name": max(len("NAME"), *(len(row["name"]) for row in rows)),
        "status": max(len("STATUS"), *(len(row["status"]) for row in rows)),
        "image": max(len("IMAGE"), *(len(row["image"]) for row in rows)),
        "ports": max(len("PORTS"), *(len(row["ports"]) for row in rows)),
    }

    header = (
        f"{headers[0]:<{widths['name']}}  "
        f"{headers[1]:<{widths['status']}}  "
        f"{headers[2]:<{widths['image']}}  "
        f"{headers[3]:<{widths['ports']}}"
    )

    lines = [header]
    for row in rows:
        lines.append(
            f"{row['name']:<{widths['name']}}  "
            f"{row['status']:<{widths['status']}}  "
            f"{row['image']:<{widths['image']}}  "
            f"{row['ports']:<{widths['ports']}}"
        )

    return "\n".join(lines)


def load_rows(project_name: str) -> list[dict[str, str]]:
    command = [
        "docker",
        "ps",
        "-a",
        "--filter",
        f"label=com.docker.compose.project={project_name}",
        "--format",
        "{{json .}}",
    ]
    result = subprocess.run(command, check=True, capture_output=True, text=True)
    rows: list[dict[str, str]] = []
    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        parsed = json.loads(line)
        rows.append(
            {
                "name": parsed.get("Names", ""),
                "status": parsed.get("Status", ""),
                "image": parsed.get("Image", ""),
                "ports": parsed.get("Ports", ""),
            }
        )
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("project_name")
    args = parser.parse_args()

    try:
        rows = load_rows(args.project_name)
    except subprocess.CalledProcessError as exc:
        print(exc.stderr.strip() or "docker ps failed", file=sys.stderr)
        return 1

    print(build_status_table(rows))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
