# 项目文件结构规划

本项目采用标准 Python `src/` 布局，并将代码、配置模板、文档、测试、脚本与运行期数据隔离。

## 顶层结构

```text
qmt_data_api/
├─ src/qmt_data_api/       # Python 应用代码
├─ configs/                # 可提交的配置模板
├─ scripts/                # 开发、部署、运维和数据维护脚本
├─ tests/                  # 单元、集成、契约测试
├─ docs/                   # 架构、接口、部署和运维文档
├─ data/                   # 本地数据和缓存，不提交真实内容
├─ logs/                   # 本地日志，不提交真实内容
├─ var/                    # 运行期状态，不提交真实内容
├─ packaging/              # Windows 服务、任务计划和发布模板
└─ skills/                 # Agent 规范
```

## 代码分层

- `api/`：HTTP 和 WebSocket 协议层，只做参数接收、依赖注入和响应包装。
- `core/`：配置、日志、生命周期、错误码、统一响应等基础设施。
- `domain/`：业务语义层，表达行情、标的、交易等领域概念。
- `providers/qmt/`：唯一允许直接封装 `xtquant` 调用的位置。
- `cache/`：缓存抽象、缓存 key 和 TTL 策略。
- `tasks/`：历史补数、缓存预热、清理等后台任务。
- `auth/`：API Key、权限和 scope。
- `middleware/`：request_id、访问日志、鉴权、限流和异常处理。
- `observability/`：指标、追踪和审计。

## 运行期目录

- `data/`：行情缓存、快照、导出和临时文件。
- `logs/`：API、QMT 网关、计划任务和诊断日志。
- `var/`：pid、lock、任务水位、诊断报告和运行状态。

这些目录只提交说明文件和 `.gitkeep`，真实内容由 `.gitignore` 排除。

## 第一阶段边界

第一阶段只实现只读数据网关。可以保留 `domain/trading/` 和 `xttrader_adapter.py` 作为边界，但不得开放真实下单、撤单或资金操作。
