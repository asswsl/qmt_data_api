# QMT Data API 系统需求分析与接口规划

## 1. 项目定位

QMT Data API 的目标是把绑定 QMT 的 Windows 主机封装成一个稳定、可控、可观测的数据网关。QMT 主机负责连接 MiniQMT、`xtdata` 和后续可能的 `xttrader`，其他电脑、策略服务、研究脚本只通过标准 HTTP 或 WebSocket 接口访问数据。

第一阶段只做只读数据服务，不做真实交易。交易能力后续独立规划，并默认关闭。

```text
研究机 / 策略机 / 其他电脑
        |
HTTP / WebSocket / SDK
        |
QMT Data API 网关
        |
xtquant.xtdata / xtquant.xttrader
        |
本机 MiniQMT / QMT 客户端
```

## 2. 核心目标

- 降低 QMT 数据使用门槛：其他电脑无需安装、绑定或登录 QMT。
- 解耦数据获取与数据使用：QMT 主机专注取数，下游机器专注研究、回测和策略。
- 建立统一数据服务边界：统一代码格式、字段命名、时间格式、复权口径和错误码。
- 提升稳定性：通过缓存、任务、重试、状态检查和标准错误响应降低原始接口波动影响。
- 为后续扩展打基础：后续可增加财务数据、WebSocket、任务调度、落库、监控和交易模块。

## 3. 用户角色

### 3.1 个人量化研究者

需求：

- 在非 QMT 主机上运行 Notebook、研究脚本和回测程序。
- 快速拉取历史 K 线、实时行情、基础信息和财务数据。
- 希望接口简单、字段稳定、出错信息清晰。

### 3.2 策略开发者

需求：

- 周期性获取实时行情、盘口、涨跌停、分钟线和交易日历。
- 希望接口延迟低、稳定性高、返回结构固定。
- 需要批量查询能力，避免单只股票循环请求造成性能浪费。

### 3.3 数据维护者

需求：

- 批量同步历史行情。
- 维护缓存覆盖范围。
- 追踪缺失数据、失败任务和数据更新时间。

### 3.4 运维维护者

需求：

- 判断 API 服务、QMT 客户端、xtdata 连接是否正常。
- 查看最近行情更新时间、缓存状态、任务状态和错误日志。
- 控制访问权限、IP 白名单和限流策略。

### 3.5 后续交易用户

需求：

- 查询账户、资产、持仓、委托和成交。
- 后续可能需要下单、撤单。

交易能力风险较高，不进入 MVP。后续必须独立鉴权、独立开关、独立审计，并具备风控和熔断机制。

## 4. 典型使用场景

### 4.1 研究电脑拉取历史行情

研究机请求 `600519.SH` 从 2020-01-01 到 2026-05-14 的日线。网关优先读取本地缓存；若缺失，则通过 QMT 补齐后返回统一 JSON。

关键要求：

- 支持单代码和多代码。
- 支持日线、分钟线等周期。
- 支持不复权、前复权、后复权。
- 返回结果可直接转为 pandas DataFrame。

### 4.2 策略服务获取实时行情

策略机批量请求股票最新价、成交量、成交额、买一卖一等字段。网关优先使用短 TTL 内存缓存，减少对 QMT 的压力。

关键要求：

- 支持批量股票代码。
- 支持字段裁剪。
- 能区分实时数据、缓存数据和过期数据。
- 批量请求中单个代码失败不能影响全部结果。

### 4.3 每日盘后数据同步

盘后创建异步任务，同步全市场日线、指数行情、交易日历、除权除息或其他基础数据。

关键要求：

- 支持任务创建、查询、取消、重试。
- 支持失败明细。
- 支持断点续跑。
- 支持缓存覆盖范围查询。

### 4.4 多台机器共享 QMT 数据源

QMT 只运行在一台 Windows 主机。其他研究机、策略机通过局域网 API 访问同一套数据，统一口径。

关键要求：

- 默认只开放内网。
- 支持 API Key。
- 支持 IP 白名单。
- 支持请求日志和限流。

### 4.5 故障排查

