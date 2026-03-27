# Watch Shop 基础工程

当前仓库的优先目标是把商城后端稳定部署到腾讯云 Ubuntu 24.04 服务器，并以服务器运行为验收标准。

固定部署约束：

- 服务器：`120.53.87.191`
- 登录用户：`root`
- 项目目录：`/opt/mall`
- 在线/半离线运行方式：`docker compose -f docker-compose.prod.yml ...`
- 完整离线运行方式：`docker compose -f docker-compose.offline.yml ...`
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
- 完整离线镜像构建、导出与加载脚本

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
├─ docker-compose.offline.yml
└─ README.md
```

详细目录说明见 `docs/project-structure.md`。

## 生产部署关键文件

- `services/api/Dockerfile`：API 生产镜像
- `docker-compose.prod.yml`：生产编排
- `docker-compose.offline.yml`：完整离线编排
- `deploy/docker/nginx/Dockerfile`：Nginx 生产镜像
- `deploy/nginx/mall.api.prod.conf`：Nginx 反向代理配置
- `deploy/scripts/bootstrap_ubuntu.sh`：Ubuntu 24.04 初始化脚本
- `deploy/scripts/deploy_prod.sh`：生产部署脚本
- `deploy/scripts/post_deploy_check.sh`：部署后验收脚本
- `deploy/scripts/check_offline_prereqs.sh`：本地完整离线前置镜像预检脚本
- `deploy/scripts/check_offline_prereqs.ps1`：Windows PowerShell 完整离线前置镜像预检脚本
- `deploy/scripts/build_offline_images.sh`：本地完整离线业务镜像构建脚本
- `deploy/scripts/build_offline_images.ps1`：Windows PowerShell 完整离线业务镜像构建脚本
- `deploy/scripts/export_images.sh`：本地完整离线镜像导出脚本
- `deploy/scripts/export_images.ps1`：Windows PowerShell 完整离线镜像导出脚本
- `deploy/scripts/load_images_and_start.sh`：服务器离线镜像加载并启动脚本
- `deploy/scripts/offline_post_check.sh`：服务器离线部署验收脚本
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

### 3. 在线或半离线启动生产容器

```bash
cd /opt/mall
docker compose -f docker-compose.prod.yml up -d --build
```

如果服务器无法访问 Docker Hub、PyPI 或其他公网依赖，不要使用这一方式，直接跳到下方“完整离线部署方案（推荐）”。

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

该脚本走的是 `docker-compose.prod.yml`，适用于在线或半离线环境。

这个脚本会自动：

- 尝试更新当前代码
- 检查 `.env`
- 启动 `mall_mysql` / `mall_redis` / `mall_api` / `mall_nginx`
- 等待 MySQL 与 API 可用
- 在 `mall_api` 容器内执行 Alembic 迁移
- 在 `mall_api` 容器内执行种子数据写入
- 输出接口验收地址

## 完整离线部署方案（推荐）

当服务器无法访问 Docker Hub、PyPI 或其他公网依赖时，使用完整离线方案。业务镜像在本地预构建，服务器只做 `docker load` 和 `docker compose up -d`，不再执行 `build`。

### 1. 完整离线前置条件

本地机器在执行 build/export 之前，必须先具备这些基础镜像：

- `python:3.11.15-slim-bookworm`
- `nginx:1.27.5-alpine`
- `mysql:8.0.45`
- `redis:7.4.8-alpine`

同时：

- 缺少基础镜像时，不允许继续 `build_offline_images`
- 缺少 `mall_api:offline` 或 `mall_nginx:offline` 时，不允许继续 `export_images`

建议先运行预检脚本。

Linux/macOS:

```bash
cd /path/to/watch_shop
bash deploy/scripts/check_offline_prereqs.sh
```

Windows PowerShell:

```powershell
Set-Location C:\Users\JASON_XY\Desktop\watch_shop
powershell -ExecutionPolicy Bypass -File .\deploy\scripts\check_offline_prereqs.ps1
```

### 2. 本地构建业务镜像

Linux/macOS:

```bash
cd /path/to/watch_shop
bash deploy/scripts/build_offline_images.sh
```

Windows PowerShell:

```powershell
Set-Location C:\Users\JASON_XY\Desktop\watch_shop
powershell -ExecutionPolicy Bypass -File .\deploy\scripts\build_offline_images.ps1
```

本地会构建：

- `mall_api:offline`
- `mall_nginx:offline`

如果基础镜像缺失，脚本会直接失败并列出缺失镜像，不会再输出 success。

### 3. 本地导出统一离线包

Linux/macOS:

```bash
cd /path/to/watch_shop
bash deploy/scripts/export_images.sh
```

Windows PowerShell:

```powershell
Set-Location C:\Users\JASON_XY\Desktop\watch_shop
powershell -ExecutionPolicy Bypass -File .\deploy\scripts\export_images.ps1
```

也可以显式指定输出文件：

```powershell
Set-Location C:\Users\JASON_XY\Desktop\watch_shop
powershell -ExecutionPolicy Bypass -File .\deploy\scripts\export_images.ps1 -OutputTar mall_offline_bundle.tar
```

默认会生成：

```text
mall_offline_bundle.tar
```

当前离线包包含这些镜像标签：

- `mysql:8.0.45`
- `redis:7.4.8-alpine`
- `mall_api:offline`
- `mall_nginx:offline`

说明：

- `mall_api:offline` 已包含 `python:3.11.15-slim-bookworm` 的镜像层
- `mall_nginx:offline` 已包含 `nginx:1.27.5-alpine` 的镜像层
- 因此完整离线包不需要再额外单独导出 Python 或 Nginx 基础镜像
- 如果缺少上面任一镜像，导出脚本会直接失败，不会生成不完整 tar

### 4. 如果本地也无法访问 Docker Hub

不要继续执行 build/export。先在另一台可联网机器上准备基础镜像 tar，再回到本机 `docker load`。

示例：

```bash
docker pull python:3.11.15-slim-bookworm
docker pull nginx:1.27.5-alpine
docker pull mysql:8.0.45
docker pull redis:7.4.8-alpine
docker save -o mall_offline_base_images.tar \
  python:3.11.15-slim-bookworm \
  nginx:1.27.5-alpine \
  mysql:8.0.45 \
  redis:7.4.8-alpine
