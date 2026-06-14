# 抖音数据内容分析项目

本项目按“真正产品”的思路，完成了一版抖音公开内容研究方案，覆盖产品调研、数据采集报告、分析技术报告、样例数据、分析脚本、阶段总结和导师周报。

这是一版研究型 MVP，重点是把任务完整跑通，而不是直接提供绕过平台限制的抓取器。首版输入采用“公开可见页面内容的人工留存/研究快照 + 统一结构化解析”的方式，不依赖官方 API，也不包含获取真实 IP、绕过风控、批量规避限制等高风险能力。

## 目录结构

```text
抖音数据/
├── README.md
├── docs/
│   ├── 01_产品调研与需求分析.md
│   ├── 02_数据抓取报告.md
│   ├── 03_分析技术报告.md
│   └── 04_下一步优化方案.md
├── reports/
│   ├── 01_阶段总结_产品调研.md
│   ├── 02_阶段总结_数据采集.md
│   ├── 03_阶段总结_分析建模.md
│   ├── 04_阶段总结_交付整理.md
│   └── 周报_抖音数据项目_v1.md
├── data/
│   ├── raw/
│   │   ├── manual_capture_template.json
│   │   └── sample_public_douyin_dataset.json
│   └── processed/
├── scripts/
│   └── analyze_public_douyin.py
└── outputs/
    ├── analysis_report.md
    └── analysis_summary.json
```

## 交付内容

1. `docs/01_产品调研与需求分析.md`
   明确目标用户、核心场景、价值主张、MVP 功能和成功指标。
2. `docs/02_数据抓取报告.md`
   说明首版研究流程中可采集的数据字段、采集边界、字段价值、规范化存储方案和限制。
3. `docs/03_分析技术报告.md`
   说明首版分析目标、方法、指标和结果读取方式。
4. `docs/04_下一步优化方案.md`
   给出后续在数据、模型、流程和产品层面的优化路线。
5. `scripts/analyze_public_douyin.py`
   可直接运行的首版分析脚本，输入统一格式的公开数据样例，输出 Markdown 报告和 JSON 汇总。
6. `reports/*.md`
   每个阶段单独总结，另附一份可直接汇报导师的周报。

## 快速开始

在当前目录运行：

```bash
cd /mnt/c/Users/Nxersty/Desktop/抖音数据
python3 scripts/analyze_public_douyin.py \
  --input data/raw/sample_public_douyin_dataset.json \
  --markdown outputs/analysis_report.md \
  --json outputs/analysis_summary.json
```

运行后会生成两类结果：

1. `outputs/analysis_report.md`
   面向汇报阅读的分析结论。
2. `outputs/analysis_summary.json`
   面向程序消费的结构化摘要。

## 操作流程

1. 先阅读 `docs/01_产品调研与需求分析.md`，确定分析场景与目标用户。
2. 再阅读 `docs/02_数据抓取报告.md`，明确首版能拿到哪些公开字段、如何留存、如何结构化。
3. 准备数据：
   使用 `data/raw/manual_capture_template.json` 的字段结构，整理你自己的研究样本；也可以直接先用 `sample_public_douyin_dataset.json` 跑通流程。
4. 运行分析脚本，得到初版结果。
5. 对照 `docs/03_分析技术报告.md` 和 `docs/04_下一步优化方案.md`，评估需要优化的是数据、模型还是目标定义。
6. 汇报时优先使用：
   `reports/01_阶段总结_产品调研.md`、
   `reports/02_阶段总结_数据采集.md`、
   `reports/03_阶段总结_分析建模.md`、
   `reports/04_阶段总结_交付整理.md`、
   `reports/周报_抖音数据项目_v1.md`。

## 首版研究边界

1. 只讨论公开可见内容的研究型采集与分析。
2. 不提供真实 IP 获取能力，只保留页面若公开展示的 `IP属地标签` 一类字段。
3. 不提供绕过平台安全机制、批量规避限制或攻击性抓取方案。
4. 样例数据已经做了脱敏和合成处理，目的是演示方法链路，而不是复原真实用户身份。

## 建议的下一步

1. 用真实研究样本替换 `sample_public_douyin_dataset.json`。
2. 在获得合规授权的前提下扩充采样范围，覆盖更多事件和作者类型。
3. 将规则法升级为“规则 + 监督模型/大模型”联合分析，提高情感和立场识别准确率。