当远程机器取不到数据时，需要快速判断是 API 服务异常、QMT 未运行、xtdata 断连、缓存缺失，还是请求参数错误。

关键接口：

- `GET /api/v1/health`
- `GET /api/v1/status`
- `GET /api/v1/status/qmt`
- `GET /api/v1/cache/status`
- `GET /api/v1/jobs/{job_id}`

## 5. 功能优先级

### 5.1 P0：MVP 必须实现

- 服务启动与健康检查。
- QMT / xtdata 状态检测。
- API Key 鉴权。
- 统一响应结构。
- 统一错误码。
- 历史 K 线查询。
- 实时行情快照查询。
- 基础请求日志。
- 基础缓存。
- 局域网访问验证。

### 5.2 P1：强烈建议

- 股票基础信息。
- 交易日历。
- 批量历史数据。
- IP 白名单。
- 限流。
- 缓存覆盖范围查询。
- 异步历史补数任务。
- OpenAPI 文档。

### 5.3 P2：增强能力

- WebSocket 实时行情推送。
- 财务数据。
- 板块、行业、成分股数据。
- 停复牌、除权除息数据。
- CSV / Parquet 导出。
- Web 状态页。
- 监控指标。

### 5.4 P3：生产增强

- HTTPS / 反向代理。
- 用户与权限体系。
- 审计日志。
- 自动健康诊断。
- 备份与恢复。
- 数据完整性校验。
- 账户与交易接口。

## 6. 系统模块规划

```text
qmt-data-api
├─ api                 HTTP / WebSocket 接口层
├─ core                配置、鉴权、错误码、统一响应、日志
├─ adapters
│  └─ xtquant          xtdata / xttrader 适配层
├─ services
│  ├─ market           行情快照、盘口、K 线、分时
│  ├─ instrument       股票列表、合约信息、交易日历
│  ├─ realtime         WebSocket 订阅、推送合并
│  ├─ history_sync     历史数据补全任务
│  ├─ cache            内存缓存、本地文件缓存、索引
│  └─ status           QMT、数据源、缓存、任务状态
├─ storage             SQLite / Parquet / 日志文件
├─ jobs                异步任务执行、重试、进度记录
└─ admin               管理接口、缓存刷新、限流状态
```

## 7. 通用接口约定

接口统一前缀：

```text
/api/v1
```

鉴权请求头：

```text
X-API-Key: <api-key>
X-Request-ID: <optional-client-request-id>
```

时间格式：

- 输入支持 `YYYYMMDD`、`YYYY-MM-DD`、ISO8601。
- 输出统一使用 ISO8601，例如 `2026-05-14T15:30:00+08:00`。
- 交易日字段保留 `trade_date`，格式为 `YYYY-MM-DD`。

证券代码格式：

```text
600519.SH
000001.SZ
```

## 8. 统一响应格式

成功响应：

```json
{
  "success": true,
  "code": "OK",
  "message": "success",
  "request_id": "req_20260514_153000_abcd",
  "data": {},
  "meta": {
    "source": "qmt",
    "cache": "hit",
    "server_time": "2026-05-14T15:30:00+08:00"
  }
}
```

错误响应：

```json
{
  "success": false,
  "code": "QMT_NOT_CONNECTED",
  "message": "QMT 未连接或 xtdata 不可用",
  "request_id": "req_20260514_153001_efgh",
  "data": null,
  "meta": {
    "retryable": true,
    "server_time": "2026-05-14T15:30:01+08:00"
  }
}
```

分页元信息：

```json
{
  "page": 1,
  "page_size": 500,
  "total": 3200,
  "has_more": true
}
```

## 9. MVP 接口清单

```text
GET  /api/v1/health
GET  /api/v1/status
GET  /api/v1/status/qmt
GET  /api/v1/instruments
GET  /api/v1/instruments/{symbol}
GET  /api/v1/market/snapshot
POST /api/v1/market/snapshot
GET  /api/v1/market/kline
POST /api/v1/jobs/history-sync
GET  /api/v1/jobs/{job_id}
GET  /api/v1/cache/status
GET  /api/v1/cache/coverage
WS   /ws/v1/market
```

