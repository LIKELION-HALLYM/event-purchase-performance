param(
    [string]$CsvPath = "",
    [int]$Iterations = 1000,
    [switch]$KeepContainers
)

$ErrorActionPreference = "Stop"

$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
if ([string]::IsNullOrWhiteSpace($CsvPath)) {
    $CsvPath = Join-Path $Root "data\raw\fashion_products.csv"
}
$CsvPath = (Resolve-Path -LiteralPath $CsvPath).Path

$ReportDir = Join-Path $Root "data\reports"
$DbDir = Join-Path $Root "data\db"
New-Item -ItemType Directory -Force -Path $ReportDir | Out-Null
New-Item -ItemType Directory -Force -Path $DbDir | Out-Null

$PostgresContainer = "kkm-postgres-benchmark"
$MySqlContainer = "kkm-mysql-benchmark"
$PostgresPassword = "benchmark_pw"
$MySqlPassword = "benchmark_pw"
$Database = "fashion_benchmark"

$PostgresCsv = Join-Path $ReportDir "postgres_query_benchmark.csv"
$MySqlCsv = Join-Path $ReportDir "mysql_query_benchmark.csv"
$SummaryCsv = Join-Path $ReportDir "postgres_mysql_query_benchmark.csv"
$SummaryMd = Join-Path $ReportDir "postgres_mysql_performance_result.md"
$Script:ImportedRowCount = ""

function Invoke-Docker {
    param([string[]]$DockerArgs)
    & docker @DockerArgs
    if ($LASTEXITCODE -ne 0) {
        throw "docker $($DockerArgs -join ' ') failed"
    }
}

function Remove-ContainerIfExists {
    param([string]$Name)
    $exists = docker ps -a --format "{{.Names}}" | Where-Object { $_ -eq $Name }
    if ($exists) {
        docker rm -f $Name | Out-Null
    }
}

function Wait-Postgres {
    for ($i = 0; $i -lt 60; $i++) {
        docker exec $PostgresContainer pg_isready -U postgres -d $Database | Out-Null
        if ($LASTEXITCODE -eq 0) { return }
        Start-Sleep -Seconds 2
    }
    throw "PostgreSQL container did not become ready."
}

function Wait-MySql {
    for ($i = 0; $i -lt 90; $i++) {
        docker exec $MySqlContainer mysqladmin ping -uroot "-p$MySqlPassword" --silent | Out-Null
        if ($LASTEXITCODE -eq 0) { return }
        Start-Sleep -Seconds 2
    }
    throw "MySQL container did not become ready."
}

function Write-PostgresSql {
    param([string]$Path)
    @"
\set iterations $Iterations
\timing off
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS staging_products;
CREATE TABLE staging_products (
    product_name TEXT,
    brand TEXT,
    category TEXT,
    price TEXT,
    discount_rate TEXT,
    rating TEXT,
    review_count TEXT,
    image_url TEXT,
    source TEXT,
    source_url TEXT,
    sub_category TEXT
);
\copy staging_products FROM '/tmp/fashion_products.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8');
CREATE TABLE products (
    id BIGSERIAL PRIMARY KEY,
    product_name TEXT NOT NULL,
    brand TEXT NOT NULL,
    category TEXT NOT NULL,
    sub_category TEXT,
    price INTEGER NOT NULL,
    discount_rate DOUBLE PRECISION,
    rating DOUBLE PRECISION,
    review_count INTEGER,
    image_url TEXT,
    source TEXT NOT NULL,
    source_url TEXT NOT NULL
);
INSERT INTO products (
    product_name, brand, category, sub_category, price, discount_rate,
    rating, review_count, image_url, source, source_url
)
SELECT
    trim(product_name),
    trim(brand),
    trim(category),
    NULLIF(trim(sub_category), ''),
    NULLIF(regexp_replace(price, '[^0-9]', '', 'g'), '')::INTEGER,
    NULLIF(regexp_replace(discount_rate, '[^0-9.]', '', 'g'), '')::DOUBLE PRECISION,
    NULLIF(regexp_replace(rating, '[^0-9.]', '', 'g'), '')::DOUBLE PRECISION,
    NULLIF(regexp_replace(review_count, '[^0-9.]', '', 'g'), '')::DOUBLE PRECISION::INTEGER,
    NULLIF(trim(image_url), ''),
    trim(source),
    trim(source_url)
