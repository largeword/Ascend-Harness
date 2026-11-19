# Ascend-Harness

把 Ascend 工程中的 Agent 编码经验整理为可直接安装的技能、项目约束模板和小型验证工具。适用于 Ascend C 算子、推理插件、图模式接入及性能分析；不绑定模型、设备编号、服务端口或某个 Agent 平台。

本包从一个实际工程的全部本地与远端分支 tip 提炼：**17 个分支引用，9 个不同提交**，审计日期为 2026-11-19。范围、提交与来源路径见 [分支清单](provenance/branches.md)。这是重点入口、技能、故障与验证机制的审计，不是逐行穷尽全部历史代码。

## 接入另一个工程

工具仅使用 Python 标准库，要求 Python 3.10+。阶段执行器使用 POSIX 进程组，适合 Linux；本包的主机验证不需要 CANN、模型或 NPU。

```bash
git clone https://github.com/largeword/Ascend-Harness.git

# 先显示安装计划；目标必须是已经存在的工程目录
python3 Ascend-Harness/tools/install.py /path/to/your-project

# 写入技能、指南、模板、来源记录和辅助工具
python3 Ascend-Harness/tools/install.py /path/to/your-project --apply
```

安装后：

```text
your-project/
├── .agents/skills/ascend-*/SKILL.md
└── .harness/
    ├── guides/
    ├── templates/
    ├── provenance/
    └── tools/
```

相同内容重复安装不产生改动；任何不同内容的同名文件都会在写入前报冲突，不覆盖现有 `AGENTS.md` 或工程配置。更新时仍从完整的 Ascend-Harness 仓库运行安装器，手工合并冲突。技能正文自包含，也可单独选取所需目录；不使用 `.agents/skills/` 的工具可按自己的技能发现机制载入相同 `SKILL.md`。

接着完成三项配置：

1. 将 `.harness/templates/AGENTS.project.md` 中适用的规则合并到工程现有指令，保留当前用户授权及覆盖关系。
2. 从 [模板说明](templates/README.md) 选取项目配置、验收合同和证据台账，填入本工程的硬件、接入方式、命令、精度及场景。`null`、`UNSET`、必要的空列表都表示尚未配置，不能充当通过。
3. 给 Agent 指明权威配置、源码与产物入口、允许操作范围和验收命令，再按任务使用下面的技能。模板不会自动执行命令或获得远端权限。

## 可以复用什么

| 技能 | 处理的问题 |
| --- | --- |
| [ascend-source-build](skills/ascend-source-build/SKILL.md) | 母源、生成链、CANN 构建、ABI、产物身份与实际调用路径 |
| [ascend-precision-contract](skills/ascend-precision-contract/SKILL.md) | 独立 oracle、版本化精度合同、舍入链与错误域 |
| [ascend-graph-state](skills/ascend-graph-state/SKILL.md) | 真实执行阶段、提交状态、缓存所有权、图捕获和回放 |
| [ascend-performance-experiment](skills/ascend-performance-experiment/SKILL.md) | 配对基线、完整成本、时间口径、性能回归与实验归因 |
| [ascend-deployment-triage](skills/ascend-deployment-triage/SKILL.md) | 配置生效、实时日志、真实返回码、探针和资源清理 |
| [ascend-offline-benchmark](skills/ascend-offline-benchmark/SKILL.md) | 已有日志解析、token 长度、并行重建、失败记录和统计分母 |

四篇指南展开案例和约束：

- [Agent 工作流](guides/agent-workflow.md)：历史合同的覆盖关系、多 Agent 分工、可证伪实验和失败档案。
- [分层验证与故障定位](guides/validation-and-debug.md)：CPU/编译/设备/图/质量/性能各自能证明什么。
- [性能工程](guides/performance-engineering.md)：算子收益如何与整轮收益区分，如何避免重叠时间重复计费。
- [部署与离线分析](guides/deployment-and-analysis.md)：进程与缓存所有权、线程预算、已有 benchmark 的统计陷阱。

稳定方法保留为规则；硬件、数学合同、性能门槛、原生框架或外部插件的接入方式，由新工程重新确定。原项目的一次性禁令、旧阈值和指定分支不成为新工程的默认政策。

## 三个辅助工具

以下命令在本仓库根目录运行。安装到工程后，把 `tools/` 改为 `.harness/tools/`；证据和配置使用目标工程自己的路径。

### 有界阶段运行

```bash
python3 tools/run_phase.py --output /tmp/ascend-host-check --timeout 60 -- \
  python3 -m unittest discover -s tests -v
```

`--output` 必须是新目录。命令以 argv 直接执行；stdout/stderr 合并后实时输出并保存为 `output.log`，`phase.json` 记录真实子进程返回码、状态和耗时。命令自行缓冲的输出仍受其缓冲策略影响，可使用程序自身的无缓冲选项。

正常失败保留命令退出码；超时返回 124，执行器失败返回 125，启动失败返回 127，SIGINT/SIGTERM 分别返回 130/143。仅清理本阶段创建的进程组，清理失败另记且保留首个失败；自行脱离进程组的守护进程需要项目专用生命周期管理。该工具不是持久服务管理器，也不会自动认证 NPU 运行。

运行记录包含命令、工作目录和完整输出，可能含项目私有信息；提交或分享工件前由项目负责人审阅。

### 证据台账检查

```bash
# 空模板只检查结构，不要求任何验证层已经通过
python3 tools/check_evidence.py templates/evidence.json --root .

# 真实工程交付时要求其已声明的验证层通过
python3 tools/check_evidence.py evidence.json --root . --require host --require compile
```

八个独立 gate 为 `source / host / compile / device / graph_capture / graph_replay / quality / performance`。状态为 `not_run / pass / fail / blocked / not_applicable`；`pass` 必须提供存在于证据目录内的工件和理由。检查器不判断日志真实性或数学正确性，也不会因编译通过就提升设备或性能状态。[示例](examples/README.md) 专门演示这一边界。

### 构建输入指纹

```bash
python3 tools/fingerprint.py --root . \
  --dimensions build-dimensions.json \
  --file CMakeLists.txt --file src/kernel.cpp \
  --output build-fingerprint.json
```

先按 [构建维度模板](templates/build-dimensions.json) 填写 SOC、CANN、编译器、Python 和有效编译参数，并列全相关源、头文件及生成器。指纹稳定地绑定内容与维度；它不决定缓存复用，复用还必须校验实际产物 hash、完成标记和加载身份。

## 验证与来源

```bash
python3 -m unittest discover -s tests -v
```

回归覆盖：原始退出码及双流日志、超时、SIGTERM 清理、清理失败保留首错、非法超时、证据层级与路径、安装冲突/幂等/符号链接、构建身份变化。测试只支持本包的主机行为，不构成任何目标 SDK、NPU、模型质量或性能验收。

所有技能和辅助工具均为本次面向迁移重新编写；没有复制模型权重、原始日志、参考源码、第三方技能集或插件缓存。`provenance/` 中的源工程路径仅用于追溯，使用本包不需要访问源工程。