## 10. 状态接口

### 10.1 健康检查

```http
GET /api/v1/health
```

响应：

```json
{
  "success": true,
  "code": "OK",
  "data": {
    "service": "qmt-data-api",
    "version": "0.1.0",
    "status": "ok",
    "uptime_seconds": 3600
  }
}
```

### 10.2 QMT 状态

```http
GET /api/v1/status/qmt
```

响应：

```json
{
  "success": true,
  "code": "OK",
  "data": {
    "qmt_running": true,
    "xtdata_available": true,
    "xttrader_available": false,
    "market_connected": true,
    "last_quote_time": "2026-05-14T14:59:59+08:00",
    "last_error": null
  }
}
```

状态枚举：

```text
ok
degraded
starting
disconnected
maintenance
error
```

## 11. 基础信息接口

### 11.1 股票列表

```http
GET /api/v1/instruments?market=SH,SZ&type=stock&status=active
```

响应：

```json
{
  "success": true,
  "code": "OK",
  "data": [
    {
      "symbol": "600519.SH",
      "name": "贵州茅台",
      "market": "SH",
      "type": "stock",
      "status": "active",
      "list_date": "2001-08-27",
      "delist_date": null
    }
  ],
  "meta": {
    "cache": "hit",
    "updated_at": "2026-05-14T08:30:00+08:00"
  }
}
```

### 11.2 单个证券信息

```http
GET /api/v1/instruments/600519.SH
```

## 12. 行情快照接口

### 12.1 GET 查询

```http
GET /api/v1/market/snapshot?symbols=600519.SH,000001.SZ
```

### 12.2 POST 批量查询

```http
POST /api/v1/market/snapshot
```

请求：

```json
{
  "symbols": ["600519.SH", "000001.SZ"],
  "fields": ["last_price", "open", "high", "low", "volume", "amount", "bid1", "ask1"]
}
```

响应：

```json
{
  "success": true,
  "code": "OK",
  "data": [
    {
      "symbol": "600519.SH",
      "name": "贵州茅台",
      "trade_date": "2026-05-14",
      "quote_time": "2026-05-14T14:59:59+08:00",
      "last_price": 1688.88,
      "pre_close": 1670.0,
      "open": 1675.0,
      "high": 1690.0,
      "low": 1666.0,
      "volume": 1234567,
      "amount": 2080000000.0,
      "bid1": 1688.8,
      "bid1_volume": 100,
      "ask1": 1688.9,
      "ask1_volume": 200,
      "source": "qmt",
      "cache_time": "2026-05-14T15:00:00+08:00"
    }
  ],
  "meta": {
    "cache": "mixed",
    "missing_symbols": []
  }
}
```

## 13. 历史 K 线接口

```http
GET /api/v1/market/kline?symbol=600519.SH&period=1d&start=20200101&end=20260514&adjust=front&source=auto
```

参数：

```text
symbol   证券代码，例如 600519.SH
period   tick | 1m | 5m | 15m | 30m | 60m | 1d | 1w | 1mon
start    开始日期
end      结束日期
adjust   none | front | back
source   auto | cache | qmt
limit    最大返回条数
```

响应：

```json
{
  "success": true,
  "code": "OK",
  "data": {
    "symbol": "600519.SH",
    "period": "1d",
    "adjust": "front",
    "bars": [
      {
        "time": "2026-05-14T00:00:00+08:00",
        "trade_date": "2026-05-14",
        "open": 1675.0,
        "high": 1690.0,
        "low": 1666.0,
        "close": 1688.88,
        "volume": 1234567,
        "amount": 2080000000.0
      }
    ]
  },
  "meta": {
    "source": "cache",
    "cache_range": {
      "start": "2020-01-01",
      "end": "2026-05-14"
    }
  }
}
```

## 14. WebSocket 实时行情

入口：

```text
WS /ws/v1/market
```

认证可以使用查询参数或首包认证。推荐首包认证，避免 API Key 出现在日志 URL 中。

```json
{
  "op": "auth",
  "api_key": "xxx"
}
```

订阅：

