# 功能实现记录

本文档记录已经完整实现并验证通过的功能。每次完成一个功能后，都要追加日期、功能名称、实现范围、验证结果；如果功能包含 API 接口，必须写清楚接口格式。

## 2026-05-18

### 访问日志中间件

实现范围：

- 已实现结构化 HTTP 访问日志中间件。
- 已记录请求 ID、HTTP 方法、请求路径、状态码、耗时毫秒数、客户端 IP、错误码和 API Key 指纹。
- 已避免记录原始 API Key 和完整查询串，降低敏感信息进入日志的风险。
- 已支持从 `X-Forwarded-For` 读取客户端来源地址；缺失时回退到连接客户端地址。
- 已支持成功请求和统一错误响应的日志记录，鉴权失败等应用错误会写入 `error_code`。

日志字段格式：

```text
logger_name          qmt_data_api.access
message              http_access
request_id           请求 ID，来自 X-Request-ID 或系统生成值
method               HTTP 方法，例如 GET
path                 请求路径，例如 /api/v1/status/qmt
status_code          HTTP 状态码，例如 200、401、500
duration_ms          请求耗时，单位毫秒
client_ip            客户端 IP，优先取 X-Forwarded-For 首个地址
error_code           应用错误码；成功请求为 null
api_key_fingerprint  API Key 的 SHA256 前 12 位；未提供时为 null
```

验证结果：

- `python -m compileall -q src tests` 通过。
- `python -m pytest tests/integration/test_api.py` 通过。
- 已覆盖成功健康检查请求的访问日志字段。
- 已覆盖鉴权失败请求的错误码记录与 API Key 脱敏指纹。

### 缓存状态接口

实现范围：

- 已实现 `GET /api/v1/cache/status` 只读接口。
- 已实现进程内 TTL 缓存基础对象，支持写入、读取、删除、清空和状态快照。
- 已返回缓存启用状态、缓存目录、运行期缓存层、条目数量、命中次数、未命中次数、淘汰次数、过期次数、最大 TTL 和缓存条目年龄。
- 已返回缓存目录状态 `cache_dir_status`，用于判断缓存目录是否存在、是否为目录、父目录是否存在以及是否具备文件缓存落盘条件。
- 当前接口提供运行期内存缓存状态；文件缓存覆盖范围、缓存预热任务和历史缓存索引尚未接入。

验证结果：

- `python -m compileall -q src tests` 通过。
- `python -m pytest tests/unit/test_memory_cache.py tests/integration/test_api.py` 通过。
- 已覆盖接口鉴权、状态响应、缓存目录状态、命中未命中统计和 TTL 过期统计。

接口格式：

```http
GET /api/v1/cache/status
```

鉴权要求：

- 需要请求头：`X-API-Key: <api-key>`。
- 可选请求头：`X-Request-ID: <request-id>`。

请求参数：

- 无。

成功响应：

```json
{
  "success": true,
  "code": "OK",
  "message": "success",
  "request_id": "req_xxx",
  "data": {
    "status": "ok",
    "enabled": true,
    "cache_dir": "data/cache",
    "cache_dir_status": {
      "path": "data/cache",
      "exists": true,
      "is_dir": true,
      "parent_exists": true,
      "ready_for_file_cache": true
    },
    "layers": [
      {
        "name": "runtime",
        "backend": "memory",
        "enabled": true,
        "item_count": 0,
        "hit_count": 0,
        "miss_count": 0,
        "evicted_count": 0,
        "expired_count": 0,
        "max_ttl_seconds": null,
        "oldest_item_age_seconds": null,
        "newest_item_age_seconds": null
      },
      {
        "name": "market_snapshot",
        "backend": "memory",
        "enabled": true,
        "item_count": 0,
        "hit_count": 0,
        "miss_count": 0,
        "evicted_count": 0,
        "expired_count": 0,
        "max_ttl_seconds": null,
        "oldest_item_age_seconds": null,
        "newest_item_age_seconds": null
      }
    ],
    "capabilities": [
      "memory_ttl_status",
      "hit_miss_statistics",
      "snapshot_cache_status"
    ],
    "notes": [
      "当前接口提供进程内缓存状态；文件缓存覆盖范围和预热任务状态将在后续功能接入。"
    ]
  },
  "meta": {
    "server_time": "2026-05-18T10:50:00+08:00"
  }
}
```

