\set iterations 1000
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
DO $$
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

    FOR i IN 1..1000 LOOP
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
$$;
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
