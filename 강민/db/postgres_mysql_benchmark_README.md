# PostgreSQL / MySQL 조회 성능 측정

`fashion_products.csv`를 PostgreSQL과 MySQL에 같은 스키마로 적재한 뒤,
동일한 조회 쿼리를 반복 실행해 평균, p95, min, max 시간을 비교한다.

## 입력 데이터

- 기본 입력: `강민/data/raw/fashion_products.csv`
- 현재 확인된 행 수: 30,673건

## 실행 방법

Docker Desktop을 먼저 실행한 뒤 PowerShell에서 실행한다.

```powershell
cd C:\Users\KKM\event-purchase-performance
.\강민\db\benchmark_postgres_mysql.ps1 -Iterations 1000
```

다른 CSV를 사용할 경우:

```powershell
.\강민\db\benchmark_postgres_mysql.ps1 `
  -CsvPath "C:\Users\KKM\OneDrive\文档\카카오톡 받은 파일\fashion_products.csv" `
  -Iterations 1000
```

## 생성 결과

- `강민/data/reports/postgres_query_benchmark.csv`
- `강민/data/reports/mysql_query_benchmark.csv`
- `강민/data/reports/postgres_mysql_query_benchmark.csv`
- `강민/data/reports/postgres_mysql_performance_result.md`

## 조회 쿼리

- `brand_exact`: 브랜드 정확 일치 조회
- `category_exact`: 카테고리 정확 일치 조회
- `source_exact`: 쇼핑몰 출처 정확 일치 조회
- `price_range`: 가격 범위 조회
- `name_keyword_contains`: 상품명 키워드 포함 조회
- `price_order_page`: 가격 내림차순 페이지 조회

## 주의

Docker 리소스 제한, 캐시 상태, PC 부하에 따라 결과는 달라질 수 있다.
`name_keyword_contains`는 `%keyword%` 조건이므로 일반 B-tree 인덱스 효과가 작을 수 있다.
