# MathXRay Requirements Specification

> **Status:** Award-Ready Baseline v2.0  
> **Role:** 本文件是项目范围、官方要求映射与验收标准的唯一权威来源（Single Source of Truth）。  
> **Companion docs:** `evaluation_protocol.md`、`milestones.md`  
> **Project:** MathXRay — Hybrid Process Verification and Root-Cause Error Localization for Mathematical Reasoning

---

## 0. 文档治理与优先级

当不同方案、历史文档或实现意见冲突时，按以下优先级处理：

1. **官方课题要求**：不可被删减或改写成更弱要求；
2. **本文件 P0 Requirement**：官方要求的工程化验收解释；
3. **`evaluation_protocol.md`**：指标、数据、统计与人工审计的唯一口径；
4. **`milestones.md`**：实施顺序、时间与退出 Gate；
5. **方案文档中的设计亮点**：作为 P1/P2 增强项，只有经过实验验证后才能成为最终 claim。

### 0.1 Requirement 类型

| 类型 | 含义 |
|---|---|
| **P0 / MUST** | 官方要求或完成官方要求所必需的工程条件；缺失即不完整 |
| **P1 / SHOULD** | 形成竞赛区分度和可信度的核心增强；目标是全部完成 |
| **P2 / STRETCH** | 有时间/预算时增加的高级能力；不得挤占 P0/P1 |
| **ALLOW / NOTE** | 官方允许的实现方式或参考信息，不计作“硬性要求” |

> **重要纠偏：** 官方文档中的 Hy3 仓库链接是参考链接，不单独计为一条官方交付要求；“实现方式不限”是设计自由度说明，不是必须实现多 Agent/沙盒等全部方案。

---

# 1. 项目 North Star

## 1.1 一句话定位

**MathXRay 是一个基于 Hy3 的数学推理解题与审计应用：它不仅验证最终答案，还通过 Hy3 语义审查、SymPy 确定性验证、依赖感知根因定位与冲突仲裁，判断过程是否成立、定位 earliest error、归类错误，并识别“最终答案正确但过程无法支撑结论”的样本。**

## 1.2 最终要回答的五个问题

1. 最终答案是否正确？
2. 显式、可审计的解题过程是否成立？
3. 若不成立，**最早引入错误的步骤**是哪一步？
4. 错误属于什么类型？
5. 若答案正确，它是否真的被前序推理所支持？

## 1.3 项目成功不是“做出一个 Demo”

比赛版成功必须同时具备：

- **Product:** Hy3 可运行应用；
- **Verification:** 最终答案与推理过程均有验证路径；
- **External Evidence:** 在第三方过程金标准上证明评估器有效；
- **Controlled Evidence:** 自建可控错误集验证细粒度定位与类型；
- **Human Evidence:** 对答案正确但被判过程异常的样本执行人工抽检；
- **Scientific Rigor:** 有 baseline、消融、难度分析、失败分析、置信区间与可复现记录；
- **Presentation:** README 与 <120s Demo 能在极短时间内讲清“为什么、怎么做、是否有效”。

---

# 2. Scope Freeze

## 2.1 已冻结决策

| 维度 | 决策 |
|---|---|
| 场景 | 数学推理：应用题、代数/高数、竞赛/高难数学 |
| 核心模型 | **Hy3** |
| Hy3 角色 | Solver + Semantic Critic；冲突样本可作为 Arbiter |
| Solver 输出 | 公开、简洁、结构化、可审计的 `solution_steps`，不依赖隐藏思维链 |
| 外部过程 Benchmark | **ProcessBench** |
| 应用侧题集 | **SolveBench** |
| 自建可控题集 | **TraceAdversarialBench** |
| 确定性验证 | **SymPy + 规则/一致性检查** |
| 核心定位任务 | **Earliest Error Localization** |
| 核心异常场景 | **Final-Answer-Correct but Process-Invalid / Unsupported Answer** |
| 过程结构增强 | Dependency Graph：ROOT / PROPAGATED / INDEPENDENT |
| UI | Streamlit |
| 运行方式 | Hy3 Provider 抽象；默认云 API，可兼容 OpenAI-compatible 本地 endpoint |
| 实验原则 | raw-first、可恢复、可重算、test freeze、无自证循环 |

