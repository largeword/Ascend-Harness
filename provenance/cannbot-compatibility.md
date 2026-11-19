# CANNBot 共存审计与职责划分

审计日期：2026-11-19。范围是本机可见的当前安装快照与本仓库指南/模板；未运行优化、构建、设备采集或验收工作流，未更新 CANNBot，也未复制其工作流、技能实现或全文。

**结论：CANNBot 已经覆盖通用编排、角色、状态和验收的大部分职责。** 对命中其适用范围的任务，使用当前适用入口作为这些职责的唯一权威；Ascend-Harness 只补充本项目积累的反例、证据解释和部署经验。没有适用工作流时，本仓库的通用流程及模板才作为 standalone 起点。不得因为安装了某个插件，就让所有插件同时接管一个任务；先按其入口判断适用范围。已有用户授权和更高优先级要求仍有效。

## 比对来源与版本边界

以下 `plugins-official/...` 均为本地平台仓库内的相对路径；`.codex/...`、`.agents/...` 为源项目内的相对路径。标注的行号属于本次审计快照，未来升级应按真实路径和内容重新定位。

| 来源 | 本次观察 | 版本含义 |
| --- | --- | --- |
| 当前平台仓库 | commit `6fa859d65581d646241657b7764ee73a068edd64`，工作树无改动 | 只标识此仓库中实际读取的文件，不代表所有已安装副本 |
| `.codex/AGENTS.md` | 链接至 `plugins-official/torch-compile/AGENTS.md` | 当前入口读取到的是上述仓库内容 |
| `.codex/workflows` | 链接至 `plugins-official/ops-perf-optimize/workflows` | 此目录的文件由当前仓库提供 |
| `.agents/skills/ops-perf-optimize-workflow/SKILL.md`、`ops-perf-acceptance-criteria/SKILL.md` | 经技能目录链接解析到对应 `plugins-official/ops-perf-optimize/skills/...` | 以实际解析文件为准，不能只看安装清单日期 |
| `.agents/skills/ops-direct-invoke-flash/SKILL.md` | 经技能目录链接解析到对应 `plugins-official/ops-direct-invoke-flash/skills/...` | 与本次仓库内容一致 |
| `.codex/cannbot-plugin.json` | 记录应用 commit `1c0a78d30bd0bc735223d86fedde7e573692c103`、skills revision `d075d3735535399d7fc6a5fa18b43191bb1546a9` | 这是安装来源记录，不能覆盖已经移动的链接实际内容 |
| `.agents/skills/model-infer-profiling/SKILL.md` | 是源项目本地文件；SHA-256 `226d8b4d0b2889afde1e31ded6f8fe35c1be9b4664a7aebeaf327f4b557238fb` | 不将其归入当前平台仓库 commit；本报告未审计全部原子技能副本 |

因此这是一个有链接与本地副本并存的快照，不能用单一“已安装版本”概括。本次对模型编排的比较来自当前平台仓库可见的入口与 workflow，不据此断言所有模型技能副本已同步。

关键流程文件的内容身份：

| `plugins-official/` 下的路径 | SHA-256 |
| --- | --- |
| `torch-compile/AGENTS.md` | `e27f7843a2d04dadb7692e0a97708c357f5e6757fa82e0c96983db1d11e423d3` |
| `ops-perf-optimize/skills/ops-perf-optimize-workflow/SKILL.md` | `bd364239d7aedc38ffd6ef4ba6fb07ca6e30211b0cca51d126508ca41336f10d` |
| `ops-perf-optimize/skills/ops-perf-optimize-workflow/references/workflow-contract.md` | `42845983c4cc386a382f21ce0779d9500db12cd43f118e991c58af6a0bf2d620` |
| `ops-perf-optimize/skills/ops-perf-acceptance-criteria/SKILL.md` | `84f6141b50d2dd3ecd4ed49f4bead7e1578cedde1e4732f038578fb2cedf981d` |
| `model-infer-optimize/workflows/optimize-workflow.md` | `fa24cf75dc88ee1459cfc3f96d2280dc6f25e85677c6c11375d2210e45bd288a` |
| `model-infer-optimize/workflows/sota-approach-workflow.md` | `f8b71a2413c0eabf84a2650a50cfdbb88bf9194520ff1bda655ee5505559726a` |
| `ops-direct-invoke-flash/skills/ops-direct-invoke-flash/SKILL.md` | `e7426f5325b881df8800ddab10edf274655f0e7d1865c9259d67bf0a461f2aa6` |

## 重复、潜在冲突与处理

以下是职责和规则映射，非平台规则的替代副本。共存时应读取当前平台文件，不能据此摘要重建其工作流。

