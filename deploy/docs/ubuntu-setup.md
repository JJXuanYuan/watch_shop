# 腾讯云 Ubuntu 24.04 后端部署说明

本文档以腾讯云 CVM Ubuntu 24.04 LTS 为目标环境，验收标准是服务器上可直接访问后端接口，而不是本地开发环境。

固定部署约束：

- 服务器公网 IP：`120.53.87.191`
- 登录用户：`root`
- 项目目录：`/opt/mall`
- 运行方式：`docker compose -f docker-compose.prod.yml ...`
- 迁移方式：`docker compose -f docker-compose.prod.yml exec -T mall_api alembic upgrade head`
- 种子方式：`docker compose -f docker-compose.prod.yml exec -T mall_api python -m scripts.seed_data`

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

## 4. 启动生产容器

```bash
cd /opt/mall
docker compose -f docker-compose.prod.yml up -d --build
```

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

## 7. 部署后验收

```bash
cd /opt/mall
bash deploy/scripts/post_deploy_check.sh http://120.53.87.191
```

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

## 8. 常见故障排查

### 8.1 访问服务器 IP 超时

- 检查腾讯云安全组是否放通 TCP 80
- 检查实例是否绑定公网 IP
- 检查 `docker compose -f docker-compose.prod.yml ps`

### 8.2 Nginx 返回 502

- 查看 API 容器日志：

  ```bash
  docker compose -f docker-compose.prod.yml logs mall_api --tail=100
  ```

- 确认 API 容器健康状态：

  ```bash
  docker compose -f docker-compose.prod.yml ps
  ```

- 确认 Nginx 配置中的 upstream 服务名是 `mall_api`

### 8.3 迁移失败

- 确认 MySQL 已健康：

  ```bash
  docker compose -f docker-compose.prod.yml exec -T mall_mysql sh -lc 'mysqladmin ping -h 127.0.0.1 -uroot -p"$MYSQL_ROOT_PASSWORD" --silent'
  ```

- 检查 `.env` 中数据库账号密码是否匹配
- 查看 API 日志中的 SQLAlchemy / Alembic 报错

### 8.4 种子数据未写入

- 手工重跑：

  ```bash
  docker compose -f docker-compose.prod.yml exec -T mall_api python -m scripts.seed_data
  ```

- 查看分类和商品接口返回是否为空

### 8.5 Docker 命令无权限

- 重新登录 SSH，或者暂时使用 `sudo docker ...`
- 确认当前用户已加入 `docker` 组：

  ```bash
  groups
  ```

## 9. 后续域名与 HTTPS 预留

- 当前 Nginx 配置优先支持 `http://服务器IP`
- 域名就绪后，修改 `deploy/nginx/mall.api.prod.conf` 的 `server_name`
- 后续再为 `443` 端口和证书路径补充配置
