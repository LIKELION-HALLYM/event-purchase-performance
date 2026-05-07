import pandas as pd
import numpy as np
import random
import uuid

# 실제 데이터 로드
real_df = pd.read_csv("zigzag_final_list.csv")

# ── 실제 데이터에서 분포 추출 ──────────────────────────
SHOPS      = real_df["쇼핑몰"].dropna().tolist()
CATEGORIES = real_df["카테고리"].dropna().tolist()
PRICES     = real_df["현재가"].dropna().tolist()
DISCOUNTS  = real_df["할인율"].dropna().str.replace("%", "").astype(int).tolist()
RATINGS    = real_df["평점"].dropna().tolist()
REVIEWS    = real_df["리뷰수"].dropna().tolist()

# ── 상품명 조합용 단어 ─────────────────────────────────
ADJECTIVES = [
    "스트라이프", "플로럴", "베이직", "루즈핏", "슬림핏", "오버사이즈",
    "크롭", "시스루", "레이스", "리넨", "데님", "체크", "니트", "캐주얼",
    "빈티지", "모던", "클래식", "시크", "큐트", "럭셔리", "스포티", "내추럴",
    "미니멀", "프릴", "버튼", "집업", "프린팅", "컬러블록", "자수", "패치"
]
ITEMS = [
    "블라우스", "티셔츠", "원피스", "팬츠", "스커트", "가디건", "자켓",
    "코트", "니트", "셔츠", "후드집업", "맨투맨", "슬랙스", "청바지",
    "레깅스", "민소매", "나시", "롱스커트", "미니스커트", "트렌치코트",
    "패딩", "점퍼", "조거팬츠", "와이드팬츠", "크롭티", "린넨셔츠"
]
SIZES  = ["XS", "S", "M", "L", "XL", "XXL", "FREE", "1size", "55", "66", "77"]
COLORS = ["블랙", "화이트", "베이지", "네이비", "그레이", "카키", "브라운",
          "민트", "라벤더", "핑크", "옐로우", "레드", "블루", "그린"]


def make_product_name():
    adj   = random.choice(ADJECTIVES)
    item  = random.choice(ITEMS)
    color = random.choice(COLORS)
    size  = random.choice(SIZES)
    return f"[MADE] {color} {adj} {item} ({size})"


def make_price():
    # 실제 가격 분포 기반: 로그정규분포 사용
    base = random.choice(PRICES)
    noise = np.random.normal(0, 3000)
    price = max(5000, int((base + noise) / 100) * 100)
    return price


def make_original_price(final_price, discount_rate):
    return int(final_price / (1 - discount_rate / 100) / 100) * 100


def make_review_count():
    base = random.choice([r for r in REVIEWS if str(r).isdigit()])
    noise = random.randint(-50, 200)
    return str(max(0, int(base) + noise))


def generate(n=100_000):
    print(f"🔧 {n:,}개 데이터 생성 중...")
    rows = []
    for i in range(n):
        discount = random.choice(DISCOUNTS)
        final    = make_price()
        original = make_original_price(final, discount)
        rating   = round(random.choice(RATINGS) + np.random.normal(0, 0.05), 1)
        rating   = min(5.0, max(1.0, rating))

        rows.append({
            "id":    i + 1,
            "상품명":  make_product_name(),
            "현재가":  final,
            "원래가":  original,
            "할인율":  f"{discount}%",
            "쇼핑몰":  random.choice(SHOPS),
            "평점":   rating,
            "리뷰수":  make_review_count(),
            "카테고리": random.choice(CATEGORIES),
            "상품링크": f"https://store.zigzag.kr/app/catalog/products/{random.randint(100000000, 999999999)}",
            "이미지":  f"https://cf.product-image.s.zigzag.kr/original/{uuid.uuid4().hex[:8]}.jpg",
        })

        if (i + 1) % 10000 == 0:
            print(f"   {i+1:,}개 완료...")

    df = pd.DataFrame(rows)
    out = "zigzag_100k.csv"
    df.to_csv(out, index=False, encoding="utf-8-sig")

    size_mb = df.memory_usage(deep=True).sum() / 1024 / 1024
    print(f"\n🎉 완료! {len(df):,}개 → {out}")
    print(f"📦 메모리 크기: {size_mb:.1f} MB")
    print(df.head(3).to_string())
    return df


if __name__ == "__main__":
    df = generate(100_000)
