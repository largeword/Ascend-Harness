# 部署、资源所有权与离线分析

可移植的交付应是一条参数明确、结果可追踪的入口。用户不应为了定位脚手架错误而手工执行一串相互依赖的实验。

**与 CANNBot 共存时，本指南仅补充部署与分析的工程检查。** 执行阶段、角色、确认点、设备调度和验收范围由当前适用工作流决定；本指南不自动启动新工作流，也不替代平台状态或证据。没有适用的平台流程时，才据此设计 standalone 入口。详见[兼容审计](../provenance/cannbot-compatibility.md)。

## 配置与能力发现

按实际 import/工具能力发现 Python 和编译环境，探测放入有超时的隔离进程。显式指定的解释器不合适就失败，不能静默换成另一个环境。CPU 测试依赖可用，不代表 NPU 服务栈可用；模块 import 成功，也不代表设备可执行。

设备、SOC、模型、端口、缓存与内存预算均来自显式配置。只在本地生成的编辑器配置中写环境路径，不能通过屏蔽 missing-import 提示掩盖选择错误。API 和 ABI 以实际 SDK/框架版本验证，不能把一台机器验证过的名字当作所有 Ascend 型号通用规则。

依据：`docs/python_environment.md@26cf6dc4`、`oscar_ascend_agent_start.md@7047ce36`。

## 一键入口必须管住失败与清理

每个阶段实时转发 stdout/stderr，同时保存相位日志、命令、时间和真实退出码。安装、构建、必要校准、验证、清理与正式服务之间的失败关系要明确；这些部署环节不是替换平台阶段的另一套流程。未经验证不能打印 READY；直接启动入口不运行 probe 时，要说明它不产生验收证据。

只清理本次入口创建的进程组、端口和文件。启动前拒绝占用端口，成功、失败、超时和中断都验证资源释放。首个错误保留为主错误，清理或记录失败另列；清理无法确认时，不启动下一组冲突实验。

benchmark 客户端必须绑定当前脚本实际拥有的服务，保存生效 endpoint 和模型标识。不要继承一个旧远端地址，让本地候选闲置而评测另一服务。用生成的隔离配置覆盖 endpoint，不改安装目录中的原 benchmark 配置。

依据：`docs/service_precision_round_20261105.md@ea46d233`、`docs/sink_recent_sweep.md@e43819c2`、`docs/checklist.md@7047ce36`。

## CPU 并行要按阶段和总预算管理

工作流允许时，独立文件读取、解析、离线分析和构建可并行。固定阶段、评审 barrier 与设备排他采集仍按平台要求执行。先按 affinity、容器 quota、内存和并行 worker 数确定有效总预算，避免每个 TP worker 都领取整机线程数，再叠加 OMP/BLAS/PyTorch 池。

准备、启动和 warm-up 的线程策略不应无条件沿用到请求阶段。需要恢复原生请求策略时，成功和失败都恢复；同时验证图捕获与运行时线程设置兼容。相同输入的解析、哈希、tokenizer 初始化和拟合可在身份有效时复用，但不能共享可变的实时 KV/GDN 状态来冒充独立实验。

并行化需要串行/并行结果一致、资源上界、异常传播和恢复测试。配置线程数并不等于已经测得提速。

依据：`docs/install_serve_cpu_parallelism.md`、`docs/service_precision_round_20261105.md@ea46d233`。

## 缓存与 offload 的通用所有权检查

外部适配尽量保留上游分配、hash/lookup 和生命周期；引用保留与数据复制分别计账。跨请求复用、异步 save/restore 和多 rank 发布，应检查 generation、内容身份、page 所有者和已提交 checkpoint。排队保存前后都验证对象仍存活，结束请求立即撤销未执行任务。

明确 host 池是所有 worker 的总预算还是每 worker 预算，并分别计入 staging、固定 buffer、文件索引与文件系统余量。协议与依赖版本在启动前确定，不能传输失败后无提示换协议。依赖初始化失败要保留原始错误，避免被空 assertion 抹掉。

后台 recorder 有明确事件/字节/轮转上界，记录 transaction/request/rank 的关联；“有限历史”必须显示可能缺失尾部。嵌套阶段有包含关系，多 rank 有并发关系，分析工具不能简单累加。只有调用提交日志时，设备完成仍为未知。

依据：`docs/kv_offload_memcache.md`、`docs/host_shm_startup_20261110.md`、`docs/offload_guard_incident_20261110.md@59f08592`。这里只提炼所有权与预算方法，不移植具体 connector 或部署配置。

## 已有 benchmark 结果优先离线分析

日志中的 run 路径、prediction 记录与 aggregate JSON 是不同层次。aggregate 只包含总分时不能凭它构造样本长度分布；应定位逐样本 prediction，再按稳定 ID 和配置身份关联可用字段。

长度口径优先使用保存的 token count。缺失时使用正确本地 tokenizer、实际 chat template 和已保存的完整输入重建，并标明重建而非观测。上下文、message、嵌套字段和 usage 各自有语义，不可随便挑一个字符串计数；否则“所有长样本落入一个短 bin”可能只是统计输入选错。

同一 bin 的多次运行准确率可采用等权 run 均值；明确它与 pooled 样本准确率的区别。无贡献的 run/bin 组合为缺失，不按零分计。错误记录、不可读文件、无答案回答分开统计：错误记录不是自动的无答案，答错也不是无答案。

若无答案由评分 extractor 定义，应明确这不是语义拒答/截断分类。失败回复输出长度可用已知长度的 pooled 均值，同时报告已知长度覆盖率；没有失败或没有已知长度时为 N/A，已知空回复才是零 token。

终端表可有颜色，但重定向、`NO_COLOR` 与显式关闭颜色时应无控制码；CSV/JSON 保持机器可读。摘要尽量短，完整证据落盘，原始文件不覆盖。长度 bin 的最高准确率是描述性结果，样本难度和数量可能解释差异，不能推断该长度造成更高准确率。

依据：`docs/longbench_length_stats.md@fb1a5078`。