## 2.2 明确非目标

以下内容不作为比赛版必须完成项：

- 训练、微调或本地部署 295B 级 Hy3；
- 完整自然语言定理证明器；
- Lean/Coq 全量形式化；
- 全量人工 step-level 标注；
- 与课题无关的账户、数据库、微服务体系；
- 为“看起来高级”而堆叠大量 Agent；
- 在没有实验收益的情况下保留复杂模块。

---

# 3. 官方要求追踪矩阵（P0）

> 编号沿用并规范化 R1–R20，便于和历史 WorkBuddy 文档兼容。  
> R2 与 R5 是总纲要求，拆分为子项；R10 为官方“实现方式不限”的 ALLOW 项，不作为“必须多 Agent”的验收项。

| ID | 级别 | 官方要求/含义 | 对应实现 | 验证方法 | 最终产物 |
|---|---|---|---|---|---|
| **R1** | MUST | 基于 Hy3 构建面向可验证场景的 AI 应用 | Hy3 Provider + Math Solver + Process Evaluator | 端到端 smoke；运行元数据确认 Hy3 | `app.py`、`src/llm/`、`src/solver/` |
| **R2.1** | MUST | 除最终答案外，评估推理过程是否成立 | Hybrid Evidence Verification | ProcessBench / controlled gold | evaluator + 过程结果 |
| **R2.2** | MUST | 定位错误发生步骤 | Earliest Error Localization | First-Error Exact Accuracy | 定位结果与案例 |
| **R2.3** | MUST | 归纳错误类型 | 稳定错误 taxonomy + classifier | gold 子集 Macro-F1；人工复核 | taxonomy + 分布 |
| **R2.4** | MUST | 识别答案正确但过程不能支撑结论 | A/P 二维判定 + Support Consistency | Answer-preserving subset + 人工案例 | unsupported 标记与指标 |
| **R3** | MUST | 选择一个可验证方向 | 选择数学推理 | dataset card / 场景说明 | 项目说明 |
| **R4** | MUST | 可运行应用输出完整解答过程，而非仅答案 | Atomic Verifiable Solution Steps | UI 端到端演示；schema validation | Streamlit + Demo |
| **R5.1** | MUST | 每题有明确标准答案 | 公开 gold / 派生 gold | 数据完整性检查 | 分层题集 + gold |
| **R5.2** | MUST | 每题有可自动校验判定方式 | Answer Verifier：normalize / numeric / SymPy / set | verifier tests + unknown/failure 统计 | 答案校验模块 |
| **R5.3** | MUST | 按难度分层，覆盖基础到高难 | SolveBench D1–D5（冻结后不可随意改） | 分层样本统计 | 分层数据 + 结果 |
| **R5.4** | MUST | 说明来源、构造方式、分层依据 | Dataset Card + manifest + build config | 从配置重建/追溯 | `data/README.md` / manifest |
| **R6** | MUST | 过程正确性覆盖跳步、循环论证、误用定理、条件遗漏、幻觉等 | Semantic + Symbolic + Consistency + Dependency | ProcessBench、adversarial、case audit | evaluator + taxonomy |
| **R7** | MUST | 解答错误时定位错误开始步骤 | root-cause-aware first error | Exact 为主；±1/距离为辅 | localization report |
| **R8** | MUST | 建立错误分类体系 | 10+ 类一级错误 + propagation tag | type gold / human audit | taxonomy doc + confusion matrix |
| **R9** | MUST | 识别猜中、数值巧合、误用定理却答案正确等 | Answer-Preserving Mutation + real cases | Unsupported P/R/F1（有 gold 时） | 专项结果 + Demo case |
| **R10** | ALLOW | 实现方式不限，可用规则、分步 LLM、沙盒、多 Agent 等 | 选择组合式方法，不要求全部实现 | 消融验证实际选用模块 | 方法说明 |
| **R11** | MUST | 验证定位准确率 | 外部过程 gold + 可控 gold | Error Detection + First-Error Exact | 定位验证数据 |
| **R12** | MUST | 答案正确样本中，对被判过程异常者人工抽检真实问题 vs 误报 | Formal Manual Audit | Real Issue Rate + False Discovery Proportion；有完整负类 gold 时另报 classic FPR | `manual_audit.csv` |
| **R13** | MUST | 输出最终答案准确率、过程正确率、错误类型分布 | 统一 metrics/report pipeline | raw → summary 重算 | 完整结果 |
| **R14** | MUST | 按难度分析并指出表现明显下降区间 | Difficulty curves + capability boundary rule | 分层统计 + CI / 最大相邻降幅 | 难度与临界点分析 |
| **R15** | MUST | 开源仓库：源码、评估模块、README、环境样例、运行说明 | 完整 repo + clean setup | clean clone smoke | 公开仓库 |
| **R16** | MUST | 评测材料：分层题集/标准答案/答案校验/过程评估 | data manifest + scripts + evaluator | 重建/运行检查 | 评测材料包 |
| **R17** | MUST | 完整评测结果 | raw + parsed + summary + figures | 一致性检查 | `results/` + `reports/` |
| **R18** | MUST | 定位准确率、误报验证数据及人工抽检记录 | benchmark + audit | audit trail | 验证结果包 |
| **R19** | MUST | 分析报告：方法依据、taxonomy、典型案例、能力边界与临界点 | final report | claim-to-evidence review | `reports/final_report.md` |
| **R20** | MUST | ≤2 分钟 Demo/GIF 展示完整解题与过程评估 | ~110s script | 实际时长 + 内容 checklist | MP4/GIF |

