def build_status_table(rows: list[dict[str, str]]) -> str:
    if not rows:
        return "No matching containers found."

    headers = ["NAME", "STATUS", "IMAGE", "PORTS"]
    widths = {
        "NAME": max(len("NAME"), *(len(row["name"]) for row in rows)),
        "STATUS": max(len("STATUS"), *(len(row["status"]) for row in rows)),
        "IMAGE": max(len("IMAGE"), *(len(row["image"]) for row in rows)),
        "PORTS": max(len("PORTS"), *(len(row["ports"]) for row in rows)),
    }

    header = (
        f"{headers[0]:<{widths['NAME']}}  "
        f"{headers[1]:<{widths['STATUS']}}  "
        f"{headers[2]:<{widths['IMAGE']}}  "
        f"{headers[3]:<{widths['PORTS']}}"
    )

    lines = [header]
    for row in rows:
        lines.append(
            f"{row['name']:<{widths['NAME']}}  "
            f"{row['status']:<{widths['STATUS']}}  "
            f"{row['image']:<{widths['IMAGE']}}  "
            f"{row['ports']:<{widths['PORTS']}}"
        )

    return "\n".join(lines)
