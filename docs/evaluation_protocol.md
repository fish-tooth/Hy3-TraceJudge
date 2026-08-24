# Hy3-TraceJudge Evaluation Protocol

> **Status:** Award-Ready Evaluation Protocol v2.0  
> **Purpose:** 定义唯一正式评测口径。任何 benchmark、指标、人工抽检、图表与报告均应遵循本协议。  
> **Core principle:** **Solver 能力与 Evaluator 能力分离；Final Answer Correctness 与 Process Correctness 分离；任何 evaluator claim 必须由独立 gold 支撑。**

---

# 1. 评测问题

正式实验必须能回答以下 7 个问题：

| ID | Research / Product Question |
|---|---|
| **Q1** | Hy3 的最终答案准确率如何？ |
| **Q2** | Hy3-TraceJudge 能否正确判断一条显式推理过程是否成立？ |
| **Q3** | 当过程有错时，能否定位 **earliest error**？ |
| **Q4** | 能否可靠归类错误类型？ |
| **Q5** | 能否识别 **final-answer-correct but process-invalid**？ |
| **Q6** | Full evaluator 是否真的优于直接让 Hy3 Judge？ |
| **Q7** | 可靠性在哪个难度区间开始明显下降，系统仍有哪些失败模式？ |

其中：

- Q1 属于 **Solver Evaluation**；
- Q2–Q6 属于 **Evaluator Evaluation**；
- Q7 属于 **Capability Boundary / Analysis**。

---

# 2. 六条不可违反的评测原则

## P-01 — No Final-Answer Leakage

过程评估器不能通过 gold final answer 推断过程是否正确。

正式 evaluator 输入应明确列出可见字段。除某项实验明确研究 answer-aware evaluation 外，gold answer / gold first error 不得泄露到 Critic/Arbiter。

---

## P-02 — No Circular Ground Truth

禁止：

> Hy3 生成 → Hy3 判定 → 把 Hy3 判定当 gold → 再证明 Hy3-TraceJudge 有效。

Gold 优先级：

1. 第三方专家标注；
2. 可程序证明的确定性真值；
3. 独立人工审计；
4. LLM 辅助标签只能作为 weak label / candidate，不得作为唯一正式 gold。

---

## P-03 — Solver / Evaluator Decoupling

最终答案错误，不等于第一步错误。  
最终答案正确，也不等于过程正确。

必须分别保存：

- final answer verdict；
- process verdict；
- first error；
- error type；
- unsupported answer flag。

---

## P-04 — Earliest Error Is the Primary Localization Target

定位主指标必须是 **First-Error Exact Accuracy**。

允许：

- ±1 Accuracy；
- Step Distance；

但它们只能辅助解释，不能取代 Exact。

---

## P-05 — UNKNOWN Is Valid

任何 deterministic verifier 无法可靠判断时必须返回 `UNKNOWN`。

不能为了 coverage：

> parse 不出来 → 猜 INVALID  
> 语义复杂 → 猜 VALID

---

## P-06 — Test Freeze & Traceability

正式 test 前冻结：

- prompt；
- model setting；
- taxonomy；
- metric code；
- benchmark adapter；
- data manifest；
- fusion/arbitration rules。

正式结果必须能追溯：

`sample → raw response → parsed prediction → gold → config → commit → summary`

---

# 3. Canonical Data / Output Schema

所有 benchmark adapter 最终转换到统一 canonical schema。

## 3.1 Canonical Sample

```yaml
sample_id:
problem:
source:
source_split:
difficulty:
gold_answer:
answer_type:
gold_process_correct:
gold_first_error_step:
gold_error_type:
metadata:
```

### `gold_first_error_step`

内部唯一表示：

- `int`：1-based step id；
- `null`：全过程正确。

外部数据集若使用 `-1`、0-based 等，仅允许在 adapter 层转换。

---

## 3.2 Canonical Prediction

```yaml
sample_id:
final_answer:
final_answer_correct:
process_correct:
first_error_step:
error_type:
propagation_tag:
unsupported_answer:
confidence:
evidence:
  symbolic:
  semantic:
  consistency:
  dependency:
arbiter_used:
parse_status:
latency_ms:
retry_count:
run_id:
```