```json
{
  "op": "subscribe",
  "request_id": "sub_001",
  "channel": "quote",
  "symbols": ["600519.SH", "000001.SZ"],
  "fields": ["last_price", "volume", "bid1", "ask1"]
}
```

订阅确认：

```json
{
  "type": "ack",
  "op": "subscribe",
  "request_id": "sub_001",
  "success": true,
  "data": {
    "channel": "quote",
    "symbols": ["600519.SH", "000001.SZ"]
  }
}
```

推送：

```json
{
  "type": "quote",
  "channel": "quote",
  "sequence": 1024,
  "server_time": "2026-05-14T14:59:59.500+08:00",
  "data": {
    "symbol": "600519.SH",
    "quote_time": "2026-05-14T14:59:59+08:00",
    "last_price": 1688.88,
    "volume": 1234567,
    "amount": 2080000000.0,
    "bid1": 1688.8,
    "ask1": 1688.9
  }
}
```

取消订阅：

```json
{
  "op": "unsubscribe",
  "request_id": "unsub_001",
  "channel": "quote",
  "symbols": ["600519.SH"]
}
```

心跳：

```json
{
  "op": "ping",
  "ts": 1778742000000
}
```

响应：

```json
{
  "type": "pong",
  "ts": 1778742000000,
  "server_time": "2026-05-14T15:00:00+08:00"
}
```

实现要求：

- 多客户端订阅同一 symbol 时，底层只订阅一次。
- 新客户端订阅后先推送最新快照。
- 每条推送带 `sequence`，方便客户端判断丢包或乱序。
- 限制最大连接数、单连接最大订阅数和消息发送速率。
- 客户端断开后清理引用计数。

## 15. 异步任务接口

历史补全、批量下载、缓存重建都应异步化。

```text
POST   /api/v1/jobs/history-sync
GET    /api/v1/jobs
GET    /api/v1/jobs/{job_id}
POST   /api/v1/jobs/{job_id}/cancel
POST   /api/v1/jobs/{job_id}/retry
DELETE /api/v1/jobs/{job_id}
```

创建任务：

```json
{
  "symbols": ["600519.SH", "000001.SZ"],
  "periods": ["1d", "1m"],
  "start": "2020-01-01",
  "end": "2026-05-14",
  "adjust": "front",
  "mode": "incremental",
  "priority": 5
}
```

响应：

```json
{
  "success": true,
  "code": "OK",
  "data": {
    "job_id": "job_20260514_001",
    "status": "queued"
  }
}
```

任务状态：

```text
queued
running
succeeded
failed
partial_failed
cancelled
retrying
```

任务对象：

```json
{
  "job_id": "job_20260514_001",
  "type": "history_sync",
  "status": "running",
  "progress": {
    "total": 300,
    "done": 120,
    "failed": 2,
    "percent": 40.0
  },
  "params": {
    "symbols": ["600519.SH"],
    "periods": ["1d", "1m"],
    "start": "2020-01-01",
    "end": "2026-05-14"
  },
  "created_at": "2026-05-14T10:00:00+08:00",
  "started_at": "2026-05-14T10:00:02+08:00",
  "finished_at": null,
  "last_error": null
}
```

## 16. 缓存设计

缓存分层：

```text
L1 内存缓存：实时快照、盘口，TTL 1-3 秒
L2 本地文件：历史 K 线，Parquet 分区
L3 SQLite 索引：缓存覆盖范围、任务状态、更新时间
可选 Redis：多进程或多实例时再引入
```

查询策略：

```text
source=auto   优先缓存，缺口从 QMT 补齐，并异步写回
source=cache  只读缓存，缺失返回 CACHE_MISS
source=qmt    强制 QMT 获取，并刷新缓存
```

缓存接口：

```text
GET  /api/v1/cache/status
GET  /api/v1/cache/coverage?symbol=600519.SH&period=1d
POST /api/v1/cache/warmup
POST /api/v1/cache/invalidate
POST /api/v1/cache/rebuild-index
```

缓存覆盖范围响应：

