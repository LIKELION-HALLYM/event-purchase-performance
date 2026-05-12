import pandas as pd

input_csv_file = "/Users/yanghwayeong/Desktop/system-design-interview-study/data/fashion_products_final.csv"

#중복 제거된 파일명
output_csv_file_name = "fashion_products_all_final.csv"

df = pd.read_csv(input_csv_file)

df = df.drop_duplicates(subset=["product_name"])

df = df.reset_index(drop=True)

# 저장

df.to_csv(output_csv_file_name, index=False, encoding="utf-8-sig")

print(f"최종 데이터 개수: {len(df)}")


