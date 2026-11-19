# 示例边界

`evidence-fixture.json` 仅展示状态组合和工件路径，不代表任何工程验收。它包含一个明确标记为 synthetic 的文件，演示结构检查不能判断工件真实性。采用模板时使用 `templates/evidence.json` 并填入自己的实际结果，不把此 fixture 复制为交付证据。

真实项目可以先只运行主机测试，保存完整日志后将 `host` 改为 `pass`，写明检查范围。其他层级维持实际状态，直到有属于该层的证据；没有设备时不会因主机测试成功而通过 `device`。

从工具仓库根目录运行：

```bash
python3 tools/check_evidence.py examples/evidence-fixture.json --root . --require host
```

此示例预期通过格式检查。再添加 `--require device` 应以非零状态退出，因为 device 为 `blocked`。
