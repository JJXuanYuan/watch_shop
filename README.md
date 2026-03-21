# Watch Shop 基础工程

当前仓库的优先目标是把商城后端稳定部署到腾讯云 Ubuntu 24.04 服务器，并以服务器运行为验收标准。

固定部署约束：

- 服务器：`120.53.87.191`
- 登录用户：`root`
- 项目目录：`/opt/mall`
- 运行方式：只允许 `docker compose -f docker-compose.prod.yml ...`
- 迁移和种子：只允许在 `mall_api` 容器内执行

## 当前阶段范围

- 后端：FastAPI + SQLAlchemy + Alembic
- 数据库：MySQL 8
- 缓存：Redis 7
- 反向代理：Nginx
- 部署：Docker Engine + docker compose plugin

当前已实现：

- `GET /health`
- `GET /api/v1/categories`
- `GET /api/v1/products`
- `GET /api/v1/products/{product_id}`
- Alembic 迁移
- 商品分类与商品种子数据
- 面向腾讯云 Ubuntu 24.04 的生产部署脚本

## 目录结构

```text
.
├─ apps/
│  ├─ miniprogram/
│  └─ admin/
├─ services/
│  └─ api/
├─ deploy/
│  ├─ docker/
│  ├─ nginx/
│  ├─ scripts/
│  └─ docs/
├─ docs/
├─ .env.example
├─ docker-compose.yml
├─ docker-compose.prod.yml
└─ README.md
```

详细目录说明见 `docs/project-structure.md`。

## 生产部署关键文件

- `services/api/Dockerfile`：API 生产镜像
- `docker-compose.prod.yml`：生产编排
- `deploy/docker/nginx/Dockerfile`：Nginx 生产镜像
- `deploy/nginx/mall.api.prod.conf`：Nginx 反向代理配置
- `deploy/scripts/bootstrap_ubuntu.sh`：Ubuntu 24.04 初始化脚本
- `deploy/scripts/deploy_prod.sh`：生产部署脚本
- `deploy/scripts/post_deploy_check.sh`：部署后验收脚本
- `deploy/docs/ubuntu-setup.md`：腾讯云 Ubuntu 24.04 部署说明

## 腾讯云服务器部署

### 1. 初始化服务器

先确保腾讯云安全组已经放通：

- TCP 22
- TCP 80
- TCP 443（当前可不启用，但建议预留）

登录服务器后执行：

```bash
ssh root@120.53.87.191
apt update
apt install -y git
git clone <your-repo-url> /opt/mall
cd /opt/mall
bash deploy/scripts/bootstrap_ubuntu.sh
```

如果你不是用 root 执行脚本，刚完成 Docker 安装并加入 `docker` 用户组后，需要重新登录 SSH 会话。

### 2. 配置生产环境变量

```bash
cd /opt/mall
cp .env.example .env
vim .env
```

至少修改这些值：

- `MYSQL_PASSWORD`
- `MYSQL_ROOT_PASSWORD`
- `API_SECRET_KEY`
- `NGINX_PORT`

### 3. 启动生产容器

```bash
cd /opt/mall
docker compose -f docker-compose.prod.yml up -d --build
```

### 4. 容器内执行迁移和种子

```bash
cd /opt/mall
docker compose -f docker-compose.prod.yml exec -T mall_api alembic upgrade head
docker compose -f docker-compose.prod.yml exec -T mall_api python -m scripts.seed_data
```

### 5. 一键部署方式

```bash
cd /opt/mall
bash deploy/scripts/deploy_prod.sh
```

这个脚本会自动：

- 尝试更新当前代码
- 检查 `.env`
- 启动 `mall_mysql` / `mall_redis` / `mall_api` / `mall_nginx`
- 等待 MySQL 与 API 可用
- 在 `mall_api` 容器内执行 Alembic 迁移
- 在 `mall_api` 容器内执行种子数据写入
- 输出接口验收地址

## 服务器验收命令

### 容器状态

