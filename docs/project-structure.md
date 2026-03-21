# 项目结构说明

## apps

- `apps/admin`：管理后台前端工程，使用 Vue 3 + Vite + TypeScript + Element Plus。
- `apps/miniprogram`：uni-app 小程序工程，使用 Vue 3 + TypeScript，当前包含首页占位页。

## services

- `services/api`：后端服务工程，使用 FastAPI + SQLAlchemy，当前包含健康检查、商品分类/商品模型、Alembic 迁移与种子脚本。

## deploy

- `deploy/docker`：各服务 Dockerfile，当前包含 API 与 Nginx 生产镜像构建文件。
- `deploy/nginx`：Nginx 生产配置与欢迎页静态文件。
- `deploy/scripts`：服务器初始化、生产部署、完整离线镜像构建/导出/加载与部署后检查脚本。
- `deploy/docs`：部署相关文档，当前以腾讯云 Ubuntu 24.04 为主。

## 根目录文件

- `.env.example`：本地与生产共用的根级环境变量示例。
- `docker-compose.yml`：开发环境 Compose 配置。
- `docker-compose.prod.yml`：生产环境 Compose 配置。
- `docker-compose.offline.yml`：完整离线部署 Compose 配置。
- `README.md`：项目入口说明。