---

# 4. 三层 Benchmark 体系

# 4.1 Benchmark A — SolveBench

## 角色

评价 **Hy3 Solver 与最终应用**，满足官方：

- 标准答案；
- 自动校验；
- 难度分层；
- Final Answer Accuracy；
- 难度能力边界。

## 目标规模

**500–800 题**为 award-ready 目标。

若成本受限，应预先冻结分层抽样集，而不是跑完后根据结果挑题。

## 推荐来源

- GSM8K：基础应用推理；
- MATH：中高难数学；
- Omni-MATH 或等价公开高难集合：竞赛/高难。

## 难度

最终采用 D1–D5，并在正式 test 前冻结映射。

示例：

| Level | Meaning |
|---|---|
| D1 | 基础 |
| D2 | 中等 |
| D3 | 困难 |
| D4 | 竞赛 |
| D5 | Olympiad / 极高难 |

**注意：** 若来源数据自身难度体系与 D1–D5 不可直接对应，必须记录 mapping rule，不允许按结果“事后重分层”。

## SolveBench 主指标

- Final Answer Accuracy
- Answer Verifier Unknown Rate
- Parser Failure Rate
- Accuracy by Difficulty

如果没有独立过程 gold：

- 可报告 `Process Issue Flag Rate`；
- 可报告人工审计后的 process issue statistics；
- **不得称为 Process Classification Accuracy**。

---

# 4.2 Benchmark B — ProcessBench

## 角色

作为 **Evaluator 的第三方外部金标准**，解决“自己出题、自己判卷”的可信度问题。

正式使用前必须完成一次 dataset schema preflight：

- step 字段是什么；
- correct process 如何编码；
- first error 如何编码；
- 是否/如何提供 final-answer correctness metadata；
- 各 split 的样本数与含义；
- 官方 metric 的确切计算方式。

> 在实现前以实际下载的数据与官方说明为准；历史文档中的数字/字段不能替代 preflight。

## 正式比较

至少：

- **B0 — Hy3 Direct Judge**
- **Full — Hy3-TraceJudge**

推荐消融：

- + Symbolic
- + Dependency
- + Arbitration

## 主指标

### M1 — Error Detection Recall

仅在 gold process-invalid 样本：

`TP_error / N_gold_error`

表示能否至少发现过程有问题。

### M2 — First-Error Exact Accuracy

仅在 gold process-invalid 样本：

`#(pred_first_error == gold_first_error) / N_gold_error`

**核心主指标。**

### M3 — Correct Process Accuracy / Specificity

仅在 gold process-correct 样本：

`# predicted_correct / N_gold_correct`

### M4 — Process Status Accuracy

如果 benchmark 同时包含 correct / invalid：

`# correct process-status predictions / N_all`

### M5 — ProcessBench Official Composite

若使用官方 F1/综合指标：

- 复现官方公式；
- 报告组成项；
- 不只展示一个“F1”而不解释。

## 辅助定位指标

### ±1 Localization

`|pred-gold| <= 1`

### Mean Absolute Step Distance

仅在 pred 与 gold 都是错误步骤时计算；漏检应单独统计，不能通过排除漏检使 distance 看起来更好。

---

# 4.3 Benchmark C — TraceAdversarialBench

## 角色

提供：

- 可控 first-error gold；
- error-type gold；
- unsupported-answer gold；
- root/propagated 分析；
- 对 ProcessBench 缺少的自定义能力做定向压力测试。

---

## 4.3.1 Source Trace Admission

只有满足以下条件的源轨迹才能进入 mutation：

至少满足其一：

1. 来自可信 reference solution，且可被程序验证；
2. 由 Hy3 生成，但已通过 answer + process 复核；
3. 经人工确认过程正确。

不能仅因为最终答案正确，就认为源 trace 正确。

---

## 4.3.2 Tier A — Deterministic Mutations

优先实现：

- `ArithmeticMutation`
- `SignMutation`
- `OperatorMutation`
- `Denominator/NumericMutation`
- `SubstitutionMutation`
- `BasicAlgebraMutation`

要求：

