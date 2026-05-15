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
CALL run_benchmark(1000);
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
