# 29CM CSV Cleaning Result

- Run date: 2026-05-09
- Raw rows: 10000
- Clean rows: 10000
- Removed invalid rows: 0
- Removed abnormal rows: 0
- Removed duplicates: 0
- Duplicate rule: same brand + same product_name
- Category rule: category/sub_category are kept as original 29CM labels
- Null rule: optional missing values are saved as `None`
- Encoding: UTF-8-sig
- Final limit: 10000
- Output CSV: `data/processed/29cm_products_clean.csv`
