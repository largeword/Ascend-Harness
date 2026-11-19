# 分支覆盖与来源边界

审计快照：2026-11-19。已刷新远端跟踪分支，覆盖全部 9 个本地分支与 8 个 origin 分支，共 17 个 ref、9 个不同 tip。`origin/HEAD` 是符号别名，不计为独立分支。机器可读清单见 [branches.json](branches.json)。

这是各分支 tip 的目录、入口 blob 和相关文档重点审计；没有声称逐行审计所有历史 commit 或所有源码。相同 tip 合并阅读，所有 ref 仍逐项列出。当前同名本地/远端 SHA 一致；两个本地 backup 保存不同历史快照，不能把它们写成远端现行规则。

## 全部分支

| Ref | Commit |
| --- | --- |
| `refs/heads/backup/oscar-bf16-attention-before-gitcode-20261109` | `e70d7846dc2396dbeff8049980483ff8504ed8c8` |
| `refs/heads/backup/pre-bf16-merge-20261027` | `26cf6dc40ee2182903d176a2fea1cfc41ecb579a` |
| `refs/heads/checkpoint` | `fdb8eba90522bd8942333bc27472bb3e6808649b` |
| `refs/heads/codex/add-offload` | `59f08592e59a8e1bfa663d1e45f4f64965e97efa` |
| `refs/heads/codex/oscar-ascend` | `7047ce36a19e001046a07a7d85de2a4092cd7941` |
| `refs/heads/codex/oscar-bf16-attention` | `fdb8eba90522bd8942333bc27472bb3e6808649b` |
| `refs/heads/codex/oscar-bf16-sink1024-recent2048` | `ea46d233e392930aa6b13513f44db9da8335ada2` |
| `refs/heads/codex/oscar-perf-profile` | `fb1a507882009f884ea81ae79e213b49d5ded971` |
| `refs/heads/codex/oscar-sink-recent-sweep` | `e43819c24eb05419f99f394bf38812df10533790` |
| `refs/remotes/origin/codex/add-offload` | `59f08592e59a8e1bfa663d1e45f4f64965e97efa` |
| `refs/remotes/origin/codex/aisbench-stable` | `f96820f154f62686c319edba5ac31e52a20bad4e` |
| `refs/remotes/origin/codex/oscar-ascend` | `7047ce36a19e001046a07a7d85de2a4092cd7941` |
| `refs/remotes/origin/codex/oscar-bf16-attention` | `fdb8eba90522bd8942333bc27472bb3e6808649b` |
| `refs/remotes/origin/codex/oscar-bf16-sink1024-recent2048` | `ea46d233e392930aa6b13513f44db9da8335ada2` |
| `refs/remotes/origin/codex/oscar-perf-profile` | `fb1a507882009f884ea81ae79e213b49d5ded971` |
| `refs/remotes/origin/codex/oscar-sink-recent-sweep` | `e43819c24eb05419f99f394bf38812df10533790` |
| `refs/remotes/origin/data-exchange` | `fdb8eba90522bd8942333bc27472bb3e6808649b` |

## 每个不同 tip 的提炼重点

### `e70d7846`

历史备份：BF16 合同、诊断与生产测量隔离，截止该 tip 的精度/性能边界。

重点阅读（仅引用源仓库路径；文件不随本仓库复制）：

- `AGENTS.md@e70d7846`

### `26cf6dc4`

合并前历史备份：解释器能力发现、数值链与 cache checkpoint 保留。

重点阅读（仅引用源仓库路径；文件不随本仓库复制）：

- `docs/python_environment.md@26cf6dc4`

### `fdb8eba9`

主 BF16 基底：真实 prefill 状态协议、短长输入性能保护与数值合同；checkpoint/data-exchange 同树别名。

重点阅读（仅引用源仓库路径；文件不随本仓库复制）：

- `docs/universal_regression_repair_20261028.md@fdb8eba9`
- `docs/gdn_prefill_state_20261028.md@fdb8eba9`
- `docs/official_math_v4_20261021.md@fdb8eba9`
- `skills/oscar-quant-optimization/references/experiment-template.md@fdb8eba9`

### `59f08592`

Offload 分支：异步所有权、总内存预算、持久化发布、bounded recorder 与故障保码。

重点阅读（仅引用源仓库路径；文件不随本仓库复制）：

- `docs/kv_offload_memcache.md@59f08592`
- `docs/offload_guard_incident_20261110.md@59f08592`
- `docs/host_shm_startup_20261110.md@59f08592`

### `7047ce36`

基础 Ascend 分支：档案驱动、分层 checklist、候选入口一致性、配对性能因果。

重点阅读（仅引用源仓库路径；文件不随本仓库复制）：

- `oscar_ascend_agent_start.md@7047ce36`
- `docs/checklist.md@7047ce36`

### `ea46d233`

固定窗口与质量诊断：评测身份、原评分合同、图观察器覆盖、CPU 并行的阶段边界。

重点阅读（仅引用源仓库路径；文件不随本仓库复制）：

- `docs/service_precision_round_20261105.md@ea46d233`
- `docs/accuracy_regression_20261031.md@ea46d233`
- `docs/install_serve_cpu_parallelism.md@ea46d233`

### `fb1a5078`

独立 profile 分支：从其他分支选择性移植，诊断 clone、混合引擎 ABI、离线统计与性能归因。

重点阅读（仅引用源仓库路径；文件不随本仓库复制）：

- `skills/oscar-quant-optimization/SKILL.md@fb1a5078`
- `docs/standalone_perf_profile_20261112.md@fb1a5078`
- `docs/internal_recorder_linkage_20261113.md@fb1a5078`
- `docs/attention_pipeline_breakdown_20261113.md@fb1a5078`
- `docs/longbench_length_stats.md@fb1a5078`

### `e43819c2`

窗口 sweep 分支：owned endpoint、隔离工作目录、完整重复次数、显式 top-k、resume 身份。

重点阅读（仅引用源仓库路径；文件不随本仓库复制）：

- `docs/sink_recent_sweep.md@e43819c2`

### `f96820f1`

Stable 分支：启动参数固定、默认与显式 cache 开关、真实 prefill 尾段及 MTP 状态协议。

重点阅读（仅引用源仓库路径；文件不随本仓库复制）：

- `docs/aisbench_stable.md@f96820f1`

## 如何使用来源证据

源仓库各 tip 均有同一个项目专用技能 `skills/oscar-quant-optimization/SKILL.md`，共 3 个不同 blob 版本；它的工程专属适用范围和历史覆盖规则说明，不适合原样安装到其他项目。本仓库重写为通用工作流，并保留来源定位。

使用 source commit + 相对路径在合法持有的源仓库中定位事实，不依赖会移动的分支名或过时行号。文档中的记录只代表其声明的验证层，旧结果不能自动证明新组合。源日志、模型数据、机器路径、用户信息、第三方实现与运行时状态均未复制。

`guides/` 的方法是跨分支归纳；涉及具体数值、硬件、命令权限、窗口、PT 配方与验收阈值的内容已经参数化或只描述其规则。没有移植项目原始内核、调度器或缓存实现。