FROM staging_products
WHERE NULLIF(trim(product_name), '') IS NOT NULL
  AND NULLIF(trim(brand), '') IS NOT NULL
  AND NULLIF(trim(category), '') IS NOT NULL
  AND NULLIF(regexp_replace(price, '[^0-9]', '', 'g'), '') IS NOT NULL
  AND NULLIF(trim(source), '') IS NOT NULL
  AND NULLIF(trim(source_url), '') IS NOT NULL;
CREATE INDEX idx_products_brand ON products (brand);
CREATE INDEX idx_products_category ON products (category);
CREATE INDEX idx_products_source ON products (source);
CREATE INDEX idx_products_price ON products (price);
CREATE INDEX idx_products_name ON products (product_name);
ANALYZE products;
DROP TABLE IF EXISTS benchmark_timings;
CREATE TABLE benchmark_timings (
    dbms TEXT,
    query_name TEXT,
    duration_ms DOUBLE PRECISION
);
DO `$`$
DECLARE
    i INTEGER;
    start_time TIMESTAMP;
    elapsed DOUBLE PRECISION;
    brand_value TEXT;
    category_value TEXT;
    source_value TEXT;
    token_value TEXT;
    low_price INTEGER;
    high_price INTEGER;
    page_offset INTEGER;
    row_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO row_count FROM products;

    FOR i IN 1..$Iterations LOOP
        SELECT brand INTO brand_value FROM products OFFSET floor(random() * row_count) LIMIT 1;
        start_time := clock_timestamp();
        PERFORM COUNT(*) FROM products WHERE brand = brand_value;
        elapsed := EXTRACT(EPOCH FROM (clock_timestamp() - start_time)) * 1000;
        INSERT INTO benchmark_timings VALUES ('postgresql', 'brand_exact', elapsed);

        SELECT category INTO category_value FROM products OFFSET floor(random() * row_count) LIMIT 1;
        start_time := clock_timestamp();
        PERFORM COUNT(*) FROM products WHERE category = category_value;
        elapsed := EXTRACT(EPOCH FROM (clock_timestamp() - start_time)) * 1000;
        INSERT INTO benchmark_timings VALUES ('postgresql', 'category_exact', elapsed);

        SELECT source INTO source_value FROM products OFFSET floor(random() * row_count) LIMIT 1;
        start_time := clock_timestamp();
        PERFORM COUNT(*) FROM products WHERE source = source_value;
        elapsed := EXTRACT(EPOCH FROM (clock_timestamp() - start_time)) * 1000;
        INSERT INTO benchmark_timings VALUES ('postgresql', 'source_exact', elapsed);

        SELECT price INTO low_price FROM products OFFSET floor(random() * row_count) LIMIT 1;
        SELECT price INTO high_price FROM products OFFSET floor(random() * row_count) LIMIT 1;
        IF low_price > high_price THEN
            low_price := low_price + high_price;
            high_price := low_price - high_price;
            low_price := low_price - high_price;
        END IF;
        start_time := clock_timestamp();
        PERFORM COUNT(*) FROM products WHERE price BETWEEN low_price AND high_price;
        elapsed := EXTRACT(EPOCH FROM (clock_timestamp() - start_time)) * 1000;
        INSERT INTO benchmark_timings VALUES ('postgresql', 'price_range', elapsed);

        SELECT split_part(product_name, ' ', 1) INTO token_value FROM products OFFSET floor(random() * row_count) LIMIT 1;
        start_time := clock_timestamp();
        PERFORM id FROM products WHERE product_name LIKE '%' || token_value || '%' LIMIT 50;
        elapsed := EXTRACT(EPOCH FROM (clock_timestamp() - start_time)) * 1000;
        INSERT INTO benchmark_timings VALUES ('postgresql', 'name_keyword_contains', elapsed);

        page_offset := floor(random() * GREATEST(row_count - 50, 1));
        start_time := clock_timestamp();
        PERFORM id FROM products ORDER BY price DESC LIMIT 50 OFFSET page_offset;
        elapsed := EXTRACT(EPOCH FROM (clock_timestamp() - start_time)) * 1000;
        INSERT INTO benchmark_timings VALUES ('postgresql', 'price_order_page', elapsed);
    END LOOP;
