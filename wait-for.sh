#!/bin/bash
# wait-for.sh host:port command...
set -e

sleep 3  # Delay para DNS do Docker Compose

HOST_PORT="$1"
shift

HOST="${HOST_PORT%%:*}"
PORT="${HOST_PORT##*:}"

for i in {1..30}; do
  nc -z "$HOST" "$PORT" && break
  echo "Aguardando $HOST:$PORT... ($i/30)"
  sleep 1
done

if ! nc -z "$HOST" "$PORT"; then
  echo "Timeout ao aguardar $HOST:$PORT" >&2
  exit 1
fi

exec "$@" 