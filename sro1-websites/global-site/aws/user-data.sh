#!/bin/bash
# User data для EC2 (Amazon Linux 2023).
# Вставляется в поле "Advanced details → User data" при создании инстанса:
# при первом старте сервер сам ставит Docker и запускает сайт на 80 порту.
set -e

IMAGE="abdigani/cloud-board:1.0"

dnf install -y docker
systemctl enable --now docker
usermod -aG docker ec2-user

docker run -d --name cloud-board \
  -p 80:8080 \
  -v board-data:/data \
  --restart always \
  "$IMAGE"
