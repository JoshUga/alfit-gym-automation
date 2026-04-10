#!/usr/bin/env bash
set -euo pipefail

# Generates a deterministic pair for EmailEngine API auth:
# 1) EMAILENGINE_API_TOKEN (raw 64-char hex token)
# 2) EENGINE_PREPARED_TOKEN (base64url msgpack with hashed token metadata)
#
# Usage:
#   scripts/generate_emailengine_tokens.sh
#   scripts/generate_emailengine_tokens.sh <64-char-hex-token>

if ! command -v docker >/dev/null 2>&1; then
  echo "docker is required" >&2
  exit 1
fi

RAW_TOKEN="${1:-}"
if [[ -z "$RAW_TOKEN" ]]; then
  if command -v openssl >/dev/null 2>&1; then
    RAW_TOKEN="$(openssl rand -hex 32)"
  else
    # Fallback from /dev/urandom if openssl is unavailable.
    RAW_TOKEN="$(head -c 32 /dev/urandom | od -An -tx1 | tr -d ' \n')"
  fi
fi

if [[ ! "$RAW_TOKEN" =~ ^[0-9a-fA-F]{64}$ ]]; then
  echo "Token must be exactly 64 hexadecimal characters." >&2
  exit 1
fi

if ! docker compose ps emailengine >/dev/null 2>&1; then
  echo "EmailEngine service is not available. Start it first with: docker compose up -d emailengine" >&2
  exit 1
fi

OUT="$({
  docker compose exec -T -e RAW_TOKEN="$RAW_TOKEN" emailengine node - <<'NODE'
const crypto = require('crypto');
const msgpack = require('msgpack5')();

const raw = (process.env.RAW_TOKEN || '').trim();
if (!/^[0-9a-fA-F]{64}$/.test(raw)) {
  console.error('Invalid raw token format. Must be 64 hex chars.');
  process.exit(1);
}

const normalized = raw.toLowerCase();
const id = crypto.createHash('sha256').update(Buffer.from(normalized, 'hex')).digest('hex');
const payload = {
  id,
  scopes: ['*'],
  description: 'alfit bootstrap token'
};
const prepared = msgpack.encode(payload).toString('base64url');

process.stdout.write(`EMAILENGINE_API_TOKEN=${normalized}\n`);
process.stdout.write(`EENGINE_PREPARED_TOKEN=${prepared}\n`);
NODE
} 2>/dev/null)"

if [[ -z "$OUT" ]]; then
  echo "Failed to generate token pair. Ensure emailengine container is running." >&2
  exit 1
fi

echo "$OUT"
echo

echo "Update these values in docker-compose.yml:"
echo "- email-service.environment.EMAILENGINE_API_TOKEN"
echo "- emailengine.environment.EENGINE_PREPARED_TOKEN"
