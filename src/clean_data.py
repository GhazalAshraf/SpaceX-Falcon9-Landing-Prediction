"""Clean the historical launch CSV and prepare Falcon 9 landing labels."""

import csv
from pathlib import Path
from typing import Optional


PROJECT_ROOT = Path(__file__).resolve().parent.parent
INPUT_PATH = PROJECT_ROOT / "data" / "raw" / "launches.csv"
OUTPUT_DIR = PROJECT_ROOT / "data" / "processed"
CLEANED_PATH = OUTPUT_DIR / "falcon9_launches_cleaned.csv"
LABELED_PATH = OUTPUT_DIR / "falcon9_launches_labeled.csv"
ENCODING = "cp1252"
REQUIRED_COLUMNS = {"Booster Version", "Landing Outcome"}
LABEL_COLUMN = "landing_success"


def normalize_row(row: dict[str, Optional[str]]) -> dict[str, Optional[str]]:
    """Trim text and represent empty source fields as missing values."""
    if None in row:
        raise ValueError("A CSV row has more values than the header.")

    return {
        column: value.strip() or None if value is not None else None
        for column, value in row.items()
        if column is not None
    }


def landing_label(outcome: str | None) -> str | None:
    """Return a binary label only for explicit successful or failed outcomes."""
    if outcome is None:
        return None

    normalized = outcome.casefold()
    if normalized.startswith("success"):
        return "1"
    if normalized.startswith(("failure", "uncontrolled")):
        return "0"
    return None


def clean_launches() -> tuple[int, int, int]:
    """Filter, deduplicate, label, and save historical Falcon 9 launches."""
    for output_path in (CLEANED_PATH, LABELED_PATH):
        if output_path.exists():
            raise FileExistsError(
                f"Refusing to overwrite existing output file: {output_path}"
            )

    with INPUT_PATH.open("r", encoding=ENCODING, newline="") as input_file:
        reader = csv.DictReader(input_file)
        if not reader.fieldnames or not REQUIRED_COLUMNS.issubset(reader.fieldnames):
            raise ValueError("Input CSV is missing required launch columns.")

        columns = reader.fieldnames
        unique_rows: list[dict[str, Optional[str]]] = []
        seen_rows: set[tuple[Optional[str], ...]] = set()
        duplicate_count = 0

        for source_row in reader:
            row = normalize_row(source_row)
            row_key = tuple(row[column] for column in columns)
            if row_key in seen_rows:
                duplicate_count += 1
                continue
            seen_rows.add(row_key)
            unique_rows.append(row)

    falcon9_rows = [
        row
        for row in unique_rows
        if (row["Booster Version"] or "").startswith("F9")
    ]

    cleaned_rows: list[dict[str, Optional[str]]] = []
    labeled_rows: list[dict[str, Optional[str]]] = []
    for row in falcon9_rows:
        label = landing_label(row["Landing Outcome"])
        cleaned_row = {**row, LABEL_COLUMN: label}
        cleaned_rows.append(cleaned_row)
        if label is not None:
            labeled_rows.append(cleaned_row)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_columns = [*columns, LABEL_COLUMN]
    for output_path, rows in (
        (CLEANED_PATH, cleaned_rows),
        (LABELED_PATH, labeled_rows),
    ):
        with output_path.open("x", encoding="utf-8", newline="") as output_file:
            writer = csv.DictWriter(output_file, fieldnames=output_columns)
            writer.writeheader()
            writer.writerows(rows)

    print(f"Removed exact duplicate rows: {duplicate_count}")
    print(f"Falcon 9 launch records saved: {len(cleaned_rows)}")
    print(f"Records with explicit binary landing labels: {len(labeled_rows)}")
    print(f"Cleaned data: {CLEANED_PATH}")
    print(f"Labeled data: {LABELED_PATH}")
    return duplicate_count, len(cleaned_rows), len(labeled_rows)


if __name__ == "__main__":
    clean_launches()
