## 实验报告：Python 美食点单项目静态分析对比（Pylint/Bandit/Semgrep + LLM）

### 0. 实验对象与产物位置

- **注入前代码**：项目根目录（未注入缺陷）
- **注入后代码**：`exp4_injected/`（在副本中注入 8 处缺陷，尽量放在不常走路径）

本实验已经把所有工具输出和标注文件整理到 `flaw_report/`：

- **Pylint/Bandit（我在目录名上沿用了老师示例里的 CppCheck）**：`flaw_report/CppCheck/`
  - 原始报告：`flaw_report/CppCheck/pylint.json`、`flaw_report/CppCheck/bandit.json`
  - 标注：`flaw_report/CppCheck/true_positive.json`、`flaw_report/CppCheck/false_positive.json`
- **LLM（ChatGPT）**：`flaw_report/ChatGPT/`
  - 结果源文件：`flaw_report/ChatGPT/record.txt`
  - 标注：`flaw_report/ChatGPT/true_positive.json`、`flaw_report/ChatGPT/false_positive.json`
- **Semgrep（Registry packs）**：`flaw_report/Semgrep/`
  - 原始报告：`flaw_report/Semgrep/semgrep_after_registry.json`
  - 标注：`flaw_report/Semgrep/true_positive.json`、`flaw_report/Semgrep/false_positive.json`

> 注：Pylint/Bandit 的“注入后”原始输出也在：`exp4_injected/static_analysis_reports_exp4/`
>  
> Semgrep 的“注入前/后（Registry packs）”原始输出分别在：
> - 注入前：`semgrep_reports_registry/semgrep_before_registry.json`
> - 注入后：`exp4_injected/semgrep_reports_registry/semgrep_after_registry.json`

---

### 1. 三种分析工具的检测过程

#### 1.1 Pylint（代码质量/可维护性）

- **选择原因**：覆盖大量“容易埋雷”的 Python 代码问题（宽泛异常、危险默认参数、资源管理建议等），适合看代码质量和潜在 bug。
- **运行方式**：
  - 使用 `.pylintrc`（JSON 输出、排除无关目录、降低部分噪声规则）
  - 注入后在 `exp4_injected/` 中运行（示例）：  
    `python -m pylint app scripts tests --output-format=json > static_analysis_reports_exp4/pylint.json`
- **结果**：
  - 注入前：287 条（见 `static_analysis_reports/pylint.json`）
  - 注入后：292 条（见 `exp4_injected/static_analysis_reports_exp4/pylint.json`）
  - 变化：**+5 条**

#### 1.2 Bandit（危险模式/安全基线）

- **选择原因**：更偏“安全/危险模式”检测，报告通常更少但更聚焦，适合作为安全基线扫描。
- **运行方式**：
  - 使用 `bandit.yaml`（排除模板/静态资源/UI 等目录）
  - 注入后在 `exp4_injected/` 中运行（示例）：  
    `python -m bandit -r app scripts -c bandit.yaml -f json -o static_analysis_reports_exp4/bandit.json`
- **结果**：
  - 注入前：1 条（见 `static_analysis_reports/bandit.json`）
  - 注入后：4 条（见 `exp4_injected/static_analysis_reports_exp4/bandit.json`）
  - 变化：**+3 条**

#### 1.3 Semgrep（可扩展规则库）

- **选择原因**：可以通过“选规则包/写规则”扩展覆盖面，适合做对比实验。
- **运行方式**：
  - 一开始用 `--config auto`：注入前/后均 0 findings（对本次注入缺陷覆盖不足）
  - 后续启用更多规则源（Registry packs），并强制不依赖 git ignore：  
    `--config p/security-audit --config p/python --config p/bandit --no-git-ignore --metrics off`
- **结果（Registry packs）**：
  - 注入前：0 findings（`semgrep_reports_registry/semgrep_before_registry.json`）
  - 注入后：1 finding（`exp4_injected/semgrep_reports_registry/semgrep_after_registry.json`）
  - 命中：`gitlab.bandit.B101`（非测试代码使用 `assert`）

#### 1.4 LLM（ChatGPT：语义审计）

- **方式**：用 LLM 对 API/service 做语义审计，结果落在 `record.txt`（并复制到 `flaw_report/ChatGPT/record.txt`）。
- **结果**：共 6 条（主要集中在鉴权/越权/IDOR/身份绑定等语义问题）。

---

### 2. TP/FP 评估（真实报告与误报）

#### 2.1 判定标准（我怎么判）