- mutation step 已知；
- mutated claim 可确定为 false；
- 之前步骤保持不变且有效；
- mutation type 由程序确定；
- mutation version/seed 可追溯。

---

## 4.3.3 Tier B — Semantic / Structural Mutations

可选：

- `ConditionDeletion`
- `TheoremConditionViolation`
- `LogicGap`
- `HallucinatedFact`

这些样本若无法程序保证，必须：

- 人工确认；
- 或外部专家 gold；
- 或明确标为 weak-label，不进入主 gold metric。

---

## 4.3.4 Answer-Preserving Subset

构造：

1. 在已验证正确的中间步骤注入明确错误；
2. 保留/恢复最终 gold answer；
3. 确认错误步骤仍真实存在；
4. 标记：

```text
Final Answer Correct = True
Process Correct = False
Unsupported Answer = True
```

用于：

- Unsupported Answer Recall
- First-Error Exact
- Error-Type Accuracy

---

## 4.3.5 Split Discipline

至少分：

- `dev`
- `test`

mutation rule 可在 dev 调试。  
正式 test 生成规则/seed 范围必须在运行前冻结。

---

# 5. Answer Verification Protocol

# 5.1 Verification Stack

按顺序：

1. normalization；
2. exact / canonical string；
3. numeric；
4. fraction/percentage；
5. SymPy equivalence；
6. unordered sets / roots；
7. domain-specific verifier；
8. `UNKNOWN`.

---

# 5.2 Answer Verifier Metrics

单独建立 verifier test suite，报告：

- known-correct acceptance；
- known-wrong rejection；
- UNKNOWN rate；
- parse failure；
- 典型边界 case。

不把 evaluator 的错误算到 answer verifier。

---

# 6. Process Evaluation Protocol

每个 step 允许获得四路信息：

```text
Symbolic Verdict
Semantic Verdict
Consistency Verdict
Dependency / Propagation
```

## 6.1 Symbolic Verifier

状态：

- VALID
- INVALID
- UNKNOWN

首版范围：

- arithmetic；
- equality；
- substitution；
- basic algebra。

### 原则

**Precision-first.**

比赛亮点不是“SymPy 覆盖所有数学”，而是：

> 能形式化的地方提供高可信 deterministic evidence；不能形式化的地方诚实 UNKNOWN。

### Symbolic 子指标

- Coverage
- Invalid Precision
- Valid Precision
- UNKNOWN Rate

---

## 6.2 Hy3 Semantic Critic

主要覆盖：

- `PROBLEM_MISREAD`
- `CONCEPT_ERROR`
- `THEOREM_MISUSE`
- `CONDITION_OMISSION`
- `LOGIC_GAP`
- `HALLUCINATION`

输出必须结构化：

- status；
- step；
- error_type；
- evidence / explanation；
- dependency candidates。

---

## 6.3 Consistency Verifier

首版只做高价值规则：

- 变量/条件前后矛盾；
- 已知条件丢失；
- 当前结果与显式前一步不一致；
- 最终答案与步骤结论不一致。

不做低可信自然语言规则堆叠。

---

## 6.4 Dependency Graph

目的：

- 解释错误传播；
- 支持 root-cause；
- 辅助 earliest error；
- 支持 final-answer support consistency。

传播标签：

- ROOT
- PROPAGATED
- INDEPENDENT
- NONE

外部 benchmark gold 优先于内部 graph 定义；graph 不能“重新定义”ProcessBench first error。

---

## 6.5 Fusion / Arbitration

推荐规则：

| Evidence | Action |
|---|---|
| 高可信 Symbolic INVALID | 直接产生强 invalid evidence；仍保留语义上下文 |
| Symbolic UNKNOWN + Semantic clear | 采用 semantic，confidence 中等/高视一致性而定 |
| Symbolic VALID + Semantic INVALID | disagreement → Arbiter / low confidence |
| 多路一致 VALID | 放行 |
| 多路冲突 | selective arbitration |
| 证据不足 | UNKNOWN / Low Confidence |

### Arbiter 设计目标

不是“再叫一个 LLM 投票”，而是：

> 给 Hy3 Arbiter 提供**冲突证据**，让其只解决明确 disagreement。

---

# 7. Error Taxonomy Evaluation