END
`$`$;
COPY (
    SELECT
        dbms,
        query_name,
        COUNT(*) AS iterations,
        ROUND(AVG(duration_ms)::numeric, 4) AS avg_ms,
        ROUND(percentile_cont(0.95) WITHIN GROUP (ORDER BY duration_ms)::numeric, 4) AS p95_ms,
        ROUND(MIN(duration_ms)::numeric, 4) AS min_ms,
        ROUND(MAX(duration_ms)::numeric, 4) AS max_ms
    FROM benchmark_timings
    GROUP BY dbms, query_name
    ORDER BY query_name
) TO '/tmp/postgres_query_benchmark.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8');
"@ | Set-Content -LiteralPath $Path -Encoding UTF8
}

function Write-MySqlSql {
    param([string]$Path)
    @"
SET GLOBAL local_infile = 1;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS staging_products;
CREATE TABLE staging_products (
    product_name TEXT,
    brand TEXT,
    category TEXT,
    price TEXT,
    discount_rate TEXT,
    rating TEXT,
    review_count TEXT,
    image_url TEXT,
    source TEXT,
    source_url TEXT,
    sub_category TEXT
) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
LOAD DATA LOCAL INFILE '/tmp/fashion_products.csv'
INTO TABLE staging_products
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ',' ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(product_name, brand, category, price, discount_rate, rating, review_count, image_url, source, source_url, sub_category);
CREATE TABLE products (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    product_name TEXT NOT NULL,
    brand VARCHAR(255) NOT NULL,
    category VARCHAR(255) NOT NULL,
    sub_category VARCHAR(255),
    price INT NOT NULL,
    discount_rate DOUBLE,
    rating DOUBLE,
    review_count INT,
    image_url TEXT,
    source VARCHAR(100) NOT NULL,
    source_url TEXT NOT NULL,
    INDEX idx_products_brand (brand),
    INDEX idx_products_category (category),
    INDEX idx_products_source (source),
    INDEX idx_products_price (price),
    INDEX idx_products_name (product_name(255))
) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
INSERT INTO products (
    product_name, brand, category, sub_category, price, discount_rate,
    rating, review_count, image_url, source, source_url
)
SELECT
    TRIM(product_name),
    TRIM(brand),
    TRIM(category),
    NULLIF(TRIM(sub_category), ''),
    CAST(NULLIF(REGEXP_REPLACE(price, '[^0-9]', ''), '') AS UNSIGNED),
    CAST(NULLIF(REGEXP_REPLACE(discount_rate, '[^0-9.]', ''), '') AS DOUBLE),
    CAST(NULLIF(REGEXP_REPLACE(rating, '[^0-9.]', ''), '') AS DOUBLE),
    CAST(CAST(NULLIF(REGEXP_REPLACE(review_count, '[^0-9.]', ''), '') AS DOUBLE) AS UNSIGNED),
    NULLIF(TRIM(image_url), ''),
    TRIM(source),
    TRIM(source_url)
FROM staging_products
WHERE NULLIF(TRIM(product_name), '') IS NOT NULL
  AND NULLIF(TRIM(brand), '') IS NOT NULL
  AND NULLIF(TRIM(category), '') IS NOT NULL
  AND NULLIF(REGEXP_REPLACE(price, '[^0-9]', ''), '') IS NOT NULL
  AND NULLIF(TRIM(source), '') IS NOT NULL
  AND NULLIF(TRIM(source_url), '') IS NOT NULL;
ANALYZE TABLE products;
DROP TABLE IF EXISTS benchmark_timings;
CREATE TABLE benchmark_timings (
    dbms VARCHAR(30),
    query_name VARCHAR(100),
    duration_ms DOUBLE
);
DROP PROCEDURE IF EXISTS run_benchmark;
DELIMITER //
CREATE PROCEDURE run_benchmark(IN p_iterations INT)
BEGIN
    DECLARE i INT DEFAULT 0;
    DECLARE row_count INT DEFAULT 0;
    DECLARE brand_value VARCHAR(255);
    DECLARE category_value VARCHAR(255);
    DECLARE source_value VARCHAR(100);
    DECLARE token_value VARCHAR(255);
    DECLARE low_price INT;
    DECLARE high_price INT;
    DECLARE tmp_price INT;
    DECLARE page_offset INT;
    DECLARE rand_offset INT;
    DECLARE start_time DATETIME(6);
    DECLARE dummy_count BIGINT;

    SELECT COUNT(*) INTO row_count FROM products;

    WHILE i < p_iterations DO
        SET rand_offset = FLOOR(RAND() * row_count);
        SELECT brand INTO brand_value FROM products LIMIT rand_offset, 1;
        SET start_time = NOW(6);
        SELECT COUNT(*) INTO dummy_count FROM products WHERE brand = brand_value;
        INSERT INTO benchmark_timings VALUES ('mysql', 'brand_exact', TIMESTAMPDIFF(MICROSECOND, start_time, NOW(6)) / 1000);

        SET rand_offset = FLOOR(RAND() * row_count);
        SELECT category INTO category_value FROM products LIMIT rand_offset, 1;
        SET start_time = NOW(6);
        SELECT COUNT(*) INTO dummy_count FROM products WHERE category = category_value;
        INSERT INTO benchmark_timings VALUES ('mysql', 'category_exact', TIMESTAMPDIFF(MICROSECOND, start_time, NOW(6)) / 1000);

        SET rand_offset = FLOOR(RAND() * row_count);
        SELECT source INTO source_value FROM products LIMIT rand_offset, 1;
        SET start_time = NOW(6);
        SELECT COUNT(*) INTO dummy_count FROM products WHERE source = source_value;
        INSERT INTO benchmark_timings VALUES ('mysql', 'source_exact', TIMESTAMPDIFF(MICROSECOND, start_time, NOW(6)) / 1000);

        SET rand_offset = FLOOR(RAND() * row_count);
        SELECT price INTO low_price FROM products LIMIT rand_offset, 1;
        SET rand_offset = FLOOR(RAND() * row_count);
        SELECT price INTO high_price FROM products LIMIT rand_offset, 1;
        IF low_price > high_price THEN
            SET tmp_price = low_price;
            SET low_price = high_price;
            SET high_price = tmp_price;
        END IF;
        SET start_time = NOW(6);
        SELECT COUNT(*) INTO dummy_count FROM products WHERE price BETWEEN low_price AND high_price;
        INSERT INTO benchmark_timings VALUES ('mysql', 'price_range', TIMESTAMPDIFF(MICROSECOND, start_time, NOW(6)) / 1000);

        SET rand_offset = FLOOR(RAND() * row_count);
        SELECT SUBSTRING_INDEX(product_name, ' ', 1) INTO token_value FROM products LIMIT rand_offset, 1;
        SET start_time = NOW(6);
        SELECT COUNT(*) INTO dummy_count FROM (SELECT id FROM products WHERE product_name LIKE CONCAT('%', token_value, '%') LIMIT 50) AS t;
        INSERT INTO benchmark_timings VALUES ('mysql', 'name_keyword_contains', TIMESTAMPDIFF(MICROSECOND, start_time, NOW(6)) / 1000);

        SET page_offset = FLOOR(RAND() * GREATEST(row_count - 50, 1));
        SET start_time = NOW(6);
        SELECT COUNT(*) INTO dummy_count FROM (SELECT id FROM products ORDER BY price DESC LIMIT 50 OFFSET page_offset) AS t;
        INSERT INTO benchmark_timings VALUES ('mysql', 'price_order_page', TIMESTAMPDIFF(MICROSECOND, start_time, NOW(6)) / 1000);

        SET i = i + 1;
    END WHILE;
END//
DELIMITER ;
CALL run_benchmark($Iterations);
WITH ranked AS (
    SELECT
        dbms,
        query_name,
        duration_ms,
        ROW_NUMBER() OVER (PARTITION BY dbms, query_name ORDER BY duration_ms) AS rn,
        COUNT(*) OVER (PARTITION BY dbms, query_name) AS cnt
    FROM benchmark_timings
)
SELECT
    dbms,
    query_name,
    COUNT(*) AS iterations,
    ROUND(AVG(duration_ms), 4) AS avg_ms,
    ROUND(MAX(CASE WHEN rn = CEIL(cnt * 0.95) THEN duration_ms END), 4) AS p95_ms,
    ROUND(MIN(duration_ms), 4) AS min_ms,
    ROUND(MAX(duration_ms), 4) AS max_ms
FROM ranked
GROUP BY dbms, query_name
ORDER BY query_name;
"@ | Set-Content -LiteralPath $Path -Encoding UTF8
}