---

# 4. P0 详细验收规范

## R1 / R3 / R4 — Hy3 应用与完整解答过程

### 对应实现

最终应用至少具有两条明确 Hy3 调用路径：

1. **Hy3 Solver**：输入数学题，输出结构化 `solution_steps + final_answer`；
2. **Hy3 Semantic Critic**：对显式步骤做语义/逻辑审查。

当多路验证器冲突时，可选第三条：

3. **Hy3 Arbiter**：只处理 disagreement/low-confidence 样本。

### Solver 输出约束

公开审计步骤应：

- step id 稳定；
- 一步尽量只包含一个主要推断；
- statement 与 expression 尽量分离；
- 不要求也不展示模型私有/隐藏思维链；
- 可由外部 evaluator 独立引用。

### 验收

- [ ] 用户无需 WorkBuddy/CodeBuddy 即可运行最终应用
- [ ] 正式配置实际使用 Hy3
- [ ] 一道示例题可完成 `solve → answer verify → process audit → display`
- [ ] API failure / parse failure 可见且可恢复
- [ ] README 明确“Hy3 在系统中的两个/三个核心角色”

---

## R5 — 评测题集与自动校验

### SolveBench

用于评价应用侧 Hy3 Solver。

目标规模：**500–800** 题；若 API/时间受限，可采用预注册的分层子集，但正式报告必须说明采样规则与局限。

建议来源：

- GSM8K（基础/应用推理）
- MATH（中高难）
- Omni-MATH 或同类公开高难数学集（高难/竞赛）

### 每条样本必须具备

- `sample_id`
- `problem`
- `gold_answer`
- `source`
- `source_split`
- `difficulty`
- `answer_type`
- `verification_strategy`
- `license_or_citation`
- `dataset_version`

### 自动答案校验

优先级：

1. normalized exact；
2. numeric equivalence；
3. fraction/percentage；
4. SymPy symbolic equivalence；
5. unordered set/root equivalence；
6. 无法可靠判断 → `UNKNOWN`，进入排除/人工规则，不得静默当错。

### 验收

- [ ] 正式统计样本 gold 缺失率为 0
- [ ] 正式统计样本均有确定的 verification strategy
- [ ] verifier 对 pilot 边界样本有测试
- [ ] `UNKNOWN / PARSE_ERROR` 单独统计
- [ ] 来源与难度映射可追溯

---

## R2.1 / R6 — 过程正确性

### Hybrid Evidence Verification

每步允许获得以下证据：

