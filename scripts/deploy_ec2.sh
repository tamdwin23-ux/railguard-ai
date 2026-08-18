#!/usr/bin/env bash
set -Eeuo pipefail

REPO="/home/ec2-user/railguard-ai"
ENV_FILE="/home/ec2-user/railguard-secrets.env"
IMAGE="railguard-ai:latest"
CONTAINER="railguard-api"
BACKUP="${CONTAINER}-rollback-$(date +%s)"

if [ ! -f "$ENV_FILE" ]; then
  echo "ERROR: RailGuard secrets file not found."
  exit 1
fi

cd "$REPO"

sudo -u ec2-user git fetch origin main
sudo -u ec2-user git checkout main
sudo -u ec2-user git pull --ff-only origin main

docker build -t "$IMAGE" .

if docker ps -a --format '{{.Names}}' | grep -qx "$CONTAINER"; then
  docker stop "$CONTAINER"
  docker rename "$CONTAINER" "$BACKUP"
fi

if ! docker run -d \
  --name "$CONTAINER" \
  --restart unless-stopped \
  --env-file "$ENV_FILE" \
  -p 8001:8001 \
  "$IMAGE"; then

  echo "New container failed to start. Rolling back."

  if docker ps -a --format '{{.Names}}' | grep -qx "$BACKUP"; then
    docker rename "$BACKUP" "$CONTAINER"
    docker start "$CONTAINER"
  fi

  exit 1
fi

HEALTHY=0

for i in {1..15}; do
  if curl -fsS http://127.0.0.1:8001/health >/dev/null; then
    HEALTHY=1
    break
  fi

  sleep 2
done

if [ "$HEALTHY" -ne 1 ]; then
  echo "Health check failed. Rolling back."

  docker logs --tail 50 "$CONTAINER" || true
  docker rm -f "$CONTAINER" || true

  if docker ps -a --format '{{.Names}}' | grep -qx "$BACKUP"; then
    docker rename "$BACKUP" "$CONTAINER"
    docker start "$CONTAINER"
  fi

  exit 1
fi

if docker ps -a --format '{{.Names}}' | grep -qx "$BACKUP"; then
  docker rm "$BACKUP"
fi

echo "RailGuard deployment successful."