错误响应：

```json
{
  "success": false,
  "code": "AUTH_MISSING_API_KEY",
  "message": "缺少 API Key",
  "request_id": "req_xxx",
  "data": null,
  "meta": {
    "retryable": false,
    "server_time": "2026-05-18T10:50:00+08:00"
  }
}
```

### 历史 K 线接口

实现范围：

- 已实现单证券历史 K 线查询。
- 已支持周期：`tick`、`1m`、`5m`、`15m`、`30m`、`60m`、`1d`、`1w`、`1mon`。
- 已支持复权类型：`none`、`front`、`back`。
- 已支持数据来源参数：`auto`、`qmt`。当前尚未实现缓存，`auto` 会直接走 QMT。
- 已支持返回条数限制 `limit`。
- 已实现 xtdata 历史行情适配，底层调用 `xtdata.get_market_data_ex(...)`。
- 已实现 DataFrame 行映射，输出统一 K 线字段。

验证结果：

- `python -m compileall -q src tests` 通过。
- `python -m pytest tests/unit/test_market_service.py tests/integration/test_api.py` 通过，14 项相关测试全部通过。
- 已执行真实 `get_market_klines("600519.SH", "1d", "20240101", "20240110", limit=5)` 探测，本机 QMT 返回可用历史 K 线。

接口格式：

```http
GET /api/v1/market/kline?symbol=600519.SH&period=1d&start=20240101&end=20240110&adjust=none&source=auto&limit=5
```

鉴权要求：

- 需要请求头：`X-API-Key: <api-key>`。
- 可选请求头：`X-Request-ID: <request-id>`。

请求参数：

```text
symbol  必填，证券代码，例如 600519.SH
period  可选，K 线周期，默认 1d
start   必填，开始日期，支持 YYYYMMDD 或 YYYY-MM-DD
end     必填，结束日期，支持 YYYYMMDD 或 YYYY-MM-DD
adjust  可选，复权类型，none | front | back，默认 none
source  可选，数据来源，auto | qmt，默认 auto
limit   可选，最大返回条数，必须大于等于 1
```

成功响应：

```json
{
  "success": true,
  "code": "OK",
  "message": "success",
  "request_id": "req_xxx",
  "data": {
    "symbol": "600519.SH",
    "period": "1d",
    "adjust": "none",
    "bars": [
      {
        "time": "2024-01-04T00:00:00+08:00",
        "trade_date": "2024-01-04",
        "open": 1693.0,
        "high": 1693.0,
        "low": 1662.93,
        "close": 1669.0,
        "volume": 21551.0,
        "amount": 3603970147.0,
        "pre_close": 1694.0,
        "suspend_flag": 0
      }
    ]
  },
  "meta": {
    "server_time": "2026-05-18T10:45:00+08:00",
    "source": "qmt",
    "count": 1
  }
}
```

错误响应：

```json
{
  "success": false,
  "code": "INVALID_PERIOD",
  "message": "K 线周期不支持",
  "request_id": "req_xxx",
  "data": {
    "period": "2m"
  },
  "meta": {
    "retryable": false,
    "server_time": "2026-05-18T10:45:00+08:00"
  }
}
```

### 历史 K 线文件缓存

实现范围：

- 已实现历史 K 线 JSON 文件缓存，缓存位置为 `CACHE_DIR/klines/<symbol>/<period>/<adjust>/<start>_<end>_limit-<limit>.json`。
- 已实现完整请求参数粒度缓存，缓存键包含证券代码、周期、复权类型、开始日期、结束日期和返回条数。
- 已实现 `source=auto` 优先读取文件缓存；未命中时回源 QMT，成功后写入本地 JSON 文件。
- 已实现 `source=cache` 只读文件缓存；缺失时返回 `CACHE_MISS`，不会触发 QMT 回源。
- 已实现 `source=qmt` 强制回源 QMT，并刷新同参数文件缓存。
- 已在响应 `meta` 中返回 `cache` 状态，当前支持 `hit` 与 `miss`。
- 已在 `GET /api/v1/cache/status` 中新增 `kline_file` 缓存层，展示历史 K 线文件缓存条目数、命中次数、未命中次数、淘汰次数、过期次数和文件年龄。
- 已实现 `DELETE /api/v1/cache/kline` 清理接口，可删除历史 K 线 JSON 缓存与写入过程遗留的临时文件，并返回删除数量和清理后的缓存层状态。
- 当前文件缓存没有 TTL，也不做区间合并或增量补齐；这是历史缓存能力的第一步。

验证结果：

- `python -m compileall -q src tests` 通过。
- `python -m pytest tests/unit/test_file_cache.py tests/unit/test_market_service.py tests/integration/test_api.py` 通过，28 项相关测试通过。
- `python -m pytest` 通过，31 项全量测试通过。
- 已覆盖首次请求回源 QMT、二次请求命中文件缓存、`source=cache` 缺失返回 `CACHE_MISS`、缓存状态接口返回 `kline_file` 层、清理接口鉴权与删除行为。

K 线接口格式：

```http
GET /api/v1/market/kline?symbol=600519.SH&period=1d&start=20240101&end=20240110&adjust=none&source=auto&limit=5
```

鉴权要求：

- 需要请求头：`X-API-Key: <api-key>`。
- 可选请求头：`X-Request-ID: <request-id>`。

请求参数：

```text
symbol  必填，证券代码，例如 600519.SH
period  可选，K 线周期，默认 1d；支持 tick | 1m | 5m | 15m | 30m | 60m | 1d | 1w | 1mon
start   必填，开始日期，支持 YYYYMMDD 或 YYYY-MM-DD
end     必填，结束日期，支持 YYYYMMDD 或 YYYY-MM-DD
adjust  可选，复权类型：none | front | back，默认 none
source  可选，数据来源：auto | cache | qmt，默认 auto
limit   可选，最大返回条数，必须大于等于 1
```

成功响应：

```json
{
  "success": true,
  "code": "OK",
  "message": "success",
  "request_id": "req_xxx",
  "data": {
    "symbol": "600519.SH",
    "period": "1d",
    "adjust": "none",
    "bars": [
      {
        "time": "2024-01-02T00:00:00+08:00",
        "trade_date": "2024-01-02",
        "close": 1685.01
      }
    ]
  },
  "meta": {
    "server_time": "2026-05-18T10:45:00+08:00",
    "source": "cache",
    "cache": "hit",
    "count": 1
  }
}
```

缓存缺失响应：

```json
{
  "success": false,
  "code": "CACHE_MISS",
  "message": "缓存缺失",
  "request_id": "req_xxx",
  "data": {
    "symbols": ["600519.SH"]
  },
  "meta": {
    "retryable": false,
    "server_time": "2026-05-18T10:45:00+08:00"
  }
}
```

缓存状态接口补充：

```json
{
  "name": "kline_file",
  "backend": "json_file",
  "enabled": true,
  "item_count": 1,
  "hit_count": 1,
  "miss_count": 1,
  "evicted_count": 0,
  "expired_count": 0,
  "max_ttl_seconds": null,
  "oldest_item_age_seconds": 3.2,
  "newest_item_age_seconds": 3.2
}
```

清理接口格式：

```http
DELETE /api/v1/cache/kline
```

鉴权要求：

- 需要请求头：`X-API-Key: <api-key>`。
- 可选请求头：`X-Request-ID: <request-id>`。

请求参数：

- 无。

成功响应：

```json
{
  "success": true,
  "code": "OK",
  "message": "success",
  "request_id": "req_xxx",
  "data": {
    "removed_count": 1,
    "layer": {
      "name": "kline_file",
      "backend": "json_file",
      "enabled": true,
      "item_count": 0,
      "hit_count": 1,
      "miss_count": 1,
      "evicted_count": 1,
      "expired_count": 0,
      "max_ttl_seconds": null,
      "oldest_item_age_seconds": null,
      "newest_item_age_seconds": null
    }
  },
  "meta": {
    "server_time": "2026-05-19T10:45:00+08:00"
  }
}
```

