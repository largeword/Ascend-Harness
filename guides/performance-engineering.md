# 从性能证据到可验收的优化

先找到当前执行路径的主要成本，再提出减少实际工作或暴露等待的改动。压缩比、算子名字、较少指令或更大的驻留 batch 都不是端到端收益。

**与 CANNBot 共存时，性能协议、基线身份、有效收益分类、采集角色与最终验收以当前适用流程为准。** 下文的公式和反例用于解释证据，不能替代平台的采集脚本、抖动规则或完整用例门。没有适用的平台流程时，才在 standalone 合同中自行确定这些参数。详见[兼容审计](../provenance/cannbot-compatibility.md)。

## 先闭合成本账

对稳态生成，可以用 `有效吞吐 ≈ 实际 decode batch × 每请求每步有效输出 / step 时间` 组织证据。speculative decoding 的接受率与额外工作必须一起计入。完整服务还包含混合 prefill、爬坡、排空和客户端等待，不能把稳态倍率直接外推到整轮。

分别记录：

- 容量：压缩 payload、metadata、精确窗口、workspace、缓存快照、临时缓冲与模型其他常驻内存。
- 搬运：实际 GM 地址访问、L2/HBM 流量、DMA、重排和展开；GM 逻辑字节不等于 HBM 实际传输。
- 计算：Cube、Vector、标量、量化/反量化以及每有效输出的额外工作。
- 协议：producer/consumer 所有权、等待、跨核发布、图与生命周期限制。

“不要全历史恢复”可迁移为避免每步额外物化整个高精度历史的设计审查点，不是声称精确 attention 无需读取全部压缩历史。复杂度、存储容量和流量是三个口径。

依据：`skills/oscar-quant-optimization/SKILL.md`、`references/experiment-template.md`、`docs/quant_dequant_roofline_20261011.md@fdb8eba9`；复杂度澄清见 `docs/checklist.md@7047ce36`。

## 有效的收益预测需要正确分母

局部倍率 `S_op = t_base / t_new` 只属于该完整算子或路径。只有互斥、串行且不重复计费的阶段，才可写 `T_new = T_fixed + Σ(N_i × t_i_new) + 新增开销`。流水按依赖图关键路径计算，不把相互重叠的 actor、rank 和父子阶段求和。

若只可优化当前 wall 的份额 `f`，理想上限为 `1/(1-f)`。这个上限要求份额定义有效；不知道频度、重叠或稳态占比时，只能给条件区间及缺证项。先由已有基线校准成本模型，再预测候选；不能为了命中目标倒调份额。

组合优化的本轮增量按最新已接纳基底核算绝对节省与新增成本；累计和最终收益仍绑定最初冻结的基线，不能用上轮基线替换。避免把独立倍率相乘或重复计入同一项改善。共存模式直接引用平台生成的本轮与累计 effect，不另算竞争口径。正确性修复可以是必要依赖，但不能凭推断领取性能倍率。

依据：`skills/oscar-quant-optimization/references/experiment-template.md@fdb8eba9`。

## 保持测量与被测对象可辨认

配对比较固定模型、输入、输出上限、并发、采样、种子、cache 状态、token 预算、调度、图模式及有效 argv。改参数提高吞吐属于另一项实验，不能冒充同配置算法优化。

记录源、构建、算子、PT/权重、配置与工作量身份。原始基线、候选和诊断 clone 应可区分。诊断同步、完成栅栏、profile 和观察 copy 都可能改变重叠与时间；按适用协议保留控制组，不把额外诊断插桩结果写成生产速度。平台指定 profiling 为正式采集/分析依据时，沿用其协议，不用裸 wall-clock 或本指南的一般建议取代。

平台若把一次目标调用的多个 kernel 时间之和定义为算子 `total_us`，保留该度量与名称；它不自动等于流水关键路径或客户端端到端延迟。不同层次的量分别报告，不互相改名。

`AI_CORE` 标签不证明纯 Cube 执行；Vector softmax/归约或混合 Cube/Vector 不自动代表回退。实际 engine、operator type、shape、dtype 各字段分别保留，缺失时保持未知。多 rank task 时间和不能当 TP wall 延迟。

依据：`docs/attention_pipeline_breakdown_20261113.md`、`docs/timer_32k_diagnosis_20261019.md@fb1a5078`。

## 小改动也要覆盖组合回归

调试时按风险选择短/长、单/多请求、prefill/decode/mixed、cache 命中/未命中、tail 和 MTP 边界；这些最小反例不能替代平台要求的最终功能/性能全集、每目标 SoC 验证和回集成检查。短输入可能主要走 decode/小 query，长输入主要走大 prefill；同一转换优化对两阶段的收益可能相反。

源工程按真实执行阶段组合分别已有验收记录的源码，目标是同时保护短输入与长输入，没有根据输入长度临时挑一个版本。旧版本的单项通过不代表新组合已通过，两类场景仍需复验。迁移时可保留对内核源身份的检查，但应检查真实调用链并说明允许变更的粒度；哈希门不能代替数值与性能验证。

UB/L1/GM 预算需计入 SDK workspace 与用户 buffer，尾块与并行实例也计入。去掉初始化、等待或拷贝前，先证明其发布与所有权职责确实由别处满足；“发射次数少”不保证净加速。

依据：`docs/universal_regression_repair_20261028.md@fdb8eba9`、`docs/attention_pipeline_breakdown_20261113.md@fb1a5078`。

## 评测统计也是性能合同的一部分

重复实验要记录全部运行与失败。Standalone 或业务 benchmark 合同可以预先确定均值、top-k、tie 规则和选取指标；共存模式已经有规定的性能聚合和抖动处理时，直接采用该规定，不能用业务 accuracy 的 top-k 统计替代。某个整体 accuracy 选出的 top-k，如果要同时比较类别指标，应使用同一组选中的 runs。top-k 均值是指定的选择统计，不能称为全部 runs 均值。

未完成轮次、缺失指标和错误记录不能变成零，也不能自动追加新样本直到凑出理想结果。改变评分器或输出上限后得到的改善属于新指标/新任务，不等于原合同下的模型修复。已完成的评测在身份、覆盖和有效性满足当前要求时优先复用；不能用“已有结果”跳过平台要求的最终重采、全集验收或新身份验证。

依据：`docs/sink_recent_sweep.md@e43819c2`、`docs/accuracy_regression_20261031.md@ea46d233`。