- `symbolic_verdict ∈ {VALID, INVALID, UNKNOWN}`
- `semantic_verdict ∈ {VALID, INVALID, UNKNOWN}`
- `consistency_verdict ∈ {VALID, INVALID, UNKNOWN}`
- `dependency_tag ∈ {ROOT, PROPAGATED, INDEPENDENT, NONE}`
- evidence 文本/表达式
- confidence / disagreement status

### 核心原则

- SymPy **宁可 UNKNOWN，不做超范围强判**；
- Hy3 Critic 负责定理适用、条件遗漏、逻辑跳步、幻觉等语义问题；
- 依赖图不作为“另一票 LLM”，而用于解释错误因果传播；
- 冲突样本才调用 Arbiter，控制成本并提高可审计性。

### 验收

- [ ] evaluator 输出明确 `process_correct`
- [ ] 每个 INVALID 有可追踪 evidence source
- [ ] 官方列举的问题类型都映射到 taxonomy
- [ ] `UNKNOWN` 不被伪装成 VALID

---

## R2.2 / R7 / R11 — Earliest Error Localization

### 唯一主定义

**Earliest Error = 按显式步骤顺序，第一个引入新的不成立推断的步骤。**

不是：

- 第一个“看起来可疑”的步骤；
- 第一个最终答案变错的步骤；
- 任意错误步骤；
- 第一个传播错误步骤。

### 内部规范

- UI 对用户使用 1-based `step_id`；
- 内部 canonical gold 使用 `int | null`；
- `null` 表示全过程正确；
- 外部 benchmark 的 `-1/0-based/其他编码` 只能在 adapter 层转换，核心 evaluator 禁止混用。

### 验收

- [ ] **First-Error Exact Accuracy** 是主定位指标
- [ ] ±1 与 distance 只作为辅助
- [ ] 人工核对至少 20 个 adapter 样本，覆盖 correct / first / middle / last error
- [ ] root / propagated 不改变外部 benchmark 的 gold 定义

---

## R2.3 / R8 — 错误 Taxonomy

### 一级类别 v1

| 类别 | 定义 |
|---|---|
| `PROBLEM_MISREAD` | 误读题意/目标/对象 |
| `CONDITION_OMISSION` | 忽略必要条件或约束 |
| `CONCEPT_ERROR` | 数学概念理解错误 |
| `THEOREM_MISUSE` | 定理/公式适用条件错误 |
| `LOGIC_GAP` | 无足够依据的跳步或非蕴含推导 |
| `CIRCULAR_REASONING` | 以待证结论或等价结论作前提 |
| `ALGEBRA_ERROR` | 代数变形不等价 |
| `ARITHMETIC_ERROR` | 数值运算错误 |
| `HALLUCINATION` | 引入题目/前文不存在事实 |
| `ANSWER_FORMAT_ERROR` | 解法基本成立但最终答案表示不符合要求 |
| `OTHER` | 有真实错误但当前 taxonomy 无合适类别 |
| `UNKNOWN` | 无法可靠分类 |

### 独立传播属性

- `ROOT_ERROR`
- `PROPAGATED_ERROR`
- `INDEPENDENT_ERROR`

> `PROPAGATED_ERROR` **不是一级错误类型**；否则“错误原因”和“错误传播关系”会被混成一个维度。

### 验收

- [ ] 官方示例类别全部可映射
- [ ] taxonomy 有 annotation guide
- [ ] Tier-A mutation 提供部分类型 gold
- [ ] 无 gold 真实样本只能报告“预测分布”，不能伪称分类准确率

---

## R2.4 / R9 — Final Correct but Process Invalid

### 核心二维状态

| Final Answer | Process | 状态 |
|---|---|---|
| Correct | Correct | Supported Correct |
| Correct | Invalid | **Unsupported Answer** |
| Wrong | Correct until final output | Finalization/format failure |
| Wrong | Invalid | Ordinary failure |

### 实现

- Answer Verifier 独立给出 A；
- Process Evaluator 独立给出 P；
- 当 `A=True && P=False` 时标记 `unsupported_answer=true`；
- Support Graph Check 作为解释增强：最终结论是否由有效依赖路径支持。

### 验收

