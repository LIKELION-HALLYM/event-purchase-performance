import pandas as pd

# CSV 읽기
df = pd.read_csv("/Users/yanghwayeong/Desktop/system-design-interview-study/화영/kream_청바지.csv")

# discount_rate → rating 으로 이동
# 비어있는 값은 0으로 채우기
df["rating"] = df["discount_rate"].fillna(0)

# 문자열 공백 처리
df["rating"] = df["rating"].replace("", 0)

# 숫자로 변환
df["rating"] = pd.to_numeric(df["rating"], errors="coerce").fillna(0)

# int 변환
df["rating"] = df["rating"].astype(int)

# 기존 discount_rate 컬럼 삭제
df = df.drop(columns=["discount_rate"])

# category 컬럼 삭제
df = df.drop(columns=["category"])

# 새로운 CSV 저장
df.to_csv(
    "kream_청바지_processed.csv",
    index=False,
    encoding="utf-8-sig"
)

print("컬럼 수정 완료")
print(df.head())