```json
{
  "success": true,
  "code": "OK",
  "data": {
    "symbol": "600519.SH",
    "period": "1d",
    "adjust": "front",
    "ranges": [
      {
        "start": "2020-01-01",
        "end": "2026-05-14",
        "rows": 1540,
        "updated_at": "2026-05-14T15:10:00+08:00"
      }
    ],
    "missing_ranges": []
  }
}
```

## 17. 错误码规划

```text
OK                         成功

BAD_REQUEST                请求参数错误
INVALID_SYMBOL             股票代码格式错误或不存在
INVALID_PERIOD             K 线周期不支持
INVALID_TIME_RANGE         时间范围错误
TOO_MANY_SYMBOLS           单次请求代码数量超过限制
UNSUPPORTED_FIELD          请求字段不支持

UNAUTHORIZED               未鉴权
FORBIDDEN                  权限不足
RATE_LIMITED               超过限流

QMT_NOT_RUNNING            QMT 客户端未运行
QMT_NOT_CONNECTED          QMT / xtdata 未连接
QMT_TIMEOUT                QMT 调用超时
QMT_ERROR                  QMT 原始异常
DATA_SOURCE_UNAVAILABLE    数据源不可用

CACHE_MISS                 指定 cache-only 但缓存不存在
CACHE_STALE                缓存过期
DATA_NOT_READY             数据正在准备中
DATA_PARTIAL               返回了部分数据

JOB_NOT_FOUND              任务不存在
JOB_ALREADY_RUNNING        同类任务已运行
JOB_CANCELLED              任务已取消
JOB_FAILED                 任务失败

INTERNAL_ERROR             服务内部错误
SERVICE_DEGRADED           服务降级
MAINTENANCE                服务维护中
```

## 18. 安全与权限

第一版先做简单但够用的内网安全：

- API Key。
- IP 白名单。
- 只监听内网地址。
- 请求限流。
- 请求日志。
- 管理接口单独 key。
- 交易接口默认禁用。

权限建议：

```text
market:read
instrument:read
job:read
job:write
cache:read
cache:write
admin:read
admin:write
trade:read
trade:write
```

## 19. 交易能力边界

交易接口不进入 MVP。后续如需支持，应独立命名空间：

```text
/api/v1/trade/*
```

必须具备：

```text
ENABLE_TRADE_API=false
ENABLE_REAL_ORDER=false
独立 token
IP 白名单
client_order_id 幂等
下单额度限制
标的黑白名单
交易时段校验
dry-run
审计日志
熔断开关
```

建议先实现账户、资产、持仓、委托、成交等只读查询，再评估是否开放下单和撤单。

## 20. MVP 验收标准

- QMT 主机上能启动 API 服务。
- 另一台电脑能通过 HTTP 成功拉取行情数据。
- QMT 未运行或未连接时返回清晰错误码。
- API Key 错误时拒绝访问。
- 批量请求部分失败时能返回失败代码列表。
- 历史 K 线结果可被 pandas 直接使用。
- 服务日志能定位请求耗时、来源 IP 和错误原因。
- 缓存命中、缓存缺失、QMT 强制刷新行为可区分。

## 21. 落地路线

### 阶段 1：概念验证

- 启动 HTTP 服务。
- 实现健康检查、QMT 状态、行情快照、K 线查询。
- 使用手动 API Key。
- 完成局域网访问验证。

### 阶段 2：MVP

- 补齐统一响应、错误码、日志。
- 增加股票列表、交易日历。
- 增加 SQLite 缓存索引和 Parquet 历史缓存。
- 提供基础接口文档。

### 阶段 3：Beta

- 增加异步历史补数任务。
- 增加 WebSocket 实时行情。
- 增加缓存管理接口。
- 增加 IP 白名单、限流、Web 状态页。

### 阶段 4：生产增强

- HTTPS 或反向代理部署。
- 完整审计日志。
- 监控告警。
- 数据校验任务。
- 备份与恢复。
- 账户与交易只读能力。

## 22. 结论

第一版应坚持“只读、内网、稳定、可缓存、可观测”。只要历史 K 线、实时快照、QMT 状态、鉴权和缓存链路跑顺，后续扩展 WebSocket、异步任务、财务数据、SDK 和交易模块都会更自然。
