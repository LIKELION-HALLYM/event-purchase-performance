import asyncio
import csv

from playwright.async_api import async_playwright

START_URL = "https://www.29cm.co.kr/best-products?period=HOURLY&ranking=POPULARITY&gender=F&age=30"

TARGET_COUNT = 10000
OUTPUT_FILE = "29cm_products.csv"

CSV_COLUMNS = [
    "product_name",
    "brand",
    "category",
    "price",
    "discount_rate",
    "rating",
    "review_count",
    "image_url",
    "source",
    "source_url",
]


def normalize_item(item):
    item_info = item.get("itemInfo", {})
    event = item.get("itemEvent", {}).get("eventProperties", {})

    return {
        "product_name": item_info.get("productName", ""),
        "brand": item_info.get("brandName", ""),
        "category": event.get("smallCategoryName", ""),
        "price": item_info.get("displayPrice", 0),
        "discount_rate": item_info.get("saleRate", 0),
        "rating": item_info.get("reviewScore", 0),
        "review_count": item_info.get("reviewCount", 0),
        "image_url": item_info.get("thumbnailUrl", ""),
        "source": "29CM",
        "source_url": item.get("itemUrl", {}).get("webLink", ""),
    }


def save_csv(rows):
    with open(OUTPUT_FILE, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


async def main():
    result = []
    seen_urls = set()

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            slow_mo=50,
        )

        page = await browser.new_page()

        async def handle_response(response):
            try:
                url = response.url

                if response.status != 200:
                    return

                content_type = response.headers.get("content-type", "")

                if "application/json" not in content_type:
                    return

                data = await response.json()

                items = data.get("data", {}).get("list", [])

                if not items:
                    return

                for item in items:
                    row = normalize_item(item)

                    source_url = row["source_url"]

                    if not source_url:
                        continue

                    if source_url in seen_urls:
                        continue

                    seen_urls.add(source_url)
                    result.append(row)

                print(f"[SAVE] 현재 상품 수집 개수: {len(result)}")

                save_csv(result)

            except Exception:
                pass

        page.on("response", handle_response)

        await page.goto(
            START_URL,
            wait_until="domcontentloaded",
            timeout=60000,
        )

        await page.wait_for_timeout(3000)

        scroll_count = 0

        while len(result) < TARGET_COUNT:
            scroll_count += 1

            print(f"[SCROLL] {scroll_count}")

            await page.mouse.wheel(0, 5000)
            await page.wait_for_timeout(2000)

        await browser.close()

    save_csv(result)

    print(f"[DONE] 총 {len(result)}개 저장 완료")


if __name__ == "__main__":
    asyncio.run(main())