```

把 `mall_offline_base_images.tar` 传到当前构建机后执行：

```bash
docker load -i mall_offline_base_images.tar
```

然后重新运行：

```bash
bash deploy/scripts/check_offline_prereqs.sh
bash deploy/scripts/build_offline_images.sh
bash deploy/scripts/export_images.sh
```

### 5. 上传离线镜像包到服务器

```bash
scp mall_offline_bundle.tar root@120.53.87.191:/opt/mall/
```

### 6. 服务器加载镜像并启动

```bash
ssh root@120.53.87.191
cd /opt/mall
bash deploy/scripts/load_images_and_start.sh
```

也可以手工执行：

```bash
cd /opt/mall
docker load -i mall_offline_bundle.tar
docker compose -f docker-compose.offline.yml up -d
docker compose -f docker-compose.offline.yml ps
```

### 7. 容器内执行迁移和种子

```bash
cd /opt/mall
docker compose -f docker-compose.offline.yml exec -T mall_api alembic upgrade head
docker compose -f docker-compose.offline.yml exec -T mall_api python -m scripts.seed_data
```

### 8. 离线部署后验收

```bash
cd /opt/mall
bash deploy/scripts/offline_post_check.sh
```

## 半离线方案（仅兜底）

半离线方案依然使用 `docker-compose.prod.yml`，服务器执行的是：

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

这类方案只适用于服务器还能访问 Docker Hub、PyPI 等公网依赖的场景。它会在服务器端构建 `mall_api` 和 `mall_nginx`，不适合作为默认生产方案。

## 服务器验收命令

### 容器状态

```bash
cd /opt/mall
docker compose -f docker-compose.offline.yml ps
```

### API 日志

```bash
cd /opt/mall
docker compose -f docker-compose.offline.yml logs mall_api --tail=100
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
bash deploy/scripts/offline_post_check.sh
bash deploy/scripts/post_deploy_check.sh http://120.53.87.191
```

其中：

- `offline_post_check.sh` 对应 `docker-compose.offline.yml`
- `post_deploy_check.sh` 对应 `docker-compose.prod.yml`

## Compose 文件说明

- `docker-compose.prod.yml`：在线或半离线编排，服务器会 `build`
- `docker-compose.offline.yml`：完整离线编排，直接使用 `mall_api:offline` 和 `mall_nginx:offline`

完整离线编排包含四个服务：

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

### 完整离线迁移

```bash
docker compose -f docker-compose.offline.yml exec -T mall_api alembic upgrade head
```

### 在线或半离线迁移

```bash
docker compose -f docker-compose.prod.yml exec -T mall_api alembic upgrade head
```

### 查看迁移状态

```bash
docker compose -f docker-compose.offline.yml exec -T mall_api alembic current
docker compose -f docker-compose.offline.yml exec -T mall_api alembic history
docker compose -f docker-compose.prod.yml exec -T mall_api alembic current
docker compose -f docker-compose.prod.yml exec -T mall_api alembic history
```

### 完整离线种子数据

```bash
docker compose -f docker-compose.offline.yml exec -T mall_api python -m scripts.seed_data
```

### 在线或半离线种子数据

```bash
docker compose -f docker-compose.prod.yml exec -T mall_api python -m scripts.seed_data
```

## 常见故障排查

### 1. 访问服务器 IP 无响应

- 检查腾讯云安全组是否放通 TCP 80
- 检查服务器是否有公网 IP
- 检查 `docker compose -f docker-compose.offline.yml ps`

### 2. Nginx 返回 502

- 查看 API 日志：

  ```bash
  docker compose -f docker-compose.offline.yml logs mall_api --tail=100
  ```

- 确认 `mall_api` 健康状态正常
- 确认 `deploy/nginx/mall.api.prod.conf` 中上游服务名为 `mall_api`

### 3. MySQL 启动慢导致迁移失败

- 先确认 MySQL 是否健康：

  ```bash
  docker compose -f docker-compose.offline.yml exec -T mall_mysql sh -lc 'mysqladmin ping -h 127.0.0.1 -uroot -p"$MYSQL_ROOT_PASSWORD" --silent'
  ```

- 再执行迁移：

  ```bash
  docker compose -f docker-compose.offline.yml exec -T mall_api alembic upgrade head
  ```

### 4. 商品接口返回空数据

- 重新执行种子脚本：

  ```bash
  docker compose -f docker-compose.offline.yml exec -T mall_api python -m scripts.seed_data
  ```

- 再调用：

  ```bash
  curl http://127.0.0.1/api/v1/products
  ```

### 5. Docker 无权限

- 重新登录 SSH 会话
- 或临时改用 `sudo docker compose ...`

### 6. 服务器无法从 Docker Hub 拉镜像

- 先在本地执行 `bash deploy/scripts/check_offline_prereqs.sh`
- 在本地执行 `bash deploy/scripts/build_offline_images.sh`
- 再执行 `bash deploy/scripts/export_images.sh`
- 上传 `mall_offline_bundle.tar` 到服务器 `/opt/mall`
- 在服务器执行 `bash deploy/scripts/load_images_and_start.sh`
- 如需确认镜像已加载：

  ```bash
  docker images | grep -E 'mall_api|mall_nginx|mysql|redis'
  ```

### 7. 本地机器也无法从 Docker Hub 拉基础镜像

- 不要继续执行 `build_offline_images` 或 `export_images`
- 在另一台可联网机器上先准备：
  - `python:3.11.15-slim-bookworm`
  - `nginx:1.27.5-alpine`
  - `mysql:8.0.45`
  - `redis:7.4.8-alpine`
- 把这些基础镜像打成 tar 后传到当前构建机
- 在当前构建机执行 `docker load -i mall_offline_base_images.tar`
- 再重新执行：

  ```bash
  bash deploy/scripts/check_offline_prereqs.sh
  bash deploy/scripts/build_offline_images.sh
  bash deploy/scripts/export_images.sh
  ```

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
