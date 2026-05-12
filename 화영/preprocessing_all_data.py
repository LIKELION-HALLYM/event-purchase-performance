import pandas as pd

# CSV 읽기
df = pd.read_csv("/Users/yanghwayeong/Desktop/system-design-interview-study/data/fashion_products.csv")

# 0으로 채울 컬럼
target_columns = [
    "discount_rate",
    "rating",
    "review_count"
]

for col in target_columns:
    if col in df.columns:
        # NaN -> 0
        df[col] = df[col].fillna(0)

        # 빈 문자열 -> 0
        df[col] = df[col].replace("", 0)

        # 숫자 변환
        df[col] = pd.to_numeric(
            df[col],
            errors="coerce"
        ).fillna(0)

        # int 변환
        df[col] = df[col].astype(int)

# 저장
output_file = "fashion_products_final.csv"

df.to_csv(
    output_file,
    index=False,
    encoding="utf-8-sig"
)

print("결측값 처리 완료")
print(f"저장 파일: {output_file}")
print(df.head())