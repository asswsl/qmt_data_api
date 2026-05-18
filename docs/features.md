# 功能实现记录

本文档记录已经完整实现并验证通过的功能。每次完成一个功能后，都要追加日期、功能名称、实现范围、验证结果；如果功能包含 API 接口，必须写清楚接口格式。

## 2026-05-18

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
