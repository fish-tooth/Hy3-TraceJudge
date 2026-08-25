---
name: P1-T08 产出第一张真实 ProcessBench baseline 表
overview: 运行 B0 Direct-Judge 编排脚本（真实 Hy3 API，smoke 20 条分层样本），从 raw JSONL 重算 M1–M5 指标，产出第一张可复现的 baseline 表及 run metadata。
todos:
  - id: prepare-env-credentials
    content: 确认 Python 依赖已安装，并配置真实 Hy3 凭证（.env 或环境变量的 HY3_API_KEY/HY3_BASE_URL/HY3_MODEL）
    status: completed
  - id: run-smoke-baseline
    content: 运行真实 smoke 编排脚本（python scripts/run_b0_baseline.py --stage smoke --provider hy3），必要时设置 HF_ENDPOINT 镜像并借助 resume 续跑
    status: completed
    dependencies:
      - prepare-env-credentials
  - id: verify-baseline-artifacts
    content: 校验 raw/summary/meta 产物，核对 M1-M5 与 per-source 基线表，并以相同签名重跑验证 resume 不重复计数
    status: completed
    dependencies:
      - run-smoke-baseline
---

## 用户需求

完成 P1-T08「编排脚本 + resume 测试，产出第一张真实 baseline 表」。经目录核查，P1-T05/T06/T07 及 P1-T08 的代码与测试均已实现且通过（157 项全绿），真正缺失的是 P1-T08 的产出物：`results/` 下三个目录为空，编排脚本从未实际运行。

## 已确认执行口径

- 产出方式：**真实 Hy3 API**（非 mock）。
- 运行规模：**smoke（20 条分层采样）**。

## 目标产出

运行 `scripts/run_b0_baseline.py --stage smoke --provider hy3`，得到第一张由 raw 重算而来的真实 baseline 表，包含：

- M1 Error Detection Recall、M2 First-Error Exact、M3 Correct Process Accuracy、M4 Process Status Accuracy、M5 Official Composite；
- 分 source（gsm8k/math/olympiadbench/omnimath）指标与 accounting（n_all、parse/API 失败、pred 缺失等）；
- raw JSONL、summary JSON、summary Markdown、run metadata 四类可追溯产物。

## 执行策略

本任务不新增或修改任何业务代码，直接复用已实现并测试通过的编排链路：

```
ProcessBench(default) → stratified_sample(20, seed=42) → to_canonical(1-based)
  → DirectJudge(Hy3Provider, 真实 API) → raw JSONL(append-only, resume)
  → recompute_metrics(M1-M5) → summary json/md/meta
```

核心命令（Windows PowerShell）：

```
python scripts/run_b0_baseline.py --stage smoke --provider hy3
```

脚本关键参数与行为（已核实源码）：

- `STAGE_SIZES = {"smoke": 20}`；`DATASET="Qwen/ProcessBench"`；`METHOD="B0-DirectJudge"`；
- raw 文件为稳定路径 `results/raw/B0-DirectJudge_smoke.jsonl`（不含 run_id，供 resume 复用）；summary/meta 为 `results/summaries/B0-DirectJudge_smoke_<run_id>.{json,md,meta.json}`；
- resume 以 `sample_id + method + run_signature` 去重，中断后可安全续跑，不重复消耗 API；
- 指标由 raw 记录重算（raw-first），不依赖内存状态。

## 前置条件与风险回退

1. **凭证**：仓库当前无 `.env`；`provider.model=null` 时脚本会对真实 provider 触发 `SystemExit`。需用户提供 `HY3_API_KEY`、`HY3_BASE_URL`、`HY3_MODEL`（写入 `.env` 或设为环境变量，`.env` 已被 `.gitignore` 忽略，密钥绝不入库）。
2. **依赖**：确认已安装 `datasets`、`openai`、`pydantic`、`sympy`、`pyyaml`、`python-dotenv`（见 `pyproject.toml`），缺依赖时按 `pyproject.toml` 安装。
3. **数据集网络**：首次运行会从 HuggingFace 下载 `Qwen/ProcessBench`；若不可达，设置 `HF_ENDPOINT=https://hf-mirror.com` 后重试（数据集缓存可复用，不重复下载）。
4. **API 失败**：单样本失败会被记为 `n_api_failure`/`n_parse_failure` 并写入 raw，不静默丢弃；重跑时 resume 仅补失败样本。

## 验收标准

- `results/raw/B0-DirectJudge_smoke.jsonl` 含 20 条 self-contained 记录（gold + prediction + provenance）；
- `results/summaries/` 下存在对应 run 的 `.json`/`.md`/`.meta.json`；
- summary 中 `n_all=20`，M1–M5 按分母有效情况有值（分母为 0 时如实为 None），accounting 计数完整；
- 相同 signature 重跑时 `n_new=0, n_resumed=20`，验证 raw→metric 可重算且 resume 不重复计数。