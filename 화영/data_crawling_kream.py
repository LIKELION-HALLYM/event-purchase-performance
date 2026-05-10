import re
import time
import pandas as pd

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


START_URL = "https://kream.co.kr/search?tab=49&shop_category_id=164&title=%EB%A0%88%EB%8D%94%20%EC%9E%90%EC%BC%93&exclude_filter=shop_category_id"
CATEGORY_NAME = "아우터"
SUB_CATEGORY_NAME = "레더자켓"
TARGET_COUNT = 200


def create_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--window-size=1400,1000")
    options.add_argument("--disable-blink-features=AutomationControlled")

    return webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )


def clean_price(text):
    match = re.search(r"([\d,]+)\s*원", text)
    return match.group(1).replace(",", "") if match else ""


def clean_discount_rate(text):
    match = re.search(r"(\d+)%", text)
    return match.group(1) if match else ""


def clean_review_count(text):
    match = re.search(r"리뷰\s*([\d,]+)", text)
    return match.group(1).replace(",", "") if match else ""


def clean_rating(text):
    match = re.search(r"★\s*([\d.]+)", text)
    return match.group(1) if match else ""


def extract_brand_and_name(lines):
    skip_keywords = [
        "관심",
        "리뷰",
        "거래",
        "빠른배송",
        "내일 도착 예정",
        "무료배송",
        "즉시 구매가",
        "구매가",
        "쿠폰",
        "혜택",
    ]

    candidates = []

    for line in lines:
        if any(keyword in line for keyword in skip_keywords):
            continue
        if re.search(r"\d+%", line):
            continue
        if re.search(r"[\d,]+\s*원", line):
            continue

        candidates.append(line)

    if len(candidates) >= 2:
        return candidates[0], candidates[1]

    if len(candidates) == 1:
        return candidates[0], ""

    return "", ""


def extract_card_data(link, category_name, sub_category_name):
    text = link.text.strip()
    lines = [line.strip() for line in text.split("\n") if line.strip()]

    brand, product_name = extract_brand_and_name(lines)

    image_url = ""
    try:
        img = link.find_element(By.CSS_SELECTOR, "img")
        image_url = img.get_attribute("src") or ""
    except Exception:
        pass

    return {
        "product_name": product_name,
        "brand": brand,
        "category": category_name,
        "sub_category": sub_category_name,
        "price": clean_price(text),
        "discount_rate": clean_discount_rate(text),
        "rating": clean_rating(text),
        "review_count": clean_review_count(text),
        "image_url": image_url,
        "source": "KREAM",
        "source_url": link.get_attribute("href") or "",
    }


def save_csv(products):
    df = pd.DataFrame(products)

    file_name = f"kream_{SUB_CATEGORY_NAME}.csv"
    df.to_csv(file_name, index=False, encoding="utf-8-sig")

    print("CSV 저장 완료")
    print(f"파일명: {file_name}")
    print(f"총 수집 개수: {len(df)}")


def crawl_kream_category(start_url, category_name, sub_category_name):
    driver = create_driver()
    products = []
    seen_urls = set()

    no_new_count = 0
    prev_count = 0

    try:
        driver.get(start_url)
        time.sleep(5)

        while len(products) < TARGET_COUNT:
            links = driver.find_elements(By.CSS_SELECTOR, 'a[href*="/products/"]')

            new_links = []

            for link in links:
                source_url = link.get_attribute("href") or ""

                if not source_url:
                    continue

                if source_url in seen_urls:
                    continue

                seen_urls.add(source_url)
                new_links.append(link)

            print(
                f"현재 화면 링크 수: {len(links)} / "
                f"새 링크 수: {len(new_links)} / "
                f"수집 완료: {len(products)}"
            )

            for link in new_links:
                product = extract_card_data(link, category_name, sub_category_name)
                products.append(product)

                print(
                    f"{len(products)}개 수집 | "
                    f"{product['brand']} | "
                    f"{product['product_name']} | "
                    f"{product['price']}원 | "
                    f"리뷰 {product['review_count']}"
                )

                if len(products) >= TARGET_COUNT:
                    break

            if len(products) == prev_count:
                no_new_count += 1
            else:
                no_new_count = 0

            prev_count = len(products)

            if no_new_count >= 10:
                print("더 이상 새 상품이 로딩되지 않아 종료합니다.")
                break

            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)

    except KeyboardInterrupt:
        print("사용자가 중단했습니다. 현재까지 수집한 데이터를 저장합니다.")

    finally:
        driver.quit()
        save_csv(products)

    return products


if __name__ == "__main__":
    crawl_kream_category(
        start_url=START_URL,
        category_name=CATEGORY_NAME,
        sub_category_name=SUB_CATEGORY_NAME
    )