# Сайт №1 (локальный): статический сайт на nginx
FROM nginx:1.27-alpine

LABEL org.opencontainers.image.title="sapar-local-site" \
      org.opencontainers.image.description="СРО 1: локальный сайт-гид по Казахстану на nginx"

# Заменяем стандартный конфиг своим
RUN rm /etc/nginx/conf.d/default.conf
COPY nginx.conf /etc/nginx/conf.d/sapar.conf

# Сам сайт
COPY html/ /usr/share/nginx/html/

# Docker сам проверяет, что сайт отвечает
HEALTHCHECK --interval=30s --timeout=3s CMD wget -qO- http://127.0.0.1/health || exit 1

EXPOSE 80
