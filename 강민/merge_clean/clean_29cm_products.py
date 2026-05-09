import argparse
import csv
import re
from datetime import date
from pathlib import Path


NULL_TEXT = "None"
SOURCE = "29cm"
FIELDS = [
    "product_name",
    "brand",
    "category",
    "sub_category",
    "price",
    "discount_rate",
    "rating",
    "review_count",
    "tags",
    "description",
    "image_url",
    "source",
    "source_url",
]
REQUIRED = ["product_name", "brand", "category", "price", "source", "source_url"]


def is_null(value):
    return value is None or str(value).strip() in {"", "None", "none", "NULL", "null", "NaN", "nan"}


def clean_text(value):
    if is_null(value):
        return NULL_TEXT
    value = re.sub(r"<[^>]+>", " ", str(value))
    value = re.sub(r"[\U00010000-\U0010ffff]", "", value)
    return re.sub(r"\s+", " ", value.strip())


def clean_int(value):
    if is_null(value):
        return NULL_TEXT
    digits = re.sub(r"[^0-9]", "", str(value))
    return digits or NULL_TEXT


def clean_float(value):
    if is_null(value):
        return NULL_TEXT
    cleaned = re.sub(r"[^0-9.]", "", str(value))
    return cleaned or NULL_TEXT


def clean_row(row):
    cleaned = {field: clean_text(row.get(field, "")) for field in FIELDS}
    cleaned["price"] = clean_int(cleaned["price"])
    cleaned["review_count"] = clean_int(cleaned["review_count"])
    cleaned["discount_rate"] = clean_float(cleaned["discount_rate"])
    cleaned["rating"] = clean_float(cleaned["rating"])
    cleaned["source"] = SOURCE
    return cleaned


def dedupe_key(row):
    return row.get("brand", "").lower(), row.get("product_name", "").lower()


def clean_csv(input_path, output_path, report_path, limit):
    with Path(input_path).open("r", encoding="utf-8-sig", newline="") as file:
        raw_rows = list(csv.DictReader(file))

    cleaned_rows = []
    seen = set()
    invalid_count = 0
    duplicate_count = 0
    abnormal_count = 0

    for row in raw_rows:
        cleaned = clean_row(row)
        if any(cleaned.get(field, NULL_TEXT) == NULL_TEXT for field in REQUIRED):
            invalid_count += 1
            continue
        if int(cleaned["price"]) <= 0:
            abnormal_count += 1
            continue
        if cleaned["discount_rate"] != NULL_TEXT and float(cleaned["discount_rate"]) > 100:
            abnormal_count += 1
            continue
        key = dedupe_key(cleaned)
        if key in seen:
            duplicate_count += 1
            continue
        seen.add(key)
        cleaned_rows.append(cleaned)
        if limit and len(cleaned_rows) >= limit:
            break

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(cleaned_rows)

    report_path = Path(report_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        "\n".join(
            [
                "# 29CM CSV Cleaning Result",
                "",
                f"- Run date: {date.today().isoformat()}",
                f"- Raw rows: {len(raw_rows)}",
                f"- Clean rows: {len(cleaned_rows)}",
                f"- Removed invalid rows: {invalid_count}",
                f"- Removed abnormal rows: {abnormal_count}",
                f"- Removed duplicates: {duplicate_count}",
                "- Duplicate rule: same brand + same product_name",
                "- Category rule: category/sub_category are kept as original 29CM labels",
                "- Null rule: optional missing values are saved as `None`",
                "- Encoding: UTF-8-sig",
                f"- Final limit: {limit or 'None'}",
                "- Output CSV: `data/processed/29cm_products_clean.csv`",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return len(raw_rows), len(cleaned_rows), invalid_count, duplicate_count, abnormal_count


def main():
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description="Clean and dedupe 29CM CSV.")
    parser.add_argument("--input", default=str(root / "data/raw/29cm_products_raw.csv"))
    parser.add_argument("--output", default=str(root / "data/processed/29cm_products_clean.csv"))
    parser.add_argument("--report", default=str(root / "data/reports/29cm_csv_cleaning_result.md"))
    parser.add_argument("--limit", type=int, default=10000)
    args = parser.parse_args()

    raw, clean, invalid, duplicate, abnormal = clean_csv(args.input, args.output, args.report, args.limit)
    print(f"raw={raw} clean={clean} invalid={invalid} duplicate={duplicate} abnormal={abnormal}")
    return 0 if clean >= (args.limit or 0) else 1


if __name__ == "__main__":
    raise SystemExit(main())
