# CrossBorder Tech Collector

跨境电商技术信息采集服务。Python FastAPI + SQLite + Docker。

## 快速开始

### 本地开发

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 配置
cp .env.example .env
# 编辑 .env 设置 API_KEY

# 启动
DB_PATH=./data/collector.db API_KEY=your-key python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Docker 部署

```bash
cp .env.example .env
# 编辑 .env

docker-compose up -d
```

Docker volume `collector-data` 持久化 SQLite 数据，重启不丢失。

## API

### 认证

除 `/api/v1/health` 外，所有接口需要 Bearer Token 认证：

```
Authorization: Bearer <API_KEY>
```

### 接口列表

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/health` | 健康检查（无需认证） |
| GET | `/api/v1/articles` | 获取文章列表 |
| GET | `/api/v1/articles/stats` | 数据统计 |
| POST | `/api/v1/collect` | 手动触发采集 |

### 参数

**GET /api/v1/articles**

| 参数 | 类型 | 说明 |
|------|------|------|
| `date` | string | 按日期过滤 (YYYY-MM-DD) |
| `category` | string | 按分类过滤 |
| `source` | string | 按来源过滤（支持模糊匹配） |
| `limit` | int | 分页大小 (1-500, 默认 50) |
| `offset` | int | 偏移量 |

### 示例

```bash
# 健康检查
curl http://VPS:8000/api/v1/health

# 获取今日文章
curl -H "Authorization: Bearer YOUR_KEY" "http://VPS:8000/api/v1/articles?date=2026-05-11"

# 获取统计
curl -H "Authorization: Bearer YOUR_KEY" "http://VPS:8000/api/v1/articles/stats"

# 手动触发采集
curl -X POST -H "Authorization: Bearer YOUR_KEY" "http://VPS:8000/api/v1/collect"
```

## 数据源

数据源配置在 `config/sources.yaml`，支持热更新（改配置后重启容器生效）。

### 当前源（一期）

**RSS 源：**
- GitHub Blog（全量）
- OpenAI Blog（全量，近7天）
- WooCommerce Dev Blog（全量）
- 36kr（关键词：出海/跨境/电商/海外）
- Hacker News frontpage + Show HN（关键词：ecommerce/shopify/payment 等）
- TechCrunch（关键词：ecommerce/retail/marketplace）

**GitHub Trending：**
- ecommerce / scraper / translation / marketplace

### 添加新源

编辑 `config/sources.yaml`，按格式添加。RSS 源支持 `filter_mode: all`（全量）或 `filter_mode: keyword`（关键词过滤）。

## 定时采集

默认每天 UTC 06:00 自动采集，通过环境变量配置：

```
COLLECT_CRON_HOUR=6
COLLECT_CRON_MINUTE=0
```

## 项目结构

```
├── app/
│   ├── main.py          # FastAPI 入口 + API Key 鉴权
│   ├── db.py            # SQLite + SQLAlchemy
│   ├── models.py        # 数据模型
│   ├── collector.py     # 采集编排器
│   ├── scheduler.py     # APScheduler 定时任务
│   ├── api/v1/          # API 路由
│   ├── crawlers/        # 采集器（RSS / GitHub Trending）
│   └── filters/         # 关键词过滤
├── config/
│   └── sources.yaml     # 数据源配置
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `API_KEY` | （空=不鉴权） | API 认证密钥 |
| `DB_PATH` | `/app/data/collector.db` | SQLite 数据库路径 |
| `HOST` | `0.0.0.0` | 监听地址 |
| `PORT` | `8000` | 监听端口 |
| `COLLECT_CRON_HOUR` | `6` | 采集时间（小时 UTC） |
| `COLLECT_CRON_MINUTE` | `0` | 采集时间（分钟） |
| `LOG_LEVEL` | `INFO` | 日志级别 |
