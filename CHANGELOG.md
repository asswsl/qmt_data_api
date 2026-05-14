# Changelog

本文件记录本仓库的重要变更。每次 agent 完成变更后，都应同步更新此文件。

## 2026-05-14

### Changed

- 新增 `docs/system-requirements-and-api.md`，沉淀 QMT Data API 的系统需求分析、功能优先级、模块规划、接口格式、错误码、缓存策略和落地路线。
- 新增 agent 运行规范要求：每次变更后必须同步更新 `CHANGELOG.md`。
- 新增文档变更处理规则：仅文档、说明、规范或注释类变更暂不推送分支、不创建或更新 PR，等待后续代码变更时一并推送和提交 PR。

### Validation

- 已执行 UTF-8 严格解码检查。
- 已执行 `git diff --check`，未发现空白错误。
