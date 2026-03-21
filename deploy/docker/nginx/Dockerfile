FROM nginx:1.27.5-alpine

LABEL org.opencontainers.image.title="watch-shop-nginx"

COPY deploy/nginx/mall.api.prod.conf /etc/nginx/conf.d/default.conf
COPY deploy/nginx/index.html /usr/share/nginx/html/index.html

EXPOSE 80
