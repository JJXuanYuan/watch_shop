# 腾讯云 Ubuntu 24.04 后端部署说明

本文档以腾讯云 CVM Ubuntu 24.04 LTS 为目标环境，验收标准是服务器上可直接访问后端接口，而不是本地开发环境。

固定部署约束：

- 服务器公网 IP：`120.53.87.191`
- 登录用户：`root`
- 项目目录：`/opt/mall`
- 在线/半离线运行方式：`docker compose -f docker-compose.prod.yml ...`
- 完整离线运行方式：`docker compose -f docker-compose.offline.yml ...`
- 迁移方式：只允许在 `mall_api` 容器内执行
- 种子方式：只允许在 `mall_api` 容器内执行

## 1. 服务器前置检查

- 系统版本：Ubuntu 24.04 LTS
- 建议规格：2 vCPU / 4 GB RAM 或更高
- 腾讯云安全组至少放通：
  - TCP 22：SSH
  - TCP 80：HTTP
  - TCP 443：当前可先不启用，后续给 HTTPS 预留

## 2. 首次初始化

先以 root 登录服务器：

```bash
ssh root@120.53.87.191
```

安装 Git 并拉取代码：

```bash
apt update
apt install -y git
git clone <your-repo-url> /opt/mall
cd /opt/mall
```

执行初始化脚本安装 Docker Engine 与 Docker Compose plugin：

```bash
bash deploy/scripts/bootstrap_ubuntu.sh
```

如果后续你切换到非 root 用户执行 Docker，再处理 `docker` 组重新登录问题；当前 root 用户不受这个限制。

## 3. 配置生产环境变量

```bash
cd /opt/mall
cp .env.example .env
vim .env
```

当前 `.env.example` 已预填 `120.53.87.191`，你主要修改：

- `MYSQL_PASSWORD`
- `MYSQL_ROOT_PASSWORD`
- `API_SECRET_KEY`
- `NGINX_PORT`

## 4. 在线或半离线启动生产容器

```bash
cd /opt/mall
docker compose -f docker-compose.prod.yml up -d --build
```

如果服务器无法访问 Docker Hub、PyPI 或其他公网依赖，不要使用这一方式，直接使用第 7 节“完整离线部署方案（推荐）”。

## 5. 容器内执行迁移与种子

```bash
cd /opt/mall
docker compose -f docker-compose.prod.yml exec -T mall_api alembic upgrade head
docker compose -f docker-compose.prod.yml exec -T mall_api python -m scripts.seed_data
```

## 6. 一键部署脚本

```bash
cd /opt/mall
bash deploy/scripts/deploy_prod.sh
```

该脚本会执行以下动作：

- 尝试拉取当前分支最新代码
- 检查 `.env`
- 启动或更新 `mall_mysql` / `mall_redis` / `mall_api` / `mall_nginx`
- 等待 MySQL 与 API 容器可用
- 在 `mall_api` 容器内执行 Alembic 迁移
- 在 `mall_api` 容器内写入种子数据
- 输出验收地址

## 7. 完整离线部署方案（推荐）

当腾讯云服务器无法访问 Docker Hub、PyPI 或其他公网依赖时，使用完整离线方案。业务镜像在本地预构建，服务器只做 `docker load` 和 `docker compose up -d`，不再执行 `build`。

### 7.1 完整离线前置条件

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

### 7.2 本地构建业务镜像

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

### 7.3 本地导出统一离线包

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

导出结果默认是：

```text
mall_offline_bundle.tar
```

离线包包含：

- `mysql:8.0.45`
- `redis:7.4.8-alpine`
- `mall_api:offline`
- `mall_nginx:offline`

说明：

- `mall_api:offline` 已包含 `python:3.11.15-slim-bookworm` 的镜像层
- `mall_nginx:offline` 已包含 `nginx:1.27.5-alpine` 的镜像层
- 所以服务器不需要再从公网拉取 Python 或 Nginx 基础镜像
- 如果缺少上面任一镜像，导出脚本会直接失败，不会生成不完整 tar

### 7.4 如果本地也无法访问 Docker Hub

不要继续执行 build/export。先在另一台可联网机器上准备基础镜像 tar，再回到当前构建机 `docker load`。

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

### 7.5 上传镜像包到服务器