function Convert-MySqlTsvToCsv {
    param([string]$TsvPath, [string]$CsvPath)
    $lines = Get-Content -LiteralPath $TsvPath -Encoding UTF8 | Where-Object { $_.Trim().Length -gt 0 }
    $rows = foreach ($line in $lines) {
        $parts = $line -split "`t"
        if ($parts.Count -eq 7 -and $parts[0] -ne "dbms") {
            [PSCustomObject]@{
                dbms = $parts[0]
                query_name = $parts[1]
                iterations = $parts[2]
                avg_ms = $parts[3]
                p95_ms = $parts[4]
                min_ms = $parts[5]
                max_ms = $parts[6]
            }
        }
    }
    $rows | Export-Csv -LiteralPath $CsvPath -NoTypeInformation -Encoding UTF8
}

function Write-Summary {
    $postgresRows = Import-Csv -LiteralPath $PostgresCsv -Encoding UTF8
    $mysqlRows = Import-Csv -LiteralPath $MySqlCsv -Encoding UTF8
    $combined = @($postgresRows + $mysqlRows)
    $combined | Export-Csv -LiteralPath $SummaryCsv -NoTypeInformation -Encoding UTF8

    $sourceRowCount = (Import-Csv -LiteralPath $CsvPath -Encoding UTF8).Count
    $rowCount = if ([string]::IsNullOrWhiteSpace($Script:ImportedRowCount)) { $sourceRowCount } else { $Script:ImportedRowCount }
    $lines = @()
    $lines += "# PostgreSQL vs MySQL Query Benchmark Result"
    $lines += ""
    $lines += "- Run date: $(Get-Date -Format 'yyyy-MM-dd')"
    $lines += "- CSV: $CsvPath"
    $lines += "- Source CSV rows: $sourceRowCount"
    $lines += "- Imported rows after required-field validation: $rowCount"
    $lines += "- Iterations per query: $Iterations"
    $lines += "- Unit: milliseconds"
    $lines += "- Both DBs use the same schema and indexes: brand, category, source, price, product_name"
    $lines += ""
    $lines += "| DBMS | query | avg_ms | p95_ms | min_ms | max_ms |"
    $lines += "| --- | --- | ---: | ---: | ---: | ---: |"
    foreach ($row in ($combined | Sort-Object query_name, dbms)) {
        $lines += "| $($row.dbms) | $($row.query_name) | $($row.avg_ms) | $($row.p95_ms) | $($row.min_ms) | $($row.max_ms) |"
    }
    $lines += ""
    $lines += "## Query Set"
    $lines += ""
    $lines += "- brand_exact: brand exact match count"
    $lines += "- category_exact: category exact match count"
    $lines += "- source_exact: source exact match count"
    $lines += "- price_range: price range count"
    $lines += "- name_keyword_contains: product name contains keyword, limit 50"
    $lines += "- price_order_page: price descending page lookup"
    $lines += ""
    $lines += "## Note"
    $lines += ""
    $lines += "The result can vary depending on Docker resource limits, cache warm-up, and the current PC load. The name_keyword_contains query uses %keyword%, so a normal B-tree index is usually less helpful than a full-text or trigram index."
    $lines | Set-Content -LiteralPath $SummaryMd -Encoding UTF8
}

