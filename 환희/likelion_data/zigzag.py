import requests
import pandas as pd
import time

# ✅ 본인 쿠키 여기에 붙여넣기
MY_COOKIE = "_fbp=fb.1.1777529154295.15840950618656135; _fwb=98xRID7aVPbMWd70iw7mJ2.1777529154377; ZIGZAGUUID=68924dfc-5676-41f1-b0f5-667eed9ce04d.dBDYYUVgyC9SfoZ0%2BhI%2BChjb1MObe9xheo%2Bp6FG8WCM; ZIGZAG_FINGERPRINT=9f49acdbf0de70883bf2ddb7c0619d4d; _gcl_au=1.1.1314647253.1777529155; _ga=GA1.1.599272329.1777529155; connect.sid=s%3A8KIIfE6kMqqHE9WeeADAUx6iCr30WAke.Dzv9%2Fn9cmtJfwvrTjJuABDDYF2y66XWDAVg8yFFJGlE; _atrk_siteuid=j3M67D3ZsYhAp91O; appier_utmz=%7B%22csr%22%3A%22google%22%2C%22timestamp%22%3A1777538621%2C%22lcsr%22%3A%22google%22%7D; _clck=59a5kt%5E2%5Eg5o%5E0%5E2311; amp_b31370=bh8LU0DbTPKLb3_lNobyz1...1jnh3hpm4.1jnh3hpm4.0.0.0; _atrk_ssid=dExs2FcFadwxF-udFYj2kN; appier_pv_counterPageView_9e66=2; appier_page_isView_PageView_9e66=449cfbd7af938566a21b0a71b26d895cc63fd9ad5945a07219bc322b4ac3f7e8; appier_pv_counterViewTwoPages_1a5e=1; appier_page_isView_ViewTwoPages_1a5e=449cfbd7af938566a21b0a71b26d895cc63fd9ad5945a07219bc322b4ac3f7e8; _atrk_sessidx=3; _ga_3JHT92YZJ8=GS2.1.s1777616870$o4$g1$t1777616873$j57$l0$h0; _clsk=1yumypk%5E1777616874197%5E3%5E0%5Ek.clarity.ms%2Fcollect"

HEADERS = {
    "accept": "*/*",
    "content-type": "application/json",
    "origin": "https://zigzag.kr",
    "referer": "https://zigzag.kr/",
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36",
    "cookie": MY_COOKIE,
}

QUERY_HOME = """
fragment PageInfoPart on UxPageInfo { page_name has_next end_cursor type ui_item_list { ...UxComponentPart } }
fragment UxComponentPart on UxComponent { __typename ... on UxGoodsCardItem { ...UxGoodsCardItemPart } }
fragment UxGoodsCardItemPart on UxGoodsCardItem { position type image_url webp_image_url video_url uuid product_url shop_name title price discount_rate free_shipping zpay column_count goods_id ranking log ubl { server_log } image_ratio aid has_coupon final_price max_price is_zpay_discount catalog_product_id browsing_type shop_product_no shop_id sales_status is_zonly is_brand similar_search display_review_count review_score is_saved_product badge_list { image_url dark_image_url small_image_url small_dark_image_url } brand_name_badge_list { image_url dark_image_url small_image_url small_dark_image_url } managed_category_list { id category_id value key depth } is_plp_v2 }
query GetPageInfoForWeb( $page_id: String $category_id: Int $sorting_id: Int $age_filter_id: Int $after: String $base_shop_id: String $goods_filter_option: GoodsFilterOptionInput $filter_id_list: [ID!] $ui_property: UiPropertyInput $external_page_id: String ) { page_info( page_id: $page_id category_id: $category_id sorting_id: $sorting_id age_filter_id: $age_filter_id after: $after base_shop_id: $base_shop_id goods_filter_option: $goods_filter_option filter_id_list: $filter_id_list ui_property: $ui_property external_page_id: $external_page_id ) { ...PageInfoPart } }
"""

QUERY_SEARCH = """
fragment SearchResultPart on UxPageInfo { page_name has_next end_cursor type ui_item_list { ...UxSearchComponentPart } }
fragment UxSearchComponentPart on UxComponent { __typename ... on UxGoodsCardItem { ...UxSearchGoodsCardItemPart } }
fragment UxSearchGoodsCardItemPart on UxGoodsCardItem { position type image_url webp_image_url video_url uuid product_url shop_name title price discount_rate free_shipping zpay column_count goods_id ranking log ubl { server_log } image_ratio aid has_coupon final_price max_price is_zpay_discount catalog_product_id browsing_type shop_product_no shop_id sellable_status is_zonly is_brand similar_search display_review_count review_score is_saved_product thumbnail_emblem_badge_list { image_url dark_image_url small_image_url small_dark_image_url } thumbnail_nudge_badge_list { image_url dark_image_url small_image_url small_dark_image_url } managed_category_list { id category_id value key depth } is_plp_v2 }
query GetSearchResult( $page_id: String $category_id: Int $sorting_id: Int $age_filter_id: Int $after: String $base_shop_id: String $goods_filter_option: GoodsFilterOptionInput $filter_id_list: [ID!] $ui_property: UiPropertyInput $external_page_id: String ) { page_info( page_id: $page_id category_id: $category_id sorting_id: $sorting_id age_filter_id: $age_filter_id after: $after base_shop_id: $base_shop_id goods_filter_option: $goods_filter_option filter_id_list: $filter_id_list ui_property: $ui_property external_page_id: $external_page_id ) { ...SearchResultPart } }
"""