### 行情快照接口

实现范围：

- 已实现证券代码规范化和去重，支持 `600519.SH`、`000001.SZ`、`430047.BJ` 这类六位代码加市场后缀格式。
- 已实现单次请求数量限制，默认最多 200 个证券代码，可通过环境变量 `MARKET_SNAPSHOT_MAX_SYMBOLS` 调整。
- 已实现 xtdata 行情快照适配，底层调用 `xtdata.get_full_tick(symbols)`。
- 已实现 QMT 原始字段映射，输出 `last_price`、`pre_close`、`open`、`high`、`low`、`volume`、`amount`、`bid1`、`ask1` 等稳定字段。
- 已实现缺失证券列表 `missing_symbols`，单个证券缺失不会导致整个请求失败。
- 已实现 GET 和 POST 两种调用方式。
- 已实现快照 TTL 缓存，`source=auto` 优先读取缓存并在缺失时回源 QMT，`source=cache` 仅读取缓存，`source=qmt` 强制回源。
- 已在响应 `meta` 中返回 `source` 与 `cache`，用于区分缓存命中、缓存缺失、混合结果和 QMT 回源。

验证结果：

- `python -m compileall -q src tests` 通过。
- `python -m pytest tests/unit/test_config.py tests/unit/test_market_service.py tests/integration/test_api.py` 通过，11 项测试全部通过。
- 已执行真实 `get_market_snapshots(["600519.SH"])` 探测，本机 QMT 返回可用行情快照。

GET 接口格式：

```http
GET /api/v1/market/snapshot?symbols=600519.SH,000001.SZ&fields=last_price,volume&source=auto
```

POST 接口格式：

```http
POST /api/v1/market/snapshot
Content-Type: application/json
```

鉴权要求：

- 需要请求头：`X-API-Key: <api-key>`。
- 可选请求头：`X-Request-ID: <request-id>`。

GET 请求参数：

```text
symbols  必填，逗号分隔的证券代码列表，例如 600519.SH,000001.SZ
fields   可选，逗号分隔的字段列表，例如 last_price,volume
source   可选，数据来源，auto | cache | qmt，默认 auto
```

POST 请求体：

```json
{
  "symbols": ["600519.SH", "000001.SZ"],
  "fields": ["last_price", "volume"],
  "source": "auto"
}
```

成功响应：

```json
{
  "success": true,
  "code": "OK",
  "message": "success",
  "request_id": "req_xxx",
  "data": [
    {
      "symbol": "600519.SH",
      "quote_time": "2026-05-18T10:38:56+08:00",
      "last_price": 1328.5,
      "pre_close": 1332.95,
      "open": 1336.0,
      "high": 1342.68,
      "low": 1325.57,
      "volume": 22930.0,
      "amount": 3057433600.0,
      "bid1": 1328.5,
      "bid1_volume": 11.0,
      "ask1": 1328.55,
      "ask1_volume": 4.0
    }
  ],
  "meta": {
    "server_time": "2026-05-18T10:38:56+08:00",
    "missing_symbols": [],
    "fields": ["last_price", "volume"],
    "source": "qmt",
    "cache": "miss"
  }
}
```

错误响应：

```json
{
  "success": false,
  "code": "INVALID_SYMBOL",
  "message": "证券代码格式错误",
  "request_id": "req_xxx",
  "data": {
    "symbols": ["BAD-SYMBOL"]
  },
  "meta": {
    "retryable": false,
    "server_time": "2026-05-18T10:38:56+08:00"
  }
}
```

### 只读 API 基础骨架

实现范围：

- 已实现 FastAPI 应用工厂和顶层路由聚合。
- 已实现配置加载，支持从环境变量读取运行环境、监听地址、端口、API Key、日志目录、数据目录、缓存目录和 QMT 交易开关。
- 已实现统一成功响应和统一错误响应。
- 已实现应用错误码、`AppError`、`AuthError`、`QmtError`。
- 已实现请求 ID 中间件，支持读取或生成 `X-Request-ID` 并写回响应头。
- 已实现 API Key 鉴权依赖，默认启用。
- 已实现全局异常处理，覆盖应用异常、请求参数校验异常和未预期异常。