- [ ] TraceAdversarialBench 必须包含 answer-preserving subset
- [ ] 报告 Unsupported Answer Recall
- [ ] 有可靠 gold 时进一步报告 Precision/F1
- [ ] Demo 至少展示 1 个该类案例
- [ ] 不能通过“最终答案正确”覆盖过程错误

---

## R12 — 人工误报抽检

官方要求的是：

> 在最终答案正确样本中，被评估器判为过程存在问题的样本，经人工抽检确认真实问题与误报比例。

### 正式候选集合

`final_answer_correct == True AND evaluator_flags_process_issue == True`

### 最低审计要求

- 固定 seed；
- 保存 candidate pool；
- 使用预先定义的随机/分层随机采样；
- 记录 `REAL_PROCESS_ERROR / FALSE_POSITIVE / UNCERTAIN`；
- 保存人工 first error/type/notes；
- case study 的精选样本不得混入正式统计分母。

### 指标命名必须正确

**Flagged-set False Discovery Proportion**

`FALSE_POSITIVE / (REAL_PROCESS_ERROR + FALSE_POSITIVE)`

这是官方人工抽检最直接对应的比例。

若拥有完整 gold correct-process 负类集合，可另报：

**Classic FPR**

`FP / (FP + TN)`

二者不能混称。

### Award-level 增强

- 正式抽检目标 n≈100，若候选不足则全审；
- 尽可能让第二位复核者对 ≥30 条样本独立复核；
- 报告 agreement / Cohen's κ（若有第二复核者）；
- Reviewer 尽量不知道样本来自 baseline 还是 full，降低确认偏差。

---

# 5. P1 — 竞赛区分度需求

## EXT-01 — Direct Hy3 Judge Baseline

必须有：

**B0 = Hy3 Direct Judge**

输入同样的题目与显式步骤，直接预测过程是否正确与 first error。

目的：

> 证明复杂系统不是“复杂而已”，而是真的比直接调用 Hy3 更可靠。

**验收：**

- [ ] B0 与 Full 在相同 benchmark / model / generation settings 下比较
- [ ] 主结果必须展示 B0
- [ ] 若 Full 没有可靠提升，不夸大 claim

---

## EXT-02 — ProcessBench 外部公开证明

ProcessBench 是 evaluator 的外部可信锚点。

**验收：**

- [ ] 最终正式结果优先跑完整目标集
- [ ] 数据 schema / label semantics 在实现前人工核验
- [ ] raw predictions 保留
- [ ] 不用自建 label 替换官方 gold

---

## EXT-03 — TraceAdversarialBench

建立两层真值：

### Tier A — Deterministic

- Arithmetic
- Sign
- Operator
- Denominator/Numeric
- Basic algebra/substitution

### Tier B — Semantic / Structural

- Condition omission
- Theorem misuse
- Logic gap
- Hallucination

Tier B 若无法程序保证，必须人工/外部 gold 支持。

**验收：**

- [ ] mutation step 可追溯
- [ ] source trace 必须先被验证为正确
- [ ] 每条样本保存 mutation version/seed
- [ ] dev/test 分离
- [ ] answer-preserving subset 单独统计

---

## EXT-04 — Root Cause vs Propagated Error

目标：

- `ROOT_ERROR`
- `PROPAGATED_ERROR`
- `INDEPENDENT_ERROR`

**验收：**

- [ ] 至少有 3 个真实 case 展示该模块价值
- [ ] root-cause 机制不能降低 benchmark first-error 定义的一致性
- [ ] 依赖图错误时允许回退，不强行产生因果解释

---

## EXT-05 — Hybrid Evidence + Conflict Arbitration

**验收：**

- [ ] deterministic evidence 具有优先解释权
- [ ] 冲突进入 arbitration 或 low-confidence
- [ ] Arbiter 只处理分歧样本，而非无条件多次 LLM 投票
- [ ] report 中记录额外调用/延迟

---

## EXT-06 — 消融实验

最小对照：

- B0: Direct Hy3 Judge
- A1: + Structured audit interface / schema（若与 benchmark 输入设计相容）
- A2: + Symbolic Verifier
- A3: + Dependency / Root Cause
- A4: + Arbitration
- Full

**模块进入最终“贡献列表”的条件：**