| 项目 | 原通用设计的风险 | 平台依据：相对路径与行号 | 处理方式 |
| --- | --- | --- | --- |
| 主流程与触发 | 通用“分析→实现→验证”闭环可能抢占任务或省略必需阶段 | `ops-perf-optimize/AGENTS.md:15–28`；`ops-perf-optimize/skills/ops-perf-optimize-workflow/references/workflow-contract.md:31–47`；`model-infer-optimize/AGENTS.md:31–54` | 通用闭环仅用于 standalone。共存时先按平台入口路由，不因关键词或报告分析请求启动完整优化 |
| 角色与并行 | 通用任务书允许分析/实施并行，可能越过固定阶段或让 primary 直接实施 | `model-infer-optimize/workflows/optimize-workflow.md:23–29`；`model-infer-optimize/workflows/sota-approach-workflow.md:77–84`；`ops-perf-optimize/skills/ops-perf-optimize-workflow/references/workflow-contract.md:9–19` | 角色权限、派发模板、共享上下文路径和并行边界沿用平台；本仓库的事故线索写进指定上下文，不额外扩展受限派发信封 |
| 确认节点 | “减少确认”若被理解为跳过分析后的方案确认，会违反模型基础流程；反过来统一增加确认也会重复已有授权 | `model-infer-optimize/workflows/optimize-workflow.md:17–29,198–207,278–280`；`ops-perf-optimize/skills/ops-perf-optimize-workflow/SKILL.md:14`；`torch-compile/AGENTS.md:46–67` | 保留适用流程的未满足确认点，复用其认可的既有确认，不凭通用指南额外增加或删除确认 |
| 第二套状态 | `evidence.json`、实验卡和通用台账可能与平台状态分别宣布“完成” | `ops-perf-optimize/skills/ops-perf-optimize-workflow/references/workflow-contract.md:7,94–102`；`model-infer-optimize/workflows/sota-approach-workflow.md:83–88`；`ops-direct-invoke-flash/skills/ops-direct-invoke-flash/SKILL.md:151–158` | 平台状态为唯一权威。共存模式只引用状态/证据及身份，补充反例不维护独立任务完成状态；通用 gate 模板保留给 standalone |
| 精度失败分类 | 通用 pass/fail 无法完整表达已确认且未恶化的基线失败，容易变成无条件通过或全局阻塞 | `ops-perf-optimize/skills/ops-perf-acceptance-criteria/references/precision-policy.md:3–18` | 保留平台原始分类与条件，不把 `conditional_pass` 改写成 `pass`；候选失败、基线失败、未诊断状态按平台分别处理 |
| 数值合同 | “数学变化另建合同”可能被误用为在优化任务中自行换 dtype/golden/阈值 | `ops-perf-optimize/skills/ops-perf-optimize-workflow/references/workflow-contract.md:45–47,86–88` | 尊重适用流程冻结的公开接口、dtype、golden、阈值和 scope；合同变化交回其决策节点，不用通用模板为既有失败重新定门 |
| 性能采集与汇总 | 空白的 warmup/重复/聚合模板可能覆盖平台规定协议；只看当前基底会漏掉累计口径 | `ops-perf-optimize/skills/ops-perf-acceptance-criteria/references/performance-collection.md:3–11`；`performance-jitter-policy.md:3–26,44–69`（同一 references 目录） | 使用平台采集、有效收益和 effect 工件；本轮对当前基底，累计/最终对原始冻结基底。通用公式只解释单位，不重算竞争指标 |
| 必需验证与结束条件 | 最小反例、风险选例或复用已有 benchmark 可能被当作最终验收替代 | `ops-perf-optimize/skills/ops-perf-optimize-workflow/references/workflow-contract.md:49–70,104–112`；`model-infer-optimize/workflows/sota-approach-workflow.md:193–217` | 最小检查用于诊断；平台要求的完整集合、目标 SoC、回集成或最终重采不能省略。复用需满足身份、覆盖与有效性要求 |
| 不同流程的局部例外 | 统一套用“必须全串行/必须多 Agent 评审”反而覆盖 Flash 的快速路径 | `ops-direct-invoke-flash/skills/ops-direct-invoke-flash/SKILL.md:73–125` | 按实际入口的复杂度与配置执行；共存声明不把一种平台流程的细节强加给另一种 |

四篇指南已增加模式边界，并修订派发上下文、并行、精度分类、累计基线、性能证据和最终覆盖表述。根入口、模板及工具应保持同一委托关系：其检查通过只能说明自身检查范围，不能覆盖平台未通过的 gate 或替平台宣布完成。

## 六个补充技能的路由映射

这里比较语义职责，不将“名字不同”视为没有重复。源项目中的实际技能文件位于 `.agents/skills/<技能名>/SKILL.md`；下表的短 hash 是本次读取文件的 SHA-256 前 12 位。它们可能是本地副本或经目录链接解析的文件，不能统一套用平台仓库 commit。仅核实文件身份不表示本次执行过该技能。

