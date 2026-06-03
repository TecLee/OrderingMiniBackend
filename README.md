# OrderingMini Backend

家庭私厨点菜系统后端 API — FastAPI + DeepSeek AI Function Calling + WebSocket 实时推送。

[![FastAPI](https://img.shields.io/badge/FastAPI-0.136-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python)](https://www.python.org/)
[![DeepSeek](https://img.shields.io/badge/AI-DeepSeek_Flash-536DFE)](https://platform.deepseek.com/)
[![License](https://img.shields.io/badge/license-MIT-green)](./LICENSE)

---

## 核心特性

- **AI Function Calling** — 7 个工具函数，AI 能直接操作购物车和下单（不是幻觉，是真实 DB 操作）
- **SSE 流式输出** — DeepSeek 逐字流式返回，打字机效果
- **WebSocket 实时推送** — 厨房看板零轮询，有新单秒级同步
- **双认证体系** — 管理员（admin_users）+ 顾客（users）各自独立 JWT
- **三端支持** — 顾客端 / 厨师端 / 管理员端，不同角色不同权限

## 快速启动

```bash
pip install -r requirements.txt
cp .env.example .env
# 编辑 .env: 替换 DEEPSEEK_API_KEY 和 JWT_SECRET
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

> **AI 智能体使用 DeepSeek Flash（`deepseek-chat`）**。去 [platform.deepseek.com](https://platform.deepseek.com) 申请 API Key，填入 `.env` 的 `DEEPSEEK_API_KEY`。

首次启动自动建库并创建种子数据：
- 管理员 `admin` / `admin123`
- 厨师 `chef` / `chef123`
- 5 个默认菜品分类

## API 路由

| 路径 | 说明 |
|------|------|
| `POST /api/v1/miniapp/ai/chat` | **AI 对话（SSE 流式 + Function Calling）** |
| `POST /api/v1/miniapp/auth/mock-login` | 顾客模拟登录 |
| `GET/POST /api/v1/miniapp/cart` | 购物车 CRUD |
| `POST /api/v1/miniapp/orders` | 下单 |
| `POST /api/v1/admin/auth/login` | 管理员/厨师登录 |
| `GET/PUT /api/v1/admin/orders` | 订单管理 |
| `PUT /api/v1/admin/orders/{id}/status` | 订单状态变更（→ 触发 WS 广播） |
| `WS /ws/kitchen` | **厨房看板 WebSocket** |

## AI Function Calling 流程

```
POST /api/v1/miniapp/ai/chat  →  _handle_tool_calls()
                                          │
                              ① 检测用户意图（关键词匹配）
                              ┌─ needs_action=True → tool_choice="required"
                              │
                              ② 调用 DeepSeek API（带 tools 定义）
                                          │
                              AI 返回 tool_calls? ──Yes──▶ 执行工具（DB读写）
                                          │                    │
                                          │No           结果回传 AI ──┐
                                          │                              │
                              ③ final text → SSE 流式返回前端    ◀──────┘
```

7 个工具：`search_dishes` · `get_cart` · `add_to_cart` · `update_cart_item` · `remove_from_cart` · `set_order_note` · `place_order`

> 详细架构：前端仓库 [`docs/AI-Kitchen-Butler.md`](https://github.com/TecLee/OrderingWeb/blob/main/docs/AI-Kitchen-Butler.md)

## 项目结构

```
├── main.py              # FastAPI 入口 + WebSocket 端点注册
├── config.py            # pydantic-settings 配置（读 .env）
├── database.py          # SQLAlchemy 连接
├── routers/
│   ├── miniapp_ai.py    # AI 对话核心 — Function Calling 循环
│   ├── miniapp_auth.py  # 顾客登录
│   ├── miniapp_cart.py  # 购物车
│   ├── miniapp_orders.py # 下单（+ WebSocket 通知）
│   ├── admin_auth.py    # 管理员登录
│   ├── admin_orders.py  # 订单管理（+ 状态变更广播）
│   ├── admin_dishes.py  # 菜品 CRUD
│   ├── admin_categories.py
│   ├── admin_users.py
│   └── admin_stats.py
├── models/              # SQLAlchemy 数据模型
├── schemas/             # Pydantic 校验
├── middleware/           # JWT 认证中间件（admin + user 两套）
├── utils/
│   ├── ws_manager.py    # WebSocket 连接管理器
│   ├── init_db.py       # 建库 + 种子数据
│   └── security.py      # 密码哈希
└── requirements.txt
```

## 部署

生产环境 systemd + Nginx 反向代理：

```ini
[Service]
WorkingDirectory=/opt/ordering-backend
ExecStart=uvicorn main:app --host 127.0.0.1 --port 8000
```

```nginx
location /api/ { proxy_pass http://127.0.0.1:8000/api/; }
location /ws/  {
    proxy_pass http://127.0.0.1:8000/ws/;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_read_timeout 86400s;
}
```

## 前端仓库

[OrderingWeb](https://github.com/TecLee/OrderingWeb) — Vue 3 · Element Plus · PWA

---

*Built with ☕ and Claude Code*