至少满足其一：

1. 在预注册主指标上相对前一版本有稳定提升；
2. 改善特定关键子集且有明确作用机制；
3. 明显降低 FPR/FDP、成本或失败率。

不能因为“架构图好看”就宣称贡献。

---

## EXT-07 — 统计可信度

**必须：**

- 主指标报告 95% bootstrap CI；
- Full vs B0 使用 paired bootstrap 比较差值；
- subgroup 报告样本数 N；
- 不在没有统计检验时使用“statistically significant”。

**推荐目标：**

- Full 在 ProcessBench 主指标相对 B0 获得稳定正向差值；
- 若 95% CI 跨 0，写为“observed improvement”，而不是“显著提升”。

---

## EXT-08 — 可复现实验与 Provenance

每次 run 必须记录：

- `run_id`
- git commit
- model/provider
- prompt version/hash
- config hash
- dataset/version/manifest hash
- seed
- raw response
- parsed prediction
- parse/API failure
- latency/retry
- verifier evidence
- metric summary

**验收：**

- [ ] raw → summary 可重算
- [ ] resume 不重复计数
- [ ] 正式结果不静默覆盖
- [ ] test freeze 后的 prompt/config 可定位到 commit

---

## EXT-09 — 效率与成本

竞赛不只看精度，也应证明组合式方法不是不可用。

至少记录：

- 平均 Hy3 calls/sample；
- latency p50 / p95；
- Arbiter trigger rate；
- symbolic coverage；
- API/token/cost proxy（如果可获得）。

目标：

> 用确定性验证和 selective arbitration 换取可靠性，而不是简单“多调用几次 LLM”。

---

## EXT-10 — Confidence / Selective Review

置信度主要来自：

- verifier agreement；
- deterministic evidence；
- arbitration agreement；
- historical calibration（若实现）。

低置信样本 UI 标记“建议人工复核”。

**P1 最低：** High/Medium/Low 规则透明。  
**P2 可选：** ECE/Brier/selective risk curve。

---

## EXT-11 — 产品化 UI

最终应用建议三个页面：

### 1. Solve & Audit

- Problem
- Hy3 Solution
- Final Answer Verdict
- Step-level Audit
- First Root Error
- Error Type
- Evidence
- Unsupported Answer Warning

### 2. Benchmark Dashboard

- ProcessBench main table
- B0 vs Full
- Difficulty
- Error Distribution
- Unsupported Answer

### 3. Error Explorer

- sample id
- source
- difficulty
- error type
- final/process status
- baseline/full prediction
- evidence

**验收：**

- [ ] 所有数字从真实 result files 读取
- [ ] 不硬编码漂亮数字
- [ ] sample 可追溯
- [ ] UI 是结果展示层，不承担隐藏评测逻辑

---

## EXT-12 — 开源与安全

- API Key 只能来自环境变量；
- `.env` 不进入仓库；
- 数据许可/引用清楚；
- README 明确 Hy3 与数据集来源；
- 不上传不允许再分发的数据；
- 依赖版本锁定；
- clean clone 可运行 smoke。

---

# 6. P2 — Stretch Goals

只有 P0/P1 进入收口后才考虑：

- Calibration：ECE / Brier / selective accuracy；
- 第二位人工 reviewer 与更完整的 inter-rater analysis；
- Semantic mutations 扩展；
- 更多数学领域；
- latency/cost Pareto 图；
- Error Explorer 高级筛选；
- 自动生成 model card / evaluation card；
- 可选本地 Hy3-compatible endpoint 说明。

---

# 7. 核心术语冻结

## Final Answer Correct

最终答案通过独立 Answer Verifier。

## Process Correct

显式、可审计解题过程不存在足以破坏其逻辑成立性的错误。

## Earliest Error

按 step 顺序第一个**引入新的错误推断**的步骤。

## Root Error

可解释后续一组无效步骤的最早根因错误。

## Propagated Error

由于上游错误状态而失效，但当前步骤未引入新的独立根因。

## Independent Error

在已有错误之外又引入的独立错误。

## Unsupported Answer

`final_answer_correct=True && process_correct=False`。

## Process Issue Flag Rate

