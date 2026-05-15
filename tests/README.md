# 测试说明

测试默认不得依赖真实 QMT 登录状态、真实账户、真实持仓或真实交易数据。

- `unit/`：纯函数、配置、schema、缓存策略测试。
- `integration/`：API 与 QMT 适配层集成测试，可使用 mock。
- `contract/`：接口响应结构与兼容性测试。
- `fixtures/`：只允许提交小体积脱敏样例数据。
