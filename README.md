# Hy3-TraceJudge

> Hybrid Process Verification and Root-Cause Error Localization for Mathematical Reasoning with Hy3

**Can a correct answer still be wrong?**

Hy3-TraceJudge 基于 Hy3 构建数学推理解题与审计应用：它不仅验证最终答案，还判断推理过程是否成立、定位 earliest error、归类错误，并识别"最终答案正确但过程无法支撑结论"的样本。

## 项目状态

- **当前阶段**：Phase 0–1（实验地基 + Hy3 Direct Judge × ProcessBench baseline）
- **Single Source of Truth**：`docs/requirements.md`、`docs/evaluation_protocol.md`、`docs/milestones.md`

## 目录结构

```
src/          # 源码（llm / solver / verifier / benchmark / evaluator / analysis）
tests/        # pytest 单元测试
scripts/      # 运行脚本（preflight / baseline / 数据准备）
configs/      # YAML 配置
prompts/      # prompt 模板（版本化）
data/         # 数据集（raw / processed）
results/      # 实验产物（raw / parsed / summaries）
reports/      # 分析报告
docs/         # 规范文档
```

## 快速开始

环境搭建与运行命令见 `pyproject.toml`、`configs/default.yaml` 与 `scripts/`。

## Hy3 集成

- API key 仅来自环境变量（`HY3_API_KEY`），绝不硬编码或提交 `.env`。
- 配置见 `configs/default.yaml` 与 `.env.example`。
