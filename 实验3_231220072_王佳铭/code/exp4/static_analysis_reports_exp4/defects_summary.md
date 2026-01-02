## EXP4 静态分析汇总（exp4_injected）

- Pylint: 292 条
  - 按类别: {'convention': 216, 'warning': 68, 'refactor': 8}
- Bandit: 4 条
  - 按严重性: {'LOW': 4}

## Pylint 规则 Top 20（按出现次数）

| 次数 | message-id | symbol |
|---:|---|---|
| 161 | C0303 | trailing-whitespace |
| 32 | C0305 | trailing-newlines |
| 26 | W0621 | redefined-outer-name |
| 17 | W0611 | unused-import |
| 11 | C0411 | wrong-import-order |
| 10 | W0707 | raise-missing-from |
| 7 | C0413 | wrong-import-position |
| 5 | W0718 | broad-exception-caught |
| 4 | C0415 | import-outside-toplevel |
| 4 | W1309 | f-string-without-interpolation |
| 3 | R0401 | cyclic-import |
| 3 | R0801 | duplicate-code |
| 2 | W0404 | reimported |
| 1 | W0613 | unused-argument |
| 1 | C0412 | ungrouped-imports |
| 1 | W0107 | unnecessary-pass |
| 1 | R1732 | consider-using-with |
| 1 | W0102 | dangerous-default-value |
| 1 | R0911 | too-many-return-statements |
| 1 | W0612 | unused-variable |

## Bandit 明细（如有）

| severity | confidence | test_id | 文件:行 | 说明 |
|---|---|---|---|---|
| LOW | HIGH | B110 | app/services/exp4_experiment_service.py:36 | Try, Except, Pass detected. |
| LOW | HIGH | B101 | app/services/exp4_experiment_service.py:60 | Use of assert detected. The enclosed code will be removed when compiling to optimised byte code. |
| LOW | HIGH | B112 | app/services/image_service.py:82 | Try, Except, Continue detected. |
| LOW | HIGH | B110 | app/services/inventory_service.py:73 | Try, Except, Pass detected. |

## 全量缺陷清单

- CSV: static_analysis_reports_exp4/defects.csv
- 原始报告: static_analysis_reports_exp4/pylint.json, static_analysis_reports_exp4/bandit.json