```bash
cd /opt/mall
docker compose -f docker-compose.prod.yml ps
```

### API 日志

```bash
cd /opt/mall
docker compose -f docker-compose.prod.yml logs mall_api --tail=100
```

### 健康检查

```bash
curl http://127.0.0.1/health
curl http://120.53.87.191/health
```

### 分类接口

```bash
curl http://127.0.0.1/api/v1/categories
curl http://120.53.87.191/api/v1/categories
```

### 商品列表接口

```bash
curl http://127.0.0.1/api/v1/products
curl "http://120.53.87.191/api/v1/products?keyword=Chronos"
```

### 商品详情接口

```bash
curl http://127.0.0.1/api/v1/products/1
curl http://120.53.87.191/api/v1/products/1
```

### 脚本化验收

```bash
cd /opt/mall
bash deploy/scripts/post_deploy_check.sh http://120.53.87.191
```

## docker-compose.prod.yml 运行说明

生产编排包含四个服务：

- `mall_mysql`
- `mall_redis`
- `mall_api`
- `mall_nginx`

运行特性：

- API 通过服务名访问 MySQL 和 Redis
- MySQL 与 Redis 使用持久化卷
- API 与 Nginx 都设置了重启策略
- 所有服务都带健康检查
- 对外只暴露 Nginx `80` 端口
- 日志默认走 Docker `json-file`

## 容器化迁移与种子命令

### 迁移

```bash
docker compose -f docker-compose.prod.yml exec -T mall_api alembic upgrade head
```

### 查看迁移状态

```bash
docker compose -f docker-compose.prod.yml exec -T mall_api alembic current
docker compose -f docker-compose.prod.yml exec -T mall_api alembic history
```

### 种子数据

```bash
docker compose -f docker-compose.prod.yml exec -T mall_api python -m scripts.seed_data
```

## 常见故障排查

### 1. 访问服务器 IP 无响应

- 检查腾讯云安全组是否放通 TCP 80
- 检查服务器是否有公网 IP
- 检查 `docker compose -f docker-compose.prod.yml ps`

### 2. Nginx 返回 502

- 查看 API 日志：

  ```bash
  docker compose -f docker-compose.prod.yml logs mall_api --tail=100
  ```

- 确认 `mall_api` 健康状态正常
- 确认 `deploy/nginx/mall.api.prod.conf` 中上游服务名为 `mall_api`

### 3. MySQL 启动慢导致迁移失败

- 先确认 MySQL 是否健康：

  ```bash
  docker compose -f docker-compose.prod.yml exec -T mall_mysql sh -lc 'mysqladmin ping -h 127.0.0.1 -uroot -p"$MYSQL_ROOT_PASSWORD" --silent'
  ```

- 再执行迁移：

  ```bash
  docker compose -f docker-compose.prod.yml exec -T mall_api alembic upgrade head
  ```

### 4. 商品接口返回空数据

- 重新执行种子脚本：

  ```bash
  docker compose -f docker-compose.prod.yml exec -T mall_api python -m scripts.seed_data
  ```

- 再调用：

  ```bash
  curl http://127.0.0.1/api/v1/products
  ```

### 5. Docker 无权限

- 重新登录 SSH 会话
- 或临时改用 `sudo docker compose ...`

## 当前接口测试方式

当前阶段优先使用：

- `http://服务器IP/health`
- `http://服务器IP/api/v1/categories`
- `http://服务器IP/api/v1/products`
- `http://服务器IP/api/v1/products/1`

## 后续域名与 HTTPS 预留

- 当前 Nginx 配置优先支持服务器公网 IP 验证
- 后续绑定域名后，修改 `deploy/nginx/mall.api.prod.conf` 中的 `server_name`
- 再为 `443` 端口与证书配置补充 HTTPS

## 本地开发说明

如果仍需本地开发，可继续使用：

```bash
cp .env.example .env
docker compose up --build
```

或进入 `services/api` 本地执行：

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
python -m scripts.seed_data
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
