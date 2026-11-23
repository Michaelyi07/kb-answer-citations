# CHANGELOG — prompts/kb_answer

格式遵循 Keep a Changelog；提示词版本号与 `kb_answer/recorder.py::PROMPT_VERSION` 对应。

## [v1] - 2026-11-23

- 首版发布（S3-KB-020）。
- 三条硬规则：强制 `[n]` 引用；证据不足拒答（`refused=true`，正文「知识库中没有找到」）；价格费用数字逐字引用、禁止计算。
- 证据块格式：`[n] 《文档标题》 v版本 > heading_path` 拼接。
- 输出 JSON Schema：`{points:[{text, citations:[n]}], refused}`（见 `kb_answer/schema.py`）。
- v1 冻结：措辞改动一律新建 v2，禁止原地修改 v1（快照测试 hash-pin 锁定）。