```bash
scp mall_offline_bundle.tar root@120.53.87.191:/opt/mall/
```

### 7.6 服务器加载镜像并启动

```bash
ssh root@120.53.87.191
cd /opt/mall
bash deploy/scripts/load_images_and_start.sh
```

如果你更想手工执行：

```bash
cd /opt/mall
docker load -i mall_offline_bundle.tar
docker compose -f docker-compose.offline.yml up -d
docker compose -f docker-compose.offline.yml ps
```

### 7.7 容器内执行迁移与种子

```bash
cd /opt/mall
docker compose -f docker-compose.offline.yml exec -T mall_api alembic upgrade head
docker compose -f docker-compose.offline.yml exec -T mall_api python -m scripts.seed_data
```

### 7.8 离线部署后验收

```bash
cd /opt/mall
bash deploy/scripts/offline_post_check.sh
```

## 7A. 半离线方案（仅兜底）

半离线方案依然使用 `docker-compose.prod.yml`，服务器执行的是：

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

它仍会在服务器构建 `mall_api` 和 `mall_nginx`，如果服务器不能访问 PyPI 等公网依赖，这条链路会失败，所以只建议在网络受限较少时作为兜底方案。

## 8. 部署后验收

```bash
cd /opt/mall
bash deploy/scripts/offline_post_check.sh
bash deploy/scripts/post_deploy_check.sh http://120.53.87.191
```

其中：

- `offline_post_check.sh` 对应 `docker-compose.offline.yml`
- `post_deploy_check.sh` 对应 `docker-compose.prod.yml`

也可以手工验证：

```bash
curl http://127.0.0.1/health
curl http://127.0.0.1/api/v1/categories
curl http://127.0.0.1/api/v1/products
curl http://127.0.0.1/api/v1/products/1
curl http://120.53.87.191/health
curl http://120.53.87.191/api/v1/categories
curl http://120.53.87.191/api/v1/products
curl http://120.53.87.191/api/v1/products/1
```

## 9. 常见故障排查

### 9.1 访问服务器 IP 超时

- 检查腾讯云安全组是否放通 TCP 80
- 检查实例是否绑定公网 IP
- 检查 `docker compose -f docker-compose.offline.yml ps`

### 9.2 Nginx 返回 502

- 查看 API 容器日志：

  ```bash
  docker compose -f docker-compose.offline.yml logs mall_api --tail=100
  ```

- 确认 API 容器健康状态：

  ```bash
  docker compose -f docker-compose.offline.yml ps
  ```

- 确认 Nginx 配置中的 upstream 服务名是 `mall_api`

### 9.3 迁移失败

- 确认 MySQL 已健康：

  ```bash
  docker compose -f docker-compose.offline.yml exec -T mall_mysql sh -lc 'mysqladmin ping -h 127.0.0.1 -uroot -p"$MYSQL_ROOT_PASSWORD" --silent'
  ```

- 检查 `.env` 中数据库账号密码是否匹配
- 查看 API 日志中的 SQLAlchemy / Alembic 报错

### 9.4 种子数据未写入

- 手工重跑：

  ```bash
  docker compose -f docker-compose.offline.yml exec -T mall_api python -m scripts.seed_data
  ```

- 查看分类和商品接口返回是否为空

### 9.5 Docker 命令无权限

- 重新登录 SSH，或者暂时使用 `sudo docker ...`
- 确认当前用户已加入 `docker` 组：

  ```bash
  groups
  ```

### 9.6 离线镜像加载后仍然报缺少基础镜像

- 检查镜像是否已加载：

  ```bash
  docker images | grep -E 'mall_api|mall_nginx|mysql|redis'
  ```

- 重新执行：

  ```bash
  cd /opt/mall
  docker load -i mall_offline_bundle.tar
  ```

- 然后再次启动：

  ```bash
  docker compose -f docker-compose.offline.yml up -d
  ```

### 9.7 本地构建机也无法从 Docker Hub 拉基础镜像

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

## 10. 后续域名与 HTTPS 预留

- 当前 Nginx 配置优先支持 `http://服务器IP`
- 域名就绪后，修改 `deploy/nginx/mall.api.prod.conf` 的 `server_name`
- 后续再为 `443` 端口和证书路径补充配置
