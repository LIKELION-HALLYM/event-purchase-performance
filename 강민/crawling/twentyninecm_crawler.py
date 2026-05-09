import argparse
import csv
import json
import sys
import time
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path


API_URL = "https://display-bff-api.29cm.co.kr/api/v1/listing/items?colorchipVariant=control"
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

CATEGORY_CODES = [
    268100100,  # women clothing
    270100100,  # women shoes
    269100100,  # women bags
    271100100,  # women accessories
    272100100,  # men clothing
    274100100,  # men shoes
    273100100,  # men bags
    275100100,  # men accessories
    266100100,  # beauty
    292100100,  # kitchen/living
    291100100,  # furniture/interior
    294100100,  # computer/digital
    293100100,  # electronics
    265100100,  # culture
    286100100,  # leisure
    290100100,  # kids
    289100100,  # food
    307100100,  # earth
]


def normalize_none(value):
    return NULL_TEXT if value is None or value == "" else value


def post_listing(body, timeout, user_agent):
    payload = json.dumps(body).encode("utf-8")
    request = urllib.request.Request(
        API_URL,
        data=payload,
        method="POST",
        headers={
            "User-Agent": user_agent,
            "Accept": "application/json",
            "Content-Type": "application/json; charset=utf-8",
            "Origin": "https://www.29cm.co.kr",
            "Referer": "https://www.29cm.co.kr/",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return json.loads(response.read().decode(charset, errors="replace"))


def product_from_item(item):
    if item.get("itemType") != "PRODUCT":
        return None

    item_info = item.get("itemInfo") if isinstance(item.get("itemInfo"), dict) else {}
    event = item.get("itemEvent") if isinstance(item.get("itemEvent"), dict) else {}
    event_props = event.get("eventProperties") if isinstance(event.get("eventProperties"), dict) else {}
    item_url = item.get("itemUrl") if isinstance(item.get("itemUrl"), dict) else {}

    if item_info.get("isSoldOut") or event_props.get("isSoldout"):
        return {"_skip_reason": "sold_out", "source_url": item_url.get("webLink")}

    product_name = item_info.get("productName") or event_props.get("itemName")
    brand = item_info.get("brandName") or event_props.get("brandName")
    category = event_props.get("largeCategoryName")
    sub_category = event_props.get("middleCategoryName") or event_props.get("smallCategoryName")
    price = item_info.get("displayPrice") or event_props.get("price")
    source_url = item_url.get("webLink") or f"https://product.29cm.co.kr/catalog/{item.get('itemId')}"

    return {
        "product_name": product_name,
        "brand": brand,
        "category": category,
        "sub_category": sub_category,
        "price": int(price) if isinstance(price, (int, float)) else price,
        "discount_rate": item_info.get("saleRate") if item_info.get("saleRate") is not None else event_props.get("discountRate"),
        "rating": item_info.get("reviewScore"),
        "review_count": item_info.get("reviewCount"),
        "tags": "|".join(
            badge.get("text", "")
            for badge in item_info.get("textBadges", [])
            if isinstance(badge, dict) and badge.get("text")
        )
        or None,
        "description": None,
        "image_url": item_info.get("thumbnailUrl"),
        "source": SOURCE,
        "source_url": source_url,
    }


def write_csv(rows, output_path):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(
            {
                field: normalize_none(row.get(field))
                for field in FIELDS
            }
            for row in rows
        )


def write_lines(lines, output_path):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def write_report(report_path, stats, output_path, urls_path):
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        "\n".join(
            [
                "# 29CM Crawling Result",
                "",
                f"- Run date: {date.today().isoformat()}",
                "- Target count standard: 10000 products",
                f"- Requested pages: {stats['requested_pages']}",
                f"- Success products: {stats['success']}",
                f"- Sold out skipped: {stats['sold_out']}",
                f"- Duplicate skipped: {stats['duplicate']}",
                f"- Parse failed: {stats['parse_failed']}",
                f"- HTTP 429: {stats['rate_limited']}",
                f"- Other failed: {stats['failed']}",
                f"- Output raw CSV: `{output_path.as_posix()}`",
                f"- Product URL list: `{urls_path.as_posix()}`",
                "- Source rule: `source` is fixed as `29cm`",
                "- URL rule: `source_url` is the 29CM product detail URL",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def crawl(args):
    rows = []
    urls = []
    seen_product_ids = set()
    seen_dedupe = set()
    sold_out_urls = []
    failed_pages = []
    stats = {
        "requested_pages": 0,
        "success": 0,
        "sold_out": 0,
        "duplicate": 0,
        "parse_failed": 0,
        "rate_limited": 0,
        "failed": 0,
    }

    for category_code in args.category_code:
        page = 1
        while len(rows) < args.target_count:
            body = {
                "pageType": "CATEGORY_PLP",
                "largeCategoryCode": category_code,
                "pageRequest": {"page": page, "size": args.page_size},
                "sortType": args.sort_type,
            }
            stats["requested_pages"] += 1
            try:
                data = post_listing(body, args.timeout, args.user_agent)
            except urllib.error.HTTPError as error:
                if error.code == 429:
                    stats["rate_limited"] += 1
                    time.sleep(args.retry_delay)
                else:
                    stats["failed"] += 1
                    failed_pages.append(f"{category_code}\t{page}\tHTTP {error.code}")
                if page == 1:
                    break
                page += 1
                continue
            except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as error:
                stats["failed"] += 1
                failed_pages.append(f"{category_code}\t{page}\t{error}")
                if page == 1:
                    break
                page += 1
                continue

            if data.get("meta", {}).get("result") != "SUCCESS":
                stats["failed"] += 1
                failed_pages.append(f"{category_code}\t{page}\t{data.get('meta') or data.get('message')}")
                break

            payload = data.get("data") if isinstance(data.get("data"), dict) else {}
            items = payload.get("list") if isinstance(payload.get("list"), list) else []
            if not items:
                break

            for item in items:
                product_id = item.get("itemId")
                if product_id in seen_product_ids:
                    stats["duplicate"] += 1
                    continue
                product = product_from_item(item)
                if product and product.get("_skip_reason") == "sold_out":
                    stats["sold_out"] += 1
                    if product.get("source_url"):
                        sold_out_urls.append(product["source_url"])
                    continue
                if not product:
                    stats["parse_failed"] += 1
                    continue

                required = ["product_name", "brand", "category", "price", "source", "source_url"]
                if any(product.get(field) in (None, "") for field in required):
                    stats["parse_failed"] += 1
                    continue

                dedupe_key = (str(product["brand"]).strip().lower(), str(product["product_name"]).strip().lower())
                if dedupe_key in seen_dedupe:
                    stats["duplicate"] += 1
                    continue

                seen_product_ids.add(product_id)
                seen_dedupe.add(dedupe_key)
                rows.append(product)
                urls.append(product["source_url"])
                stats["success"] += 1
                if len(rows) >= args.target_count:
                    break

            print(f"category={category_code} page={page} saved={len(rows)}")
            pagination = payload.get("pagination") if isinstance(payload.get("pagination"), dict) else {}
            if not pagination.get("hasNext"):
                break
            page += 1
            time.sleep(args.delay)

        if len(rows) >= args.target_count:
            break

    output_path = Path(args.output)
    urls_path = Path(args.urls_output)
    log_dir = Path(args.log_dir)
    write_csv(rows, output_path)
    write_lines(urls, urls_path)
    write_lines(sold_out_urls, log_dir / "29cm_sold_out_urls.txt")
    write_lines(failed_pages, log_dir / "29cm_failed_pages.txt")
    write_report(Path(args.report), stats, output_path, urls_path)
    return rows, stats


def main():
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description="Crawl 29CM products into the common product CSV schema.")
    parser.add_argument("--target-count", type=int, default=10000)
    parser.add_argument("--page-size", type=int, default=100)
    parser.add_argument("--delay", type=float, default=1.0)
    parser.add_argument("--retry-delay", type=float, default=5.0)
    parser.add_argument("--timeout", type=int, default=20)
    parser.add_argument("--sort-type", default="RECOMMENDED")
    parser.add_argument("--category-code", type=int, action="append", default=CATEGORY_CODES)
    parser.add_argument("--output", default=str(root / "data/raw/29cm_products_raw.csv"))
    parser.add_argument("--urls-output", default=str(root / "data/raw/29cm_product_urls.txt"))
    parser.add_argument("--log-dir", default=str(root / "data/logs"))
    parser.add_argument("--report", default=str(root / "data/reports/29cm_crawling_result.md"))
    parser.add_argument("--user-agent", default="Mozilla/5.0 KKM-Crawling-Project")
    args = parser.parse_args()

    rows, stats = crawl(args)
    print(f"Saved {len(rows)} products to {args.output}")
    print(json.dumps(stats, ensure_ascii=False, indent=2))
    return 0 if len(rows) >= args.target_count else 1


if __name__ == "__main__":
    raise SystemExit(main())