验证结果：

- `python -m compileall -q src tests` 通过。
- `python -m pytest tests/unit/test_config.py tests/integration/test_api.py` 通过，5 项测试全部通过。
- 已执行真实 `probe_xtdata_status()` 探测，本机 QMT 数据链路可连接。

### 健康检查接口

接口格式：

```http
GET /api/v1/health
```

鉴权要求：

- 不需要 API Key。
- 可选请求头：`X-Request-ID: <request-id>`。

请求参数：

- 无。

成功响应：

```json
{
  "success": true,
  "code": "OK",
  "message": "success",
  "request_id": "req_xxx",
  "data": {
    "service": "qmt-data-api",
    "version": "0.1.0",
    "status": "ok",
    "environment": "local"
  },
  "meta": {
    "server_time": "2026-05-18T10:00:00+08:00"
  }
}
```

### 系统状态接口

接口格式：

```http
GET /api/v1/status
```

鉴权要求：

- 需要请求头：`X-API-Key: <api-key>`。
- 可选请求头：`X-Request-ID: <request-id>`。

请求参数：

- 无。

成功响应：

```json
{
  "success": true,
  "code": "OK",
  "message": "success",
  "request_id": "req_xxx",
  "data": {
    "service": "qmt-data-api",
    "version": "0.1.0",
    "environment": "local",
    "status": "ok",
    "qmt": {
      "status": "ok",
      "xtdata_imported": true,
      "qmt_running": true,
      "connected": true,
      "peer_addr": "127.0.0.1:58610",
      "data_dir": "D:/QMT/userdata_mini/datadir",
      "quote_server_status": null,
      "quote_server_status_error": null
    }
  },
  "meta": {
    "server_time": "2026-05-18T10:00:00+08:00"
  }
}
```

降级响应说明：

- 当 QMT 探测抛出应用异常时，接口仍返回 HTTP 200。
- `data.status` 返回 `degraded`。
- `data.qmt` 返回错误码、错误信息和是否可重试。

### QMT 状态探测接口

接口格式：

```http
GET /api/v1/status/qmt
```

鉴权要求：

- 需要请求头：`X-API-Key: <api-key>`。
- 可选请求头：`X-Request-ID: <request-id>`。

请求参数：

- 无。

成功响应：

```json
{
  "success": true,
  "code": "OK",
  "message": "success",
  "request_id": "req_xxx",
  "data": {
    "status": "ok",
    "xtdata_imported": true,
    "qmt_running": true,
    "connected": true,
    "peer_addr": "127.0.0.1:58610",
    "data_dir": "D:/QMT/userdata_mini/datadir",
    "quote_server_status": null,
    "quote_server_status_error": null
  },
  "meta": {
    "server_time": "2026-05-18T10:00:00+08:00"
  }
}
```

错误响应：

```json
{
  "success": false,
  "code": "QMT_XTDATA_UNAVAILABLE",
  "message": "xtdata 客户端不可用",
  "request_id": "req_xxx",
  "data": {
    "error": "原始异常信息"
  },
  "meta": {
    "retryable": true,
    "server_time": "2026-05-18T10:00:00+08:00"
  }
}
```

### API Key 鉴权

实现范围：

- 默认启用 API Key 鉴权。
- 从环境变量 `API_KEYS` 读取逗号分隔的可用密钥。
- 支持通过 `API_KEY_ENABLED=false` 关闭鉴权。
- 未提供 API Key 时返回 `AUTH_MISSING_API_KEY`。
- API Key 无效时返回 `AUTH_INVALID_API_KEY`。

接口格式：

```http
X-API-Key: <api-key>
```

错误响应：

```json
{
  "success": false,
  "code": "AUTH_MISSING_API_KEY",
  "message": "缺少 API Key",
  "request_id": "req_xxx",
  "data": null,
  "meta": {
    "retryable": false,
    "server_time": "2026-05-18T10:00:00+08:00"
  }
}
```
