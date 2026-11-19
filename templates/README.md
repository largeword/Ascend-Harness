# 模板约定

这些文件供新项目填写使用，工具不会自动运行 `project.json` 中的命令。所有路径按采用本模板的项目根目录解释；证据路径还应符合校验工具指定的 root。使用前把 `UNSET`、`null` 和必要的空数组换成真实配置。

**使用 CANNBot 的工程以平台当前适用的工作流和文件格式为准。** 优先使用下方 `supplement.md` 引用其已有配置和证据。其余 JSON 模板用于独立工程，不能建立另一份平台 request/state、精度/性能门或发布许可；本文的八个 gate 也不是 CANNBot Stage 的映射。

| 文件 | 用途 |
| --- | --- |
| `supplement.md` | 共存时的补充核查：引用平台权威工件，不另记验收结论 |
| `AGENTS.project.md` | 合并进项目规则的通用约束及本地填写项 |
| `project.json` | 当前任务 owner、设备、模型、边界与显式授权范围 |
| `acceptance.json` | 测量前冻结精度、图、质量和性能合同 |
| `build-dimensions.json` | fingerprint 工具需要的显式编译维度 |
| `evidence.json` | 逐层报告状态、工件、适用性与允许声明 |
| `references.json` | 显式批准、只读的参考来源清单 |
| `incident.md` | 原始事实、修复边界与失败尝试档案 |
| `experiment.md` | 冻结输入、argv、计时器、统计口径及实验归因 |

`project.json` 的未知硬件和路径保留 `null` 或 `[]`，不可猜测。`commands` 中每个命令以 argv 数组填写，例如 `["python3", "-m", "unittest", "discover"]`，避免把字符串交给 shell。`scope` 记录现有授权，不建立重复询问用户的流程。

`integration.mode` 按任务填写，例如外部插件、独立算子或原生框架开发；`reference_policy` 与 `references.json.policy` 记录已确认的来源边界。模板不强制所有工程采用外部插件。图地址、同步等约束同样按目标运行时合同填写，未配置不表示允许或禁止。

`acceptance.json` 是独立工程需要自行实现的合同示例。CANNBot 已规定的误差指标、标准、重复/聚合/抖动策略直接由平台维护，不抄成这份模板的另一组值。空阈值表示尚未定义，不能视作不限制或验收通过。模型质量容忍度使用百分点，性能比例使用小数。精度合同改变时升级 revision 并在新测量前冻结，保留旧结果。

`references.json.sources` 每项推荐包含 `id`、`url` 或 `local_path`、`revision`、`allowed_scope`、`owner`、`read_only: true`。没有列出的参考需先确认本次任务是否已授权其使用；禁止修改或部署覆盖参考树。

## 证据格式

顶层固定为 `schema_version: 1`、`subject`、`gates` 和 `claims`。`subject.revision`、`subject.scenario` 是字符串。`gates` 含以下八层：

| gate | 它能够支持的结论 |
| --- | --- |
| source | 源码、路由、冻结边界与参考来源检查 |
| host | 主机测试、CPU oracle、离线解析 |
| compile | 指定源码与环境下的编译和产物身份 |
| device | 真实设备执行和错误域 |
| graph_capture | 规定场景成功捕获 |
| graph_replay | 规定输入与状态下的回放行为 |
| quality | 预先约定业务/模型质量指标 |
| performance | 冻结实验协议下的性能指标 |

每项包含 `status`、`artifacts`（项目内相对路径列表）、`reason`；模板另带 `applicability` 描述适用范围。可用状态为 `not_run`、`pass`、`fail`、`blocked`、`not_applicable`。`pass` 必须至少有一个真实工件且 reason 非空；`blocked` 与 `not_applicable` 必须说明原因。`claims` 是允许声明的 gate 名称列表，列入的 gate 必须为 `pass`。

没有真实测量就保留 `not_run`；缺少必须资源或前置条件用 `blocked`；任务确实不涉及该层才用 `not_applicable`。规则允许某层不适用，不应把它伪装成通过。每层独立，编译成功不会自动提升 device 或 performance。

证据工具只能检查结构、状态和工件路径，不能证明日志真实、数学正确、计时可比或质量达标。reviewer 还需核对 subject、输入身份、工件内容和冻结合同。不要发布包含私有路径、访问凭证或用户数据的工件。

## 与命令行工具配合

下面命令从本工具仓库根目录运行。安装到其他工程后将 `tools/` 改为 `.harness/tools/`，并使用该工程实际配置与工件位置。

记录一个真实主机检查，输出目录必须不存在；`--` 后面直接传 argv：

```bash
python3 tools/run_phase.py --output artifacts/host-check --timeout 60 -- \
  python3 -m json.tool templates/project.json
```

此命令只证明 JSON 可解析。完整输出写入 `output.log`，执行状态写入 `phase.json`。只有真实测试完成后才手工更新对应 evidence gate，并注明检查范围。

验证未执行模板的格式，或检查真实项目要求通过的层级：

```bash
python3 tools/check_evidence.py templates/evidence.json --root .
python3 tools/check_evidence.py evidence.json --root . --require host --require compile
```

第二条命令要求项目自己已经创建 `evidence.json`；把未测层级标成 `pass` 不会产生真实证据。

填写 `build-dimensions.json` 中 SOC、CANN、编译器和 Python 的准确版本/身份后，再计算显式输入集合的 fingerprint。`null` 会被工具拒绝：

```bash
python3 tools/fingerprint.py --root . \
  --dimensions build-dimensions.json \
  --file CMakeLists.txt --file src/kernel.cpp \
  --output artifacts/build-fingerprint.json
```

示例中的源文件需换成实际项目路径，并列全会影响编译的源文件、头文件、生成器和构建脚本。输出父目录应先存在，manifest 文件必须是新文件。该工具只计算身份；不清理、不复用构建，也不验证已生成二进制。若实现缓存复用，还须独立检查完成标记、产物 hash 和加载身份。