URL_HOME   = "https://api.zigzag.kr/api/2/graphql/GetPageInfoForWeb"
URL_SEARCH = "https://api.zigzag.kr/api/2/graphql/GetSearchResult"


def fetch_home():
    """홈 피드 조회 (카테고리 ID 탐색용)"""
    payload = {
        "operationName": "GetPageInfoForWeb",
        "variables": {"page_id": "web_home", "external_page_id": None, "after": None},
        "query": QUERY_HOME,
    }
    res = requests.post(URL_HOME, headers=HEADERS, json=payload)
    res.raise_for_status()
    return res.json()


def fetch_page(after=None, category_id=None, sorting_id=None):
    """카테고리 상품 목록 조회 (GetSearchResult)"""
    variables = {
        "page_id": "web_plp",
        "external_page_id": None,
        "after": after,
    }
    if category_id is not None:
        variables["category_id"] = category_id
    if sorting_id is not None:
        variables["sorting_id"] = sorting_id
    payload = {
        "operationName": "GetSearchResult",
        "variables": variables,
        "query": QUERY_SEARCH,
    }
    res = requests.post(URL_SEARCH, headers=HEADERS, json=payload)
    res.raise_for_status()
    return res.json()


def discover_category_ids():
    """홈 피드에서 리프(leaf) category_id 목록만 수집 (부모 카테고리 제외)"""
    print("🔍 카테고리 ID 탐색 중...")
    data = fetch_home()
    page_info = data.get("data", {}).get("page_info", {})
    ui_item_list = page_info.get("ui_item_list", [])

    leaf_ids = {}   # category_id → 카테고리명 (가장 하위 카테고리만)
    parent_ids = set()

    for item in ui_item_list:
        if item.get("__typename") != "UxGoodsCardItem":
            continue
        cat_list = item.get("managed_category_list") or []
        # 부모 ID 수집 (마지막 제외한 모든 것)
        for cat in cat_list[:-1]:
            cid = cat.get("category_id")
            if cid:
                parent_ids.add(cid)
        # 리프 ID 수집
        if cat_list:
            leaf = cat_list[-1]
            cid = leaf.get("category_id")
            val = leaf.get("value")
            if cid and val:
                leaf_ids[cid] = val

    # 부모 카테고리 제거
    for pid in parent_ids:
        leaf_ids.pop(pid, None)

    print(f"   → {len(leaf_ids)}개 리프 카테고리 발견: {list(leaf_ids.values())}")
    return list(leaf_ids.keys())


def parse_items(ui_item_list):
    parsed = []
    for item in ui_item_list:
        if item.get("__typename") != "UxGoodsCardItem":
            continue
        # 품절 상품 제외 (GetSearchResult는 sellable_status 사용)
        if item.get("sellable_status") not in (None, "ON_SALE"):
            continue
        category_list = item.get("managed_category_list") or []
        category = category_list[-1]["value"] if category_list else None
        subcategory = category_list[-2]["value"] if len(category_list) >= 2 else None
        discount_rate = item.get("discount_rate")
        parsed.append({
            "product_name": item.get("title"),
            "brand":        item.get("shop_name"),
            "category":     category,
            "subcategory":  subcategory,
            "price":        item.get("final_price"),
            "discount_rate": discount_rate if discount_rate is not None else None,
            "rating":       item.get("review_score"),
            "review_count": item.get("display_review_count"),
            "source":       "zigzag",
            "source_url":   item.get("product_url"),
            "image_url":    item.get("image_url"),
        })
    return parsed


SORTING_IDS = [1, 2, 3, 4, 5, 6]


def crawl_combination(category_id, sorting_id, all_items, seen, target, max_pages=200):
    """카테고리+정렬 조합으로 상품 수집. target 달성 시 True 반환."""
    after = None
    for page_num in range(1, max_pages + 1):
        data = fetch_page(after=after, category_id=category_id, sorting_id=sorting_id)
        page_info = data.get("data", {}).get("page_info", {})
        ui_item_list = page_info.get("ui_item_list", [])
        items = parse_items(ui_item_list)

        added = 0
        for item in items:
            key = (item["brand"], item["product_name"])
            if key in seen:
                continue
            seen.add(key)
            all_items.append(item)
            added += 1

        if added > 0:
            print(f"   페이지 {page_num}: {added}개 추가 (누적: {len(all_items)}개)")

        if len(all_items) >= target:
            return True

        has_next = page_info.get("has_next", False)
        after = page_info.get("end_cursor")
        if not has_next or not after:
            break

        time.sleep(0.5)

    return False


def crawl(target=10000):
    category_ids = discover_category_ids()

    all_items = []
    seen = set()

    for cat_id in category_ids:
        for sort_id in SORTING_IDS:
            print(f"\n📂 카테고리 {cat_id} / 정렬 {sort_id} 수집 중... (현재 {len(all_items)}개)")
            done = crawl_combination(cat_id, sort_id, all_items, seen, target)
            if done:
                print(f"✅ 목표 {target}개 달성!")
                break
        else:
            continue
        break

    if len(all_items) < target:
        print(f"⚠️  조합 소진 후 총 {len(all_items)}개 수집됨 (목표 미달)")

    df = pd.DataFrame(all_items[:target])
    df = df.where(pd.notnull(df), None)
    df.to_csv("zigzag_final_list.csv", index=False, encoding="utf-8-sig")
    print(f"\n🎉 완료! 총 {len(df)}개 → zigzag_final_list.csv 저장됨")
    return df


if __name__ == "__main__":
    df = crawl(target=10000)
    print(df.head())
