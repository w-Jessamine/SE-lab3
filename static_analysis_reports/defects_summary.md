## 静态分析汇总

- Pylint: 287 条
  - 按类别: {'convention': 215, 'warning': 65, 'refactor': 7}
- Bandit: 1 条
  - 按严重性: {'LOW': 1}

## Pylint 规则 Top 15（按出现次数）

| 次数 | message-id | symbol |
|---:|---|---|
| 161 | C0303 | trailing-whitespace |
| 31 | C0305 | trailing-newlines |
| 26 | W0621 | redefined-outer-name |
| 17 | W0611 | unused-import |
| 11 | C0411 | wrong-import-order |
| 10 | W0707 | raise-missing-from |
| 7 | C0413 | wrong-import-position |
| 4 | C0415 | import-outside-toplevel |
| 4 | W1309 | f-string-without-interpolation |
| 3 | W0718 | broad-exception-caught |
| 3 | R0401 | cyclic-import |
| 3 | R0801 | duplicate-code |
| 2 | W0404 | reimported |
| 1 | W0613 | unused-argument |
| 1 | C0412 | ungrouped-imports |

## 问题最多的文件 Top 15（Pylint+Bandit 合计）

| 次数 | 工具 | 文件 |
|---:|---|---|
| 44 | pylint | tests/test_order.py |
| 30 | pylint | scripts/seed.py |
| 26 | pylint | app/services/order_service.py |
| 23 | pylint | tests/test_inventory.py |
| 20 | pylint | tests/test_concurrency.py |
| 15 | pylint | app/services/menu_service.py |
| 14 | pylint | scripts/gen_images.py |
| 13 | pylint | app/models/dish.py |
| 12 | pylint | app/api/admin.py |
| 11 | pylint | app/services/inventory_service.py |
| 10 | pylint | app/db.py |
| 10 | pylint | app/models/order.py |
| 9 | pylint | tests/conftest.py |
| 6 | pylint | app/models/user.py |
| 5 | pylint | app/main.py |

## Bandit 明细（如有）

| severity | confidence | test_id | 文件:行 | 说明 |
|---|---|---|---|---|
| LOW | HIGH | B112 | app/services/image_service.py:82 | Try, Except, Continue detected. |

## 全量缺陷清单

- CSV: static_analysis_reports/defects.csv
- 原始报告: static_analysis_reports/pylint.json, static_analysis_reports/bandit.json