一级 taxonomy：

1. PROBLEM_MISREAD
2. CONDITION_OMISSION
3. CONCEPT_ERROR
4. THEOREM_MISUSE
5. LOGIC_GAP
6. CIRCULAR_REASONING
7. ALGEBRA_ERROR
8. ARITHMETIC_ERROR
9. HALLUCINATION
10. ANSWER_FORMAT_ERROR
11. OTHER
12. UNKNOWN

传播属性单独评估，不计作一级类型。

## 有 gold 时

报告：

- Accuracy
- Macro-F1
- per-class P/R/F1
- Confusion Matrix

## 无 gold 时

只报告：

- Predicted Distribution
- 人工确认后的 subset distribution

不能报告虚假的 Error-Type Accuracy。

---

# 8. Unsupported Answer Evaluation

# 8.1 定义

`A = final_answer_correct`  
`P = process_correct`

目标：

`A=True && P=False`

---

# 8.2 指标

有完整 gold 时：

### Recall

`TP_unsupported / N_gold_unsupported`

### Precision

`TP_unsupported / N_pred_unsupported`

### F1

harmonic mean。

如果只有 answer-preserving positive subset，则只能可靠报告 Recall，不虚构 Precision。

---

# 8.3 真实样本分析

在 SolveBench Hy3 输出中挖掘：

- final answer correct；
- evaluator says invalid。

这些不能自动当 gold unsupported；必须进入人工 audit。

---

# 9. “误报率”与人工抽检协议

这是最容易写错的官方指标之一，必须分两种统计。

## 9.1 Classic FPR — 有完整过程 Gold 时

在 `gold_process_correct=True` 集合：

`FPR = FP / (FP + TN)`

适用于 ProcessBench 的正确过程 gold（若实际 schema 支持相应集合）和其他有过程真值数据。

---

## 9.2 Official Manual-Audit Ratio — Flagged Correct-Answer Samples

候选：

`final_answer_correct=True`
且
`pred_process_issue=True`

人工结果：

- REAL_PROCESS_ERROR
- FALSE_POSITIVE
- UNCERTAIN

### Real Issue Rate

`real / (real + false_positive)`

### False Discovery Proportion

`false_positive / (real + false_positive)`

`UNCERTAIN` 单独报告。

> 该比例是对官方“真实问题 vs 误报”的直接回答，不应错误命名为 classic FPR。

---

# 9.3 Sampling

正式目标：

- n=100；
- 若候选不足 100 → 全部审计；
- 固定 seed；
- 保持难度/来源覆盖；
- 保存完整 candidate pool 与 selected IDs。

**Case Study 精选样本不得计入正式随机抽样统计。**

---

# 9.4 Human Audit Record

至少：

```csv
sample_id,source,difficulty,final_answer_correct,
pred_process_correct,pred_first_error,pred_error_type,
human_verdict,human_first_error,human_error_type,
reviewer,notes
```

---

# 9.5 Award-Level Reliability

如能获得第二复核者：

- 至少复核 30 条；
- reviewer 尽量不知道 method variant；
- 报告 agreement；
- 条件允许报告 Cohen's κ。

若无法获得第二 reviewer，明确写为 limitation，不伪装双盲。

---

# 10. Baselines / Ablations

# 10.1 Mandatory Baseline

## B0 — Hy3 Direct Judge

同一 Hy3、同一 benchmark、同一显式过程输入。

输出：

- process correct；
- first error。

这是最关键 baseline。

---

# 10.2 Ablation Ladder

| Method | Description |
|---|---|
| B0 | Hy3 Direct Judge |
| A1 | Structured Audit Schema / Atomic Step Interface |
| A2 | A1 + Symbolic |
| A3 | A2 + Dependency / Root Cause |
| A4 | A3 + Arbitration |
| Full | 所有被最终保留模块 |

若 A1 对 ProcessBench 的原始步骤格式不适用，可在 SolveBench/自建 trace 单独做，不强行制造不公平比较。

---

# 10.3 Fairness

固定：

- model version；
- reasoning setting；
- temperature；
- dataset；
- sample order/manifest；
- retry policy；
- prompt version（除被研究变量）；
- seed。

额外报告：

