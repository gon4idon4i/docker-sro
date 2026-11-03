# Сайт №2 (глобальный): Python-сервер без внешних зависимостей
FROM python:3.12-alpine

LABEL org.opencontainers.image.title="cloud-board" \
      org.opencontainers.image.description="СРО 1: глобальный сайт для AWS EC2 — инфо о сервере + гостевая книга"

# Не запускаем сервер от root
RUN adduser -D -u 1000 web && mkdir /data && chown web /data

WORKDIR /app
COPY app.py .
COPY static/ static/

USER web
ENV PORT=8080 PYTHONUNBUFFERED=1
VOLUME /data
EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=3s CMD wget -qO- http://127.0.0.1:8080/health || exit 1

CMD ["python", "app.py"]
