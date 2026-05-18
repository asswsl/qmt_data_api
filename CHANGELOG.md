# Changelog

本文档记录本仓库的重要变更。每次 agent 完成变更后，都应同步更新此文件。

## 2026-05-18

### Changed

- 新增进程内 TTL 缓存实现，支持缓存命中、未命中、写入、过期清理和统计信息。
- 行情快照接口新增 `source` 参数，支持 `auto`、`cache`、`qmt` 三种读取策略。
- 行情快照接口接入 TTL 内存缓存，`auto` 优先读缓存、缺失时读取 QMT 并回写缓存；`cache` 只读缓存；`qmt` 强制读取 QMT 并刷新缓存。
- 新增缓存状态接口 `GET /api/v1/cache/status`，返回快照缓存后端、TTL、条目数量和命中统计。
- 新增快照缓存单元测试、缓存状态接口集成测试和真实 QMT 缓存命中验证。
- 新增历史 K 线只读接口 `GET /api/v1/market/kline`，支持证券代码、周期、起止日期、复权类型、数据来源和返回条数参数。
- 新增历史 K 线 xtdata 适配与 DataFrame 行映射，统一输出 `time`、`trade_date`、`open`、`high`、`low`、`close`、`volume`、`amount`、`pre_close` 等字段。
- 新增历史 K 线参数校验，覆盖非法证券代码、不支持周期、不支持复权类型、不支持数据来源和错误时间范围。
- 新增历史 K 线单元测试、集成测试和真实 QMT 历史数据验证。
- 新增行情快照只读接口，支持 `GET /api/v1/market/snapshot` 和 `POST /api/v1/market/snapshot`。
- 新增证券代码规范化、行情快照领域服务、xtdata 快照适配和原始字段映射。
- 新增行情快照参数校验，覆盖非法证券代码、请求数量超限、缺失数据和 API Key 鉴权。
- 新增行情快照单元测试与集成测试。
- 新增 agent 运行规范：每次完整实现功能后必须更新功能文档；若为 API 接口，必须记录请求方法、路径、鉴权要求、请求参数和响应格式。
- 新增 `docs/features.md`，记录已完整实现的只读 API 基础骨架、健康检查接口、系统状态接口、QMT 状态探测接口和 API Key 鉴权。
- 实现第一步最小可运行只读 API 骨架，包括配置加载、统一响应、应用错误码、请求 ID 中间件、API Key 鉴权和统一异常处理。
- 实现 `GET /api/v1/health`、`GET /api/v1/status` 和 `GET /api/v1/status/qmt`。
- 接入真实 `xtquant.xtdata` 状态探测，用于判断 xtdata 导入、客户端连接、本地数据目录和行情服务能力状态。
- 修复 `AppError` 初始化链路，确保鉴权失败和 QMT 探测异常能够稳定返回统一错误结构。
- 新增配置与接口测试，覆盖 API Key、健康检查和 QMT 状态接口行为。

### Validation

- 已执行 `python -m compileall -q src tests`，Python 语法检查通过。
- 已执行 `python -m pytest tests/unit/test_market_service.py tests/integration/test_api.py`，18 项相关测试全部通过。
- 已执行真实主机快照缓存探测：连续两次 `get_market_snapshots(["600519.SH"], source="auto")` 返回首次 `miss/qmt`、二次 `hit/cache`。
- 已执行 `python -m compileall -q src tests`，Python 语法检查通过。
- 已执行 `python -m pytest tests/unit/test_market_service.py tests/integration/test_api.py`，14 项相关测试全部通过。
- 已执行真实主机历史 K 线探测：`get_market_klines("600519.SH", "1d", "20240101", "20240110", limit=5)` 返回可用 K 线数据。
- 已执行 `python -m compileall -q src tests`，Python 语法检查通过。
- 已执行 `python -m pytest`，11 项测试全部通过。
- 已执行真实主机行情快照探测：`get_market_snapshots(["600519.SH"])` 返回可用快照数据。
- 已执行 `python -m pytest tests/unit/test_config.py tests/integration/test_api.py`，5 项测试全部通过。
- 已执行真实主机探测：`probe_xtdata_status()` 返回已连接状态，当前本机 QMT 数据链路可用。
- 已检查本次新增与修改的代码文件首行中文说明。
- 已执行 `git diff --check`，未发现空白错误。

## 2026-05-15

### Changed

- 更新 agent 运行规范，要求 Git 提交信息、提交正文、PR 标题、PR 描述、PR 评论和合并说明均使用中文。
- 更新 PR 描述模板，将 `Summary`、`Validation`、`Risk` 改为中文标题。

### Validation

- 已执行 UTF-8 严格解码检查。
- 已执行 `git diff --check`，未发现空白错误。

## 2026-05-14

### Changed

- 更新 agent 运行规范，要求所有代码文件首行使用中文简短介绍文件功能。
- 为现有 Python 与 PowerShell 代码文件补充首行中文功能说明。
- 生成项目总目录骨架，包含 `src/qmt_data_api/` 后端包结构、配置模板、脚本目录、测试目录、运行期目录说明、Windows 打包模板和项目结构文档。
- 更新 `.gitignore`，允许提交运行期目录说明文件和 `.gitkeep`，继续排除真实数据、缓存、日志、运行状态、密钥和本地配置。
- 新增 `docs/system-requirements-and-api.md`，沉淀 QMT Data API 的系统需求分析、功能优先级、模块规划、接口格式、错误码、缓存策略和落地路线。
- 新增 agent 运行规范要求：每次变更后必须同步更新 `CHANGELOG.md`。
- 新增文档变更处理规则：仅文档、说明、规范或注释类变更暂不推送分支、不创建或更新 PR，等待后续代码变更时一并推送和提交 PR。

### Validation

- 已执行 UTF-8 严格解码检查。
- 已执行 `git diff --check`，未发现空白错误。
- 已执行 `python -m compileall -q src`，项目骨架 Python 文件语法检查通过。
- 已检查所有 `.py` 与 `.ps1` 文件首行均为中文功能说明。
