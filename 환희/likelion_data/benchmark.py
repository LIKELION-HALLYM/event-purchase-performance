import time
import pandas as pd
import pymysql
import psycopg2
import pymongo

CSV_FILE = "zigzag_100k.csv"

# ── DB 설정 ──────────────────────────────────────────
MYSQL_CONFIG = dict(host="127.0.0.1", user="root", password="", database="zigzag_bench", charset="utf8mb4")
PG_CONFIG    = dict(host="127.0.0.1", user="gimhwanhui", password="", dbname="zigzag_bench")
MONGO_URI    = "mongodb://localhost:27017/"
COLLECTION   = "products"


# ── 시간 측정 헬퍼 ────────────────────────────────────
def measure(fn):
    start = time.perf_counter()
    result = fn()
    elapsed = time.perf_counter() - start
    return elapsed, result


# ══════════════════════════════════════════════════════
# MySQL
# ══════════════════════════════════════════════════════
def setup_mysql(df):
    conn = pymysql.connect(**{**MYSQL_CONFIG, "database": ""})
    cur  = conn.cursor()
    cur.execute("CREATE DATABASE IF NOT EXISTS zigzag_bench DEFAULT CHARACTER SET utf8mb4")
    conn.select_db("zigzag_bench")
    cur.execute("DROP TABLE IF EXISTS products")
    cur.execute("""
        CREATE TABLE products (
            id         INT PRIMARY KEY,
            상품명     VARCHAR(300),
            현재가     INT,
            원래가     INT,
            할인율     VARCHAR(10),
            쇼핑몰     VARCHAR(100),
            평점       FLOAT,
            리뷰수     VARCHAR(20),
            카테고리   VARCHAR(100),
            상품링크   VARCHAR(300),
            이미지     VARCHAR(300)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)
    conn.commit()

    rows = [tuple(r) for r in df.itertuples(index=False)]
    cur.executemany(
        "INSERT INTO products VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", rows
    )
    conn.commit()
    print("  인덱스 생성 중...")
    cur.execute("CREATE INDEX idx_category ON products(카테고리)")
    cur.execute("CREATE INDEX idx_price    ON products(현재가)")
    cur.execute("CREATE INDEX idx_rating   ON products(평점)")
    conn.commit()
    cur.close()
    conn.close()
    print("  MySQL 셋업 완료")


def bench_mysql():
    conn = pymysql.connect(**MYSQL_CONFIG)
    cur  = conn.cursor()

    # 1) 전체 조회
    t1, _ = measure(lambda: cur.execute("SELECT * FROM products"))

    # 2) 카테고리 필터
    t2, _ = measure(lambda: cur.execute(
        "SELECT * FROM products WHERE 카테고리 = '블라우스'"))

    # 3) 가격 범위
    t3, _ = measure(lambda: cur.execute(
        "SELECT * FROM products WHERE 현재가 BETWEEN 20000 AND 50000"))

    # 4) 평점 정렬 TOP 100
    t4, _ = measure(lambda: cur.execute(
        "SELECT * FROM products ORDER BY 평점 DESC LIMIT 100"))

    # 5) 상품명 LIKE 검색
    t5, _ = measure(lambda: cur.execute(
        "SELECT * FROM products WHERE 상품명 LIKE '%블랙%'"))

    cur.close()
    conn.close()
    return t1, t2, t3, t4, t5


# ══════════════════════════════════════════════════════
# PostgreSQL
# ══════════════════════════════════════════════════════
def setup_postgres(df):
    conn = psycopg2.connect(**{**PG_CONFIG, "dbname": "postgres"})
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute("DROP DATABASE IF EXISTS zigzag_bench")
    cur.execute("CREATE DATABASE zigzag_bench")
    cur.close()
    conn.close()

    conn = psycopg2.connect(**PG_CONFIG)
    cur  = conn.cursor()
    cur.execute("""
        CREATE TABLE products (
            id       INT PRIMARY KEY,
            상품명   VARCHAR(300),
            현재가   INT,
            원래가   INT,
            할인율   VARCHAR(10),
            쇼핑몰   VARCHAR(100),
            평점     FLOAT,
            리뷰수   VARCHAR(20),
            카테고리 VARCHAR(100),
            상품링크 VARCHAR(300),
            이미지   VARCHAR(300)
        )
    """)
    conn.commit()

    rows = [tuple(r) for r in df.itertuples(index=False)]
    cur.executemany(
        "INSERT INTO products VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", rows
    )
    conn.commit()
    print("  인덱스 생성 중...")
    cur.execute('CREATE INDEX idx_category ON products(카테고리)')
    cur.execute('CREATE INDEX idx_price    ON products(현재가)')
    cur.execute('CREATE INDEX idx_rating   ON products(평점)')
    conn.commit()
    cur.close()
    conn.close()
    print("  PostgreSQL 셋업 완료")


def bench_postgres():
    conn = psycopg2.connect(**PG_CONFIG)
    cur  = conn.cursor()

    t1, _ = measure(lambda: cur.execute("SELECT * FROM products"))
    t2, _ = measure(lambda: cur.execute(
        "SELECT * FROM products WHERE 카테고리 = '블라우스'"))
    t3, _ = measure(lambda: cur.execute(
        "SELECT * FROM products WHERE 현재가 BETWEEN 20000 AND 50000"))
    t4, _ = measure(lambda: cur.execute(
        "SELECT * FROM products ORDER BY 평점 DESC LIMIT 100"))
    t5, _ = measure(lambda: cur.execute(
        "SELECT * FROM products WHERE 상품명 LIKE '%블랙%'"))

    cur.close()
    conn.close()
    return t1, t2, t3, t4, t5


# ══════════════════════════════════════════════════════
# MongoDB
# ══════════════════════════════════════════════════════
def setup_mongo(df):
    client = pymongo.MongoClient(MONGO_URI)
    db     = client["zigzag_bench"]
    col    = db[COLLECTION]
    col.drop()

    records = df.to_dict("records")
    col.insert_many(records)
    print("  인덱스 생성 중...")
    col.create_index("카테고리")
    col.create_index("현재가")
    col.create_index("평점")
    client.close()
    print("  MongoDB 셋업 완료")


def bench_mongo():
    client = pymongo.MongoClient(MONGO_URI)
    col    = client["zigzag_bench"][COLLECTION]

    t1, _ = measure(lambda: list(col.find()))
    t2, _ = measure(lambda: list(col.find({"카테고리": "블라우스"})))
    t3, _ = measure(lambda: list(col.find({"현재가": {"$gte": 20000, "$lte": 50000}})))
    t4, _ = measure(lambda: list(col.find().sort("평점", -1).limit(100)))
    t5, _ = measure(lambda: list(col.find({"상품명": {"$regex": "블랙"}})))

    client.close()
    return t1, t2, t3, t4, t5


# ══════════════════════════════════════════════════════
# 메인
# ══════════════════════════════════════════════════════
REPEAT = 5  # 측정 횟수 (웜업 1회 제외)


def run_bench(name, bench_fn):
    print(f"  웜업 1회...")
    bench_fn()  # 웜업 - 결과 제외
    times = []
    for i in range(1, REPEAT + 1):
        t = bench_fn()
        times.append(t)
        print(f"  {i}회: {[f'{x:.4f}s' for x in t]}")
    # 각 테스트별로 평균/최소/최대 계산
    import numpy as np
    arr = np.array(times)  # shape: (REPEAT, 5)
    return {
        "avg": arr.mean(axis=0),
        "min": arr.min(axis=0),
        "max": arr.max(axis=0),
    }


def main():
    print("📂 데이터 로딩...")
    df = pd.read_csv(CSV_FILE)
    df["현재가"] = df["현재가"].fillna(0).astype(int)
    df["원래가"] = df["원래가"].fillna(0).astype(int)
    df["평점"]   = df["평점"].fillna(0).astype(float)
    df = df.fillna("")
    print(f"   {len(df):,}개 로드 완료\n")

    TESTS = ["전체 조회", "카테고리 필터", "가격 범위 조회", "평점 TOP100", "상품명 검색"]
    stats = {}

    # MySQL
    print("=" * 40)
    print("🐬 MySQL 데이터 삽입 중 (10만건)...")
    setup_mysql(df)
    print(f"🐬 MySQL 벤치마크 {REPEAT}회 반복...")
    stats["MySQL"] = run_bench("MySQL", bench_mysql)

    # PostgreSQL
    print("\n" + "=" * 40)
    print("🐘 PostgreSQL 데이터 삽입 중 (10만건)...")
    setup_postgres(df)
    print(f"🐘 PostgreSQL 벤치마크 {REPEAT}회 반복...")
    stats["PostgreSQL"] = run_bench("PostgreSQL", bench_postgres)

    # MongoDB
    print("\n" + "=" * 40)
    print("🍃 MongoDB 데이터 삽입 중 (10만건)...")
    setup_mongo(df)
    print(f"🍃 MongoDB 벤치마크 {REPEAT}회 반복...")
    stats["MongoDB"] = run_bench("MongoDB", bench_mongo)

    # 결과 출력
    print("\n" + "=" * 70)
    print(f"📊 벤치마크 결과 (웜업 1회 제외, {REPEAT}회 평균, 단위: 초)")
    print("=" * 70)

    for stat_type, label in [("avg", "평균"), ("min", "최소"), ("max", "최대")]:
        data = {db: stats[db][stat_type] for db in stats}
        df_out = pd.DataFrame(data, index=TESTS)
        print(f"\n[ {label} ]")
        print(df_out.applymap(lambda x: f"{x:.4f}s").to_string())

    # CSV 저장
    rows = []
    for test_idx, test in enumerate(TESTS):
        for db in stats:
            rows.append({
                "테스트": test,
                "DB": db,
                "평균(s)": round(stats[db]["avg"][test_idx], 4),
                "최소(s)": round(stats[db]["min"][test_idx], 4),
                "최대(s)": round(stats[db]["max"][test_idx], 4),
            })
    result_df = pd.DataFrame(rows)
    result_df.to_csv("benchmark_result.csv", index=False, encoding="utf-8-sig")
    print("\n✅ 결과 저장: benchmark_result.csv")

    # 승자 판정 (평균 기준)
    print("\n🏆 테스트별 최고 성능 DB (평균 기준):")
    for test_idx, test in enumerate(TESTS):
        scores = {db: stats[db]["avg"][test_idx] for db in stats}
        winner = min(scores, key=scores.get)
        print(f"  {test}: {winner} ({scores[winner]:.4f}s)")


if __name__ == "__main__":
    main()