在没有过程 gold 的集合上，被 evaluator 标记有问题的比例。**它不是 Process Accuracy。**

## Process Classification Accuracy

只有存在过程 gold 时才能报告的 evaluator 分类准确率。

## False Positive Rate

`FP/(FP+TN)`，要求有 gold process-correct 负类集合。

## Flagged-set False Discovery Proportion

人工抽检的 flagged 集中：`FP/(real_issue+FP)`。这是官方“真实问题 vs 误报比例”最直接对应口径。

---

# 8. 项目文件与产物契约

推荐最终目录：

```text
mathxray/
├── app.py
├── README.md
├── pyproject.toml
├── .env.example
├── configs/
│   ├── default.yaml
│   └── formal_eval.yaml
├── docs/
│   ├── requirements.md
│   ├── evaluation_protocol.md
│   ├── milestones.md
│   ├── architecture.md
│   └── taxonomy.md
├── prompts/
│   ├── solver.md
│   ├── critic.md
│   └── arbiter.md
├── src/
│   ├── llm/
│   ├── solver/
│   ├── verifier/
│   ├── evaluator/
│   ├── benchmark/
│   └── analysis/
├── scripts/
│   ├── prepare_data.py
│   ├── generate_solutions.py
│   ├── run_processbench.py
│   ├── build_adversarial_bench.py
│   ├── run_ablation.py
│   └── generate_report.py
├── data/
│   ├── README.md
│   ├── manifests/
│   └── processed/
├── results/
│   ├── raw/
│   ├── parsed/
│   └── summaries/
├── reports/
│   ├── final_report.md
│   ├── manual_audit.csv
│   └── cases/
└── tests/
```

---

# 9. Award-Ready Definition of Done

## Gate A — Official Complete

- [ ] R1–R9 的 MUST 项全部完成
- [ ] R11–R20 全部完成
- [ ] R10 的实现选择有说明
- [ ] Hy3 应用独立可运行
- [ ] Demo <120s

## Gate B — Evidence Complete

- [ ] Direct Hy3 baseline
- [ ] ProcessBench 外部金标准结果
- [ ] TraceAdversarialBench controlled gold
- [ ] earliest-error Exact
- [ ] unsupported-answer 专项评测
- [ ] manual audit
- [ ] raw → summary 可重算
- [ ] 失败/parse/API 样本不隐藏

## Gate C — Scientific Credibility

- [ ] 正式 test 前冻结 prompt/config/taxonomy
- [ ] 主指标 95% CI
- [ ] Full vs B0 paired comparison
- [ ] 指标分母/公式公开
- [ ] FPR/FDP 命名准确
- [ ] 无过程 gold 时不伪称 Process Accuracy
- [ ] 至少一个模块经消融证明有效
- [ ] Full failure cases 被公开分析

## Gate D — Competition Ready

README 首屏 30 秒内能回答：

1. 为什么 final answer accuracy 不够？
2. MathXRay 是什么？
3. Hy3 在哪里被调用？
4. 哪个机制带来了改善？
5. 外部 benchmark 证明了什么？
6. 哪类问题仍然失败？
7. 如何一键复现？

Demo 能展示：

- Hy3 solution；
- earliest/root error；
- deterministic evidence；
- `Final ✓ / Process ✗`；
- 一张真实 benchmark 结果图/表。

---

# 10. Change Control

任何新增 feature 必须回答：

1. 对应哪个 R/EXT？
2. 改善哪个指标或官方交付？
3. 如何验证？
4. 失败时如何删除/回退？
5. 是否会推迟正式 benchmark？

若无法回答，默认不进入当前迭代。

---

# 11. Stop-Doing List

在正式 baseline 与 P0 闭环完成前，禁止把主要时间投入：

- 高级动画；
- 大规模多 Agent；
- 本地 Hy3 部署优化；
- 全量人工数据标注；
- 非核心领域扩张；
- 没有 benchmark 假设的新 verifier；
- 只为 README 好看而增加的复杂模块。

**竞争力优先级：**

> External Gold → Earliest Error → Unsupported Answer → Controlled Gold → Human Audit → Ablation → Reproducibility → UI Polish
