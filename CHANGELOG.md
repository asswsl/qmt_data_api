# Changelog

本文档记录本仓库的重要变更。每次 agent 完成变更后，都应同步更新此文件。

## 2026-05-19

### Changed

- 新增证券基础信息接口 `GET/POST /api/v1/instruments`，支持按证券代码查询名称、市场、证券类型、上市状态与缺失证券列表。
- 新增交易日历接口 `GET /api/v1/calendar/trading-days`，支持查询市场交易日、上一交易日、下一交易日，并在 `source=auto` 下提供本地工作日兜底。
- 新增批量历史 K 线接口 `POST /api/v1/market/klines`，支持多证券一次性拉取历史 K 线、字段裁剪、缓存命中状态和缺失证券列表。
- 新增最近 K 线接口 `GET /api/v1/market/kline/latest`，支持按 `count` 获取单证券最近 K 线，用于远程客户端准实时刷新。
- 历史 K 线接口新增 `fields` 参数，可按需返回 `trade_date`、`close`、`volume` 等指定字段，减少跨机器传输体积。
- 新增轻量 Python 客户端 `qmt_data_api.client.QmtDataClient`，封装快照、单证券 K 线、批量 K 线、最近 K 线、证券基础信息和交易日历调用。
- 新增可选限流中间件，支持通过 `API_RATE_LIMIT_ENABLED`、`API_RATE_LIMIT_REQUESTS` 和 `API_RATE_LIMIT_WINDOW_SECONDS` 控制远程请求频率。
- 完善新增业务接口的 OpenAPI `summary` 与 `description`，便于通过 `/docs` 直接调试。

### Validation

- 已执行 `python -m compileall -q src tests`，Python 语法检查通过。
- 已执行 `python -m pytest tests/unit/test_config.py tests/unit/test_client.py tests/unit/test_market_service.py tests/integration/test_api.py`，34 项投入使用相关接口与客户端测试通过。
- 已执行 `python -m pytest`，38 项全量测试通过。

## 2026-05-18

### Changed

- 新增历史 K 线 JSON 文件缓存，`GET /api/v1/market/kline` 在 `source=auto` 时优先读取本地文件缓存，未命中后回源 QMT 并写入缓存。
- 历史 K 线接口新增 `source=cache` 只读缓存模式；缓存缺失时返回统一 `CACHE_MISS` 错误。
- 历史 K 线接口响应 `meta` 新增 `cache` 字段，用于标识 `hit` 或 `miss`。
- 缓存状态接口新增 `kline_file` 缓存层与 `kline_file_cache_status` 能力标识，用于查看历史 K 线文件缓存条目数、命中次数和未命中次数。
- 新增历史 K 线文件缓存清理接口 `DELETE /api/v1/cache/kline`，用于删除本地 K 线 JSON 缓存并返回清理后的缓存层状态。
- 新增历史 K 线文件缓存单元测试与接口集成测试，覆盖首次回源、二次命中、只读缓存缺失和状态统计。
- 新增结构化访问日志中间件，记录请求 ID、方法、路径、状态码、耗时、客户端 IP、错误码和脱敏 API Key 指纹。
- 统一错误响应会将应用错误码写入请求状态，便于访问日志关联失败原因。
- 新增访问日志集成测试，覆盖成功请求、鉴权失败请求和敏感密钥不落日志。
- 新增缓存状态接口 `GET /api/v1/cache/status`，用于查询运行期缓存后端、缓存目录、条目数量、命中次数、未命中次数、淘汰次数和过期次数。
- 缓存状态接口新增 `cache_dir_status` 字段，用于报告缓存目录是否存在、是否为目录、父目录是否存在以及是否已具备文件缓存落盘条件。
- 缓存状态接口新增 `market_snapshot` 缓存层，能够展示行情快照缓存真实条目数、命中次数、未命中次数、过期次数和 TTL 状态。
- 新增进程内 TTL 缓存基础实现，支持 `get`、`set`、`delete`、`clear` 和状态快照，为后续行情快照缓存、历史缓存索引和预热任务提供统一状态来源。
- 行情快照接口新增 `source=auto|cache|qmt` 参数，`auto` 优先读取快照缓存并在缺失时回源 QMT，响应 `meta` 返回 `source` 和 `cache` 状态。
- 新增缓存状态接口集成测试和内存缓存单元测试，覆盖鉴权、状态响应、命中未命中统计和 TTL 过期统计。
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
- 已执行 `python -m pytest tests/unit/test_file_cache.py tests/unit/test_market_service.py tests/integration/test_api.py`，28 项历史 K 线文件缓存相关测试通过。
- 已执行 `python -m pytest`，31 项全量测试通过。
- 已执行 `python -m compileall -q src tests`，Python 语法检查通过。
- 已执行 `python -m pytest tests/integration/test_api.py`，访问日志与 API 集成测试通过。
- 已执行 `python -m pytest tests/unit/test_memory_cache.py tests/integration/test_api.py`，缓存状态接口、缓存目录状态与内存缓存相关测试通过。
- 已执行 `python -m pytest tests/unit/test_config.py tests/unit/test_memory_cache.py tests/unit/test_market_service.py tests/integration/test_api.py`，缓存联动相关测试通过。
- 已执行 `python -m pytest`，全量测试通过。
- 已执行 `git diff --check`，未发现空白错误。
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