$TempDir = Join-Path $DbDir "postgres_mysql_benchmark_tmp"
New-Item -ItemType Directory -Force -Path $TempDir | Out-Null
$PostgresSql = Join-Path $TempDir "postgres_benchmark.sql"
$MySqlSql = Join-Path $TempDir "mysql_benchmark.sql"
$MySqlTsv = Join-Path $TempDir "mysql_query_benchmark.tsv"
Write-PostgresSql -Path $PostgresSql
Write-MySqlSql -Path $MySqlSql

try {
    Remove-ContainerIfExists $PostgresContainer
    Remove-ContainerIfExists $MySqlContainer

    Invoke-Docker @("run", "--name", $PostgresContainer, "-e", "POSTGRES_PASSWORD=$PostgresPassword", "-e", "POSTGRES_DB=$Database", "-d", "postgres:16")
    Invoke-Docker @("run", "--name", $MySqlContainer, "-e", "MYSQL_ROOT_PASSWORD=$MySqlPassword", "-e", "MYSQL_DATABASE=$Database", "-d", "mysql:8.4")

    Wait-Postgres
    Wait-MySql

    Invoke-Docker @("cp", $CsvPath, "${PostgresContainer}:/tmp/fashion_products.csv")
    Invoke-Docker @("cp", $CsvPath, "${MySqlContainer}:/tmp/fashion_products.csv")
    Invoke-Docker @("cp", $PostgresSql, "${PostgresContainer}:/tmp/postgres_benchmark.sql")
    Invoke-Docker @("cp", $MySqlSql, "${MySqlContainer}:/tmp/mysql_benchmark.sql")

    Invoke-Docker @("exec", "-i", $PostgresContainer, "psql", "-U", "postgres", "-d", $Database, "-f", "/tmp/postgres_benchmark.sql")
    $Script:ImportedRowCount = (docker exec $PostgresContainer psql -U postgres -d $Database -t -A -c "SELECT COUNT(*) FROM products;").Trim()
    Invoke-Docker @("cp", "${PostgresContainer}:/tmp/postgres_query_benchmark.csv", $PostgresCsv)

    $mysqlOutput = docker exec -i $MySqlContainer mysql --local-infile=1 --default-character-set=utf8mb4 -uroot "-p$MySqlPassword" $Database -f -B -r -N -e "source /tmp/mysql_benchmark.sql"
    if ($LASTEXITCODE -ne 0) {
        throw "MySQL benchmark failed"
    }
    $mysqlOutput | Set-Content -LiteralPath $MySqlTsv -Encoding UTF8
    Convert-MySqlTsvToCsv -TsvPath $MySqlTsv -CsvPath $MySqlCsv

    Write-Summary

    Write-Host "Saved PostgreSQL report: $PostgresCsv"
    Write-Host "Saved MySQL report: $MySqlCsv"
    Write-Host "Saved combined report: $SummaryCsv"
    Write-Host "Saved markdown summary: $SummaryMd"
}
finally {
    if (-not $KeepContainers) {
        docker rm -f $PostgresContainer | Out-Null
        docker rm -f $MySqlContainer | Out-Null
    }
}
