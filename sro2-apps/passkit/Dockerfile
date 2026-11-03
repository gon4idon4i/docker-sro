# Приложение №1: консольная утилита для паролей (не веб-сервер)
FROM python:3.12-alpine

LABEL org.opencontainers.image.title="passkit" \
      org.opencontainers.image.description="СРО 2: генерация, проверка стойкости и хэширование паролей в терминале"

RUN adduser -D -u 1000 kit
WORKDIR /app
COPY passkit.py .

USER kit
ENV PYTHONUNBUFFERED=1 LANG=C.UTF-8

# ENTRYPOINT + аргументы из docker run:  docker run --rm <образ> gen -l 20
ENTRYPOINT ["python", "/app/passkit.py"]