- Hy3 calls/sample；
- latency；
- arbiter rate。

---

# 11. Statistical Protocol

# 11.1 Confidence Interval

主指标报告 **95% bootstrap CI**。

建议：

- 10,000 bootstrap resamples；
- 按 dataset split 分层抽样；
- 报告 point estimate + CI。

---

# 11.2 Full vs B0

使用 **paired bootstrap**：

对同一 sample 的 Full 与 B0 预测进行成对重采样，计算：

`Δ = Metric_Full - Metric_B0`

报告：

- mean/point Δ；
- 95% CI。

如果 CI 跨 0：

> “observed improvement”

不能写：

> “statistically significant improvement”。

---

# 11.3 Award-Level Target

以下是目标，不是伪造验收值：

- Full 在 First-Error Exact 上稳定优于 B0；
- 正确过程误报不因定位提升明显恶化；
- unsupported subset Recall 明显高于 B0；
- 至少一个关键模块在消融中有可解释贡献。

若主方法无稳定提升，应调整/简化方法，而不是只包装 UI。

---

# 12. Difficulty / Capability Boundary Protocol

每个难度报告：

- N
- Final Answer Accuracy
- Process metric
- First-Error Exact
- Correct Process Accuracy
- Error Detection Recall
- unsupported metric（样本足够时）
- 95% CI（核心指标）

---

# 12.1 临界点规则

正式分析前冻结，不允许看图后随意选。

## Rule A — Maximum Adjacent Drop

`Drop(D_i → D_i+1) = M(D_i) - M(D_i+1)`

最大相邻下降区间作为 empirical boundary 候选。

## Rule B — Reliability Threshold

可预先定义业务阈值，例如：

- First-Error Exact 低于某阈值；
- Correct Process Accuracy 低于某阈值。

阈值如果没有业务依据，不作为主结论，只做辅助。

---

# 12.2 Reporting Language

允许：

> “D3→D4 出现最大观察降幅。”

如果做了相应统计检验：

> “difference is statistically supported...”

否则禁止：

> “显著下降”。

---

# 13. Formal Experiment Lifecycle

# Stage 0 — Unit / Smoke

规模：

- 10–30 samples

目的：

- API；
- parser；
- index；
- cache；
- metrics。

不能作为正式结论。

---

# Stage 1 — Pilot Baseline

ProcessBench 分层 pilot：

- ~50–100 samples 起步；
- 人工核对 ≥20 条 adapter/gold/pred；
- 获取 Direct Hy3 初始失败模式。

输出：

- first real baseline table。

---

# Stage 2 — Development

只使用：

- ProcessBench dev/pilot subset；
- TraceAdversarialBench dev。

开发：

- symbolic；
- dependency；
- arbitration；
- prompts。

---

# Stage 3 — Pre-Registration / Freeze

冻结并写入 manifest：

- git commit；
- prompt hashes；
- configs；
- taxonomy version；
- metric version；
- dataset manifest；
- formal sample list。

---

# Stage 4 — Formal Evaluation

顺序：

1. B0 formal；
2. Full formal；
3. 关键 ablation；
4. SolveBench；
5. TraceAdversarialBench test；
6. manual audit sampling。

为节约成本：

- full test 不重复无意义调用；
- raw cache 不变时直接重算指标；
- 只有影响预测的修改才 rerun。

---

# Stage 5 — Analysis

生成：

- main results；
- ablation；
- difficulty；
- error distribution；
- unsupported answer；
- manual audit；
- failure cases；
- efficiency；
- limitations。

---

# 14. Reproducibility Protocol

每次正式 run 元数据：

```yaml
run_id:
git_commit:
created_at:
model:
provider:
endpoint_mode:
reasoning_setting:
temperature:
prompt_versions:
config_hash:
dataset_name:
dataset_version:
dataset_manifest_hash:
seed:
code_version:
```

每条 prediction 保存：

- raw model response；
- parsed output；
- parser status；
- verifier evidence；
- gold；
- latency；
- retry；
- error。

---

# 14.1 Cache

Cache key 至少包含：

- model；
- prompt；
- messages/input；
- relevant generation config。

如果 prompt/model/config 变化，不允许错误复用旧 cache。

