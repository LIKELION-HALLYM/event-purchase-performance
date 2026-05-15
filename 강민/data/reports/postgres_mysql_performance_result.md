# PostgreSQL vs MySQL Query Benchmark Result

- Run date: 2026-05-10
- CSV: C:\Users\KKM\event-purchase-performance\강민\data\raw\fashion_products_final.csv
- Source CSV rows: 38479
- Imported rows after required-field validation: 30328
- Iterations per query: 1000
- Unit: milliseconds
- Both DBs use the same schema and indexes: brand, category, source, price, product_name

| DBMS | query | avg_ms | p95_ms | min_ms | max_ms |
| --- | --- | ---: | ---: | ---: | ---: |
| mysql | brand_exact | 0.0753 | 0.13 | 0.043 | 0.232 |
| postgresql | brand_exact | 0.0530 | 0.1000 | 0.0180 | 0.4770 |
| mysql | category_exact | 0.2392 | 0.66 | 0.049 | 1.072 |
| postgresql | category_exact | 0.1438 | 0.3210 | 0.0160 | 0.6120 |
| mysql | name_keyword_contains | 9.4747 | 12.59 | 0.09 | 19.008 |
| postgresql | name_keyword_contains | 4.0559 | 5.9071 | 0.0160 | 7.7740 |
| mysql | price_order_page | 1.6345 | 2.998 | 0.083 | 4.721 |
| postgresql | price_order_page | 1.9930 | 4.0741 | 0.0180 | 6.1650 |
| mysql | price_range | 0.8275 | 1.965 | 0.04 | 2.734 |
| postgresql | price_range | 0.8623 | 1.5767 | 0.0130 | 2.5150 |
| mysql | source_exact | 1.1482 | 1.509 | 0.075 | 2.081 |
| postgresql | source_exact | 0.5452 | 0.6671 | 0.0260 | 0.8950 |

## Query Set

- brand_exact: brand exact match count
- category_exact: category exact match count
- source_exact: source exact match count
- price_range: price range count
- name_keyword_contains: product name contains keyword, limit 50
- price_order_page: price descending page lookup

## Note

The result can vary depending on Docker resource limits, cache warm-up, and the current PC load. The name_keyword_contains query uses %keyword%, so a normal B-tree index is usually less helpful than a full-text or trigram index.
