import requests
import pandas as pd
import time

# ✅ 본인 쿠키 여기에 붙여넣기
MY_COOKIE = "_fbp=fb.1.1777529154295.15840950618656135; _fwb=98xRID7aVPbMWd70iw7mJ2.1777529154377; ZIGZAGUUID=68924dfc-5676-41f1-b0f5-667eed9ce04d.dBDYYUVgyC9SfoZ0%2BhI%2BChjb1MObe9xheo%2Bp6FG8WCM; ZIGZAG_FINGERPRINT=9f49acdbf0de70883bf2ddb7c0619d4d; _gcl_au=1.1.1314647253.1777529155; _ga=GA1.1.599272329.1777529155; _clck=59a5kt%5E2%5Eg5n%5E0%5E2311; connect.sid=s%3A8KIIfE6kMqqHE9WeeADAUx6iCr30WAke.Dzv9%2Fn9cmtJfwvrTjJuABDDYF2y66XWDAVg8yFFJGlE; _clsk=12dlyi3%5E1777538210616%5E2%5E0%5Ek.clarity.ms%2Fcollect; amp_b31370=bh8LU0DbTPKLb3_lNobyz1...1jneotnhu.1jneotnhu.0.0.0; appier_utmz=%7B%22csr%22%3A%22google%22%2C%22timestamp%22%3A1777538621%7D; _atrk_siteuid=j3M67D3ZsYhAp91O; _atrk_ssid=SeschAQIMkGu7fxsu94x1o; appier_pv_counterPageView_9e66=0; appier_page_isView_PageView_9e66=fffd61df1116c931980f665310cec199897339ca29b0258cdbbb1a1ec3cd2c6b; appier_pv_counterViewTwoPages_1a5e=0; appier_page_isView_ViewTwoPages_1a5e=fffd61df1116c931980f665310cec199897339ca29b0258cdbbb1a1ec3cd2c6b; _atrk_sessidx=2; _ga_3JHT92YZJ8=GS2.1.s1777537663$o2$g1$t1777538621$j59$l0$h0"

HEADERS = {
    "accept": "*/*",
    "content-type": "application/json",
    "origin": "https://zigzag.kr",
    "referer": "https://zigzag.kr/",
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36",
    "cookie": MY_COOKIE,
}

QUERY = """
fragment PageInfoPart on UxPageInfo { page_name has_next end_cursor type ui_item_list { ...UxComponentPart } }
fragment UxComponentPart on UxComponent { __typename ... on UxGoodsCardItem { ...UxGoodsCardItemPart } }
fragment UxGoodsCardItemPart on UxGoodsCardItem { position type image_url webp_image_url video_url uuid product_url shop_name title price discount_rate free_shipping zpay column_count goods_id ranking log ubl { server_log } image_ratio aid has_coupon final_price max_price is_zpay_discount catalog_product_id browsing_type shop_product_no shop_id sales_status is_zonly is_brand similar_search display_review_count review_score is_saved_product badge_list { image_url dark_image_url small_image_url small_dark_image_url } brand_name_badge_list { image_url dark_image_url small_image_url small_dark_image_url } managed_category_list { id category_id value key depth } is_plp_v2 }
query GetPageInfoForWeb( $page_id: String $category_id: Int $sorting_id: Int $age_filter_id: Int $after: String $base_shop_id: String $goods_filter_option: GoodsFilterOptionInput $filter_id_list: [ID!] $ui_property: UiPropertyInput $external_page_id: String ) { page_info( page_id: $page_id category_id: $category_id sorting_id: $sorting_id age_filter_id: $age_filter_id after: $after base_shop_id: $base_shop_id goods_filter_option: $goods_filter_option filter_id_list: $filter_id_list ui_property: $ui_property external_page_id: $external_page_id ) { ...PageInfoPart } }
"""

URL = "https://api.zigzag.kr/api/2/graphql/GetPageInfoForWeb"


def fetch_page(after=None):
    payload = {
        "operationName": "GetPageInfoForWeb",
        "variables": {
            "page_id": "web_home",
            "external_page_id": None,
            "after": after,
        },
        "query": QUERY,
    }
    res = requests.post(URL, headers=HEADERS, json=payload)
    res.raise_for_status()
    return res.json()


def parse_items(ui_item_list):
    parsed = []
    for item in ui_item_list:
        if item.get("__typename") != "UxGoodsCardItem":
            continue
        category_list = item.get("managed_category_list") or []
        category = category_list[-1]["value"] if category_list else "N/A"
        parsed.append({
            "상품명": item.get("title"),
            "현재가": item.get("final_price"),
            "원래가": item.get("max_price"),
            "할인율": f"{item.get('discount_rate')}%" if item.get("discount_rate") else "N/A",
            "쇼핑몰": item.get("shop_name"),
            "평점": item.get("review_score"),
            "리뷰수": item.get("display_review_count"),
            "카테고리": category,
            "상품링크": item.get("product_url"),
            "이미지": item.get("image_url"),
        })
    return parsed


def crawl(max_pages=5):
    all_items = []
    after = None

    for page_num in range(1, max_pages + 1):
        print(f"📦 페이지 {page_num} 수집 중...")
        data = fetch_page(after=after)

        page_info = data.get("data", {}).get("page_info", {})
        ui_item_list = page_info.get("ui_item_list", [])
        items = parse_items(ui_item_list)
        all_items.extend(items)
        print(f"   → {len(items)}개 수집 (누적: {len(all_items)}개)")

        has_next = page_info.get("has_next", False)
        after = page_info.get("end_cursor")

        if not has_next or not after:
            print("✅ 마지막 페이지 도달!")
            break

        time.sleep(1)  # 서버 부하 방지

    df = pd.DataFrame(all_items)
    df.to_csv("zigzag_final_list.csv", index=False, encoding="utf-8-sig")
    print(f"\n🎉 완료! 총 {len(df)}개 → zigzag_final_list.csv 저장됨")
    return df


if __name__ == "__main__":
    df = crawl(max_pages=5)
    print(df.head())