---

# 14.2 Resume

- 以 `sample_id + method + run signature` 去重；
- completed samples 不重复调用；
- failed samples 可 retry；
- failure count 进入 summary。

---

# 15. Failure Accounting

正式报告必须展示：

- API failure；
- timeout；
- parse failure；
- verifier unknown；
- missing prediction；
- excluded sample 及原因。

**禁止 silent drop。**

主指标分母必须说明：

- all intended samples；
- successfully evaluated samples；
- exclusions。

---

# 16. Efficiency Protocol

至少报告：

- total Hy3 calls；
- calls/sample；
- Arbiter trigger rate；
- symbolic coverage；
- latency p50/p95；
- total runtime；
- 可获取时：token/cost proxy。

目标是证明：

> Hybrid verification 的价值来自“确定性证据 + selective reasoning”，不是无条件增加 LLM 调用次数。

---

# 17. Required Result Tables

## Table 1 — Evaluator Main Results

| Method | N | Error Detection ↑ | First-Error Exact ↑ | Correct Process Acc ↑ | Official Composite ↑ |
|---|---:|---:|---:|---:|---:|
| B0 Hy3 Direct | | | | | |
| A2 + Symbolic | | | | | |
| A3 + Dependency | | | | | |
| Full | | | | | |

每个核心 point estimate 附 95% CI。

---

## Table 2 — TraceAdversarialBench

| Method | N | First-Error Exact ↑ | Type Macro-F1 ↑ | Unsupported Recall ↑ |
|---|---:|---:|---:|---:|
| B0 | | | | |
| Full | | | | |

---

## Table 3 — Solver / Difficulty

| Difficulty | N | Final Acc ↑ | Process Issue Flag / Gold Process Metric* | First-Error Metric* |
|---|---:|---:|---:|---:|
| D1 | | | | |
| D2 | | | | |
| D3 | | | | |
| D4 | | | | |
| D5 | | | | |

`*` 仅在有相应 gold 时使用“Accuracy”；否则明确标记 predicted/audited statistic。

---

## Table 4 — Human Audit

| Item | Value |
|---|---:|
| Candidate flagged correct-answer samples | |
| Audited | |
| Real process errors | |
| False positives | |
| Uncertain | |
| Real Issue Rate | |
| False Discovery Proportion | |

---

## Table 5 — Efficiency

| Method | Calls/sample | Arbiter Rate | p50 Latency | p95 Latency |
|---|---:|---:|---:|---:|
| B0 | | | | |
| Full | | | | |

---

# 18. Required Case Studies

至少保存 6 类：

1. B0 错 / Full 对；
2. `Final ✓ / Process ✗`；
3. Symbolic 决定性证据；
4. Dependency/root propagation；
5. Full false positive；
6. Full false negative / wrong localization。

每个 case：

- sample id；
- problem；
- steps；
- gold；
- B0；
- Full；
- evidence；
- why it matters。

---

# 19. Reporting Rules

## 禁止

- 用 Final Accuracy 代替 Process Accuracy；
- 无 gold 时报告 Process Accuracy；
- 用人工 flagged-set FDP 冒充 classic FPR；
- 隐藏 UNKNOWN / parser failure；
- 用 test 调 prompt 后仍称 untouched test；
- 只展示精选案例；
- 把 LLM self-judgement 当独立 gold；
- 在没有统计支持时写“显著”。

## 必须

- 公式；
- N；
- 数据来源；
- gold 来源；
- CI；
- failure counts；
- raw traceability；
- limitations；
- formal run commit/config。

---

# 20. Final Claim Template

最终 README/报告的主 claim 应接近：

> Hy3-TraceJudge does not replace Hy3 with another judge. It augments Hy3 semantic reasoning with deterministic symbolic evidence and dependency-aware root-cause analysis. We evaluate the system against an external expert-labelled process benchmark, a controlled adversarial benchmark, and a human audit of correct-answer samples flagged as process-invalid.

只有实际实验支持后，才能补：

> Full improves earliest-error localization over Direct Hy3 Judge by **X** points (95% CI **[...]**) while maintaining/improving correct-process acceptance.

没有真实结果前，不预填 X。
