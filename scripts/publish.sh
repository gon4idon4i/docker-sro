#!/usr/bin/env bash
# Собирает все 4 образа сразу под amd64 и arm64 и отправляет на Docker Hub.
# Две архитектуры нужны, чтобы образы запускались и на обычном ПК/AWS (amd64),
# и на Mac с Apple Silicon (arm64).
#
#   docker login
#   DOCKER_USER=логин ./scripts/publish.sh
set -euo pipefail

: "${DOCKER_USER:?укажите логин Docker Hub: DOCKER_USER=логин ./scripts/publish.sh}"
TAG="${TAG:-1.0}"
PLATFORMS="linux/amd64,linux/arm64"
cd "$(dirname "$0")/.."

build() {  # имя_образа папка
  echo "==> $DOCKER_USER/$1:$TAG"
  docker buildx build --platform "$PLATFORMS" \
    -t "$DOCKER_USER/$1:$TAG" -t "$DOCKER_USER/$1:latest" \
    --push "$2"
}

build sapar-local-site sro1-websites/local-site
build cloud-board      sro1-websites/global-site
build passkit          sro2-apps/passkit
build docker-quiz      sro2-apps/docker-quiz

echo "Готово: https://hub.docker.com/u/$DOCKER_USER"
