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
