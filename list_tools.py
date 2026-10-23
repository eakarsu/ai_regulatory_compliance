"""Pure list helpers for governed policies: search/filter + CSV export."""
import csv
import io

POLICY_COLUMNS = ["policy_key", "version", "status", "reviewer_id", "legal_hold"]


def filter_policies(rows, q="", status=""):
    needle = str(q or "").strip().lower()
    result = []
    for row in rows:
        if status and row.get("status") != status:
            continue
        if needle and not any(needle in str(row.get(key) or "").lower() for key in ("policy_key", "status", "reviewer_id")):
            continue
        result.append(row)
    return result


def policies_to_csv(rows, columns=POLICY_COLUMNS):
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(columns)
    for row in rows:
        writer.writerow(["" if row.get(col) is None else row.get(col) for col in columns])
    return buffer.getvalue()