| Harness 技能 | 平台已有职责与来源身份 | 共存处理与保留范围 |
| --- | --- | --- |
| `ascend-source-build` | `ops-direct-invoke`（`5c392ba4b334`）、`workflow-orchestrator`（`980f6c398140`）、`repo-build-guide`（`f13103ca0518`） | 规格、开发流程和构建路线交给适用的平台入口；只补充源码→构建→实际加载身份链与已有事故反例，不另造构建编排 |
| `ascend-precision-contract` | `ops-precision-standard`（`09fdb58767c3`）、`ascendc-precision-debug`（`d50b95191182`）、`model-infer-precision-debug`（`d42e41795e0f`） | 精度标准、比较器、失败分类和调试流程服从选中入口；保留完整数值链、舍入位置及局部代理不能替代模型质量的案例 |
| `ascend-graph-state` | `model-infer-graph-mode`（`eabd0a51cd06`）、`model-infer-kvcache`（`c4abc5b7514c`）及当前 `torch-compile` 入口 | 图模式选路、配置与诊断交平台；补充真实 prefill 与短形状、已提交状态、缓存生命周期和 capture/replay 分层证据的反例 |
| `ascend-performance-experiment` | 当前 `ops-perf-optimize-workflow` / `ops-perf-acceptance-criteria`（身份见上表），`model-infer-perf-breakdown`（`3c23d1a7a189`）、`model-infer-profiling`（`226d8b4d0b28`） | 采集、kernel trace 拆解、候选选择和验收归平台；只补充容量与吞吐因果、跨 rank/阶段误计和业务 benchmark 分母解释 |
| `ascend-deployment-triage` | `ascendc-env-check`（`c50e4af38997`）、`ascendc-crash-debug`（`ee6e9913df92`）、`model-infer-runtime-debug`（`72d18ebeb59e`）及当前图模式 triage 入口 | 环境、算子 crash、模型运行与图故障分别交适用平台技能；保留 owned endpoint、原始退出码、相位日志、进程组清理与离线证据归属 |
| `ascend-offline-benchmark` | 本次检查范围内未发现等价的 AISBench 逐样本、多 run、长度 bin 离线统计能力 | 可保留：结果发现、token 长度来源、run 等权/pooled 区别、未作答与错误记录、覆盖率。kernel trace 分析交平台 `model-infer-perf-breakdown`；不能把“未发现”等同于穷尽平台全部能力 |

不同平台入口之间也可能对主角色、确认、流程或标准有不同规定。本仓库不自行仲裁这些局部差异，更不拼接一套新规则；按实际任务选中的当前入口及其引用链执行。

## 安装与自动触发处置

旧安装方式默认把六个技能注册到 `.agents/skills/`。检查未发现与平台技能同名覆盖，但这些技能的 description 会覆盖相近意图，仍存在语义重复和竞争触发风险。

当前安装策略将默认目标改为 `.harness/`，仅作为参考资料，不注册为自动匹配的 agent 技能。`--register-skills` 只用于独立工程；检测到本地平台标记时拒绝注册。检测到旧 Harness 注册时，在写入前报错并列出待处理位置，不自动删除已有技能。这样既避免新增并行入口，也不在迁移过程中修改平台安装或用户旧文件。

交付验证汇总：18 项主机测试及模拟安装通过，覆盖此次安装与兼容规则的主机行为。这不代表所有平台插件组合、真实任务路由或 NPU 工作流均已验证；本次未运行平台优化或设备验收。

## 保留的补充价值

这些内容是源工程自己的经验摘要，可作为平台工作流的案例输入，而不需要再造平台已有职责：

- **阶段与形状不等价**：短 query 仍可能是真实 prefill；检查已提交状态、最终发布及下一轮读取，见[验证与调试](../guides/validation-and-debug.md)。
- **诊断代码也有 ABI 风险**：混合引擎同名 helper 的布局与链接需要产物证据；本地反汇编不能冒充现场精确符号化。
- **服务归属与清理**：benchmark endpoint 必须指向本次拥有的服务；保留原始错误，清理仅限 owned 资源，见[部署与分析](../guides/deployment-and-analysis.md)。
- **多轮评测的统计分母**：业务 accuracy 的 run 均值、pooled 均值、未作答、错误记录和 token 覆盖率要分开；这些不替代平台算子性能聚合协议。
- **压缩容量与真实吞吐的因果**：区分驻留 batch、有效输出、step 时间、展开成本及混合阶段，见[性能工程](../guides/performance-engineering.md)。
- **跨分支经验的可追溯性**：[分支来源](branches.md)保留 source commit 与路径、历史目标覆盖关系和未验收边界，避免将旧项目参数迁移为通用规则。

## 本次检查的限制

本报告确认文档和流程职责的兼容边界；主机测试覆盖上述安装行为，不声明所有平台版本和技能组合均已兼容，也不构成真实设备验收。链接和本地副本可能分别升级；使用时解析实际入口，核对适用流程及内容身份。若出现新冲突，更新引用和补充说明，保留平台当前适用规则为准，不能靠本仓库一份静态摘要锁死平台版本。