- **TP（True Positive）**：报告指出的缺陷在代码中确实存在，且能从代码直接证明风险或错误路径。
- **FP（False Positive）**：报告点在该项目语境下不构成缺陷（风格告警、工程折中、或需求允许）。

标注文件已经生成：

- Pylint/Bandit：`flaw_report/CppCheck/true_positive.json`、`flaw_report/CppCheck/false_positive.json`
- LLM：`flaw_report/ChatGPT/true_positive.json`、`flaw_report/ChatGPT/false_positive.json`
- Semgrep：`flaw_report/Semgrep/true_positive.json`、`flaw_report/Semgrep/false_positive.json`

#### 2.2 植入缺陷清单（注入后 exp4_injected）

（按注入点的文件与行号列出；工具是否命中以本次实际报告为准）

| 注入点（文件:行） | 缺陷类型（CWE） | Pylint | Bandit | Semgrep(Registry packs) |
|---|---:|---:|---:|---:|
| `app/services/inventory_service.py:73` | 吞异常导致部分成功/不一致（CWE-703） | ✅ | ✅ | ❌ |
| `app/services/exp4_experiment_service.py:17` | open 未 with（CWE-772） | ✅ | ❌ | ❌ |
| `app/services/exp4_experiment_service.py:27` | 金额计算错误（CWE-682） | ❌ | ❌ | ❌ |
| `app/services/exp4_experiment_service.py:36` | 吞异常返回默认值（CWE-703） | ✅ | ✅ | ❌ |
| `app/services/exp4_experiment_service.py:45` | 输入校验缺失示例（CWE-20） | ❌ | ❌ | ❌ |
| `app/services/exp4_experiment_service.py:48` | 可变默认参数（CWE-664） | ✅ | ❌ | ❌ |
| `app/services/exp4_experiment_service.py:60` | assert 作校验（CWE-754） | ❌ | ✅ | ✅ |
| `app/main.py:65` | open 未关闭（CWE-772） | （未纳入标注） | ❌ | ❌ |

#### 2.3 误报率与原因（按本次标注集）

> 这里的“误报率”是基于我挑选出来用于写报告的标注集，不等于全量报告的统计（全量太大且大多是风格项）。

- **Pylint/Bandit（`flaw_report/CppCheck/`）**
  - TP：5 条；FP：3 条  
  - **误报率**：3 / (5 + 3) = **37.5%**
  - **我认为的误报原因**：
    - Pylint 的部分规则是“结构/风格建议”，容易把工程折中当问题（例如 `import-outside-toplevel` 用于规避循环依赖/按需导入）。
    - Bandit 对 `try/except/continue` 这类容错批处理策略偏保守：如果业务允许“尽力而为”，这条更像“需要日志/监控”的提示，而不是必然缺陷。

- **Semgrep（`flaw_report/Semgrep/`，Registry packs）**
  - TP：1 条；FP：0 条
  - **误报率**：0%
  - **但更显著的是漏报**：只命中 1 个点，说明规则包对这批“可靠性/逻辑/资源类缺陷”的覆盖有限；Semgrep 的上限很高，但强弱非常依赖你选了什么规则/是否自定义规则。

- **LLM（`flaw_report/ChatGPT/`）**
  - TP：6 条；FP：0 条（本次未强行凑 FP）
  - **误报风险（需要在报告里诚实写）**：LLM 很依赖上下文。比如如果项目有全局鉴权中间件但没展示给模型，它会把“路由里没校验”直接判为漏洞；这种偏差本质上是“输入信息不完整”。

---

### 3. 整体评价与推荐组合（更像人写的总结）

- **Pylint**：像代码卫生检查员。能抓很多坏味道和潜在 bug，但报告会很吵，必须筛选/分级，不然容易把真正的问题淹没。
- **Bandit**：像危险动作探测器。报告少但更聚焦，适合做安全基线；对 assert/吞异常这种点挺敏感。
- **Semgrep**：像可调参雷达。选对规则包或写规则时很强；但这次也能看出来——如果规则不对味，它可能“几乎看不见”你注入的大部分缺陷。
- **LLM**：像懂业务的代码审计员。对鉴权/越权/身份绑定/IDOR 这类“语义问题”更敏感，刚好补上规则工具的短板；缺点是需要足够上下文，否则判断会偏保守。

**推荐组合（类似 FastAPI 单体项目）**：

- 日常开发：`ruff/black + pylint`（质量） + `bandit`（安全基线）
- 上线前或做实验对比：在上面基础上加 `semgrep(选规则包/写自定义规则)`，专门补“项目特有模式”
- 对鉴权/越权这类语义漏洞：最好再加一轮 **LLM review** 或人工 code review（规则工具很难完全替代）


