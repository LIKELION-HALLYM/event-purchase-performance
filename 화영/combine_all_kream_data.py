import glob
import pandas as pd

# 현재 폴더의 모든 *_processed.csv 찾기
files = glob.glob("*_processed.csv")

print("찾은 CSV 파일:")
for file in files:
    print(file)

dfs = []

# CSV 읽기
for file in files:
    try:
        df = pd.read_csv(file)
        dfs.append(df)

        print(f"읽기 완료: {file} / 데이터 개수: {len(df)}")

    except Exception as e:
        print(f"읽기 실패: {file}")
        print(e)

# 합칠 데이터가 없는 경우
if not dfs:
    print("합칠 CSV 파일이 없습니다.")
    exit()

# 전체 합치기
merged_df = pd.concat(dfs, ignore_index=True)

# source_url 기준 중복 제거
if "source_url" in merged_df.columns:
    merged_df = merged_df.drop_duplicates(subset=["source_url"])

# 저장
output_file = "kream_products.csv"

merged_df.to_csv(
    output_file,
    index=False,
    encoding="utf-8-sig"
)

print("\n합치기 완료")
print(f"총 데이터 개수: {len(merged_df)}")
print(f"저장 파일: {output_file}")