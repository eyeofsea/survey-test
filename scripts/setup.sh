#!/usr/bin/env bash
# 강의용 레포 부트스트랩 스크립트 (macOS / Linux)
#
# 수행 작업:
#   1) Node 22+ 확인
#   2) corepack 으로 pnpm 활성화 후 vendor/qualtrics-mcp-server 의존성 설치
#   3) uv 로 prolific_mcp Python 의존성 동기화
#   4) .env 파일 존재 여부 확인 (없으면 .env.example 복사)
#   5) doctor.py 실행으로 API 토큰 점검

set -euo pipefail

cd "$(dirname "$0")/.."

step() { printf "\n\033[1;34m▶ %s\033[0m\n" "$*"; }
ok()   { printf "  \033[1;32m✓\033[0m %s\n" "$*"; }
warn() { printf "  \033[1;33m!\033[0m %s\n" "$*"; }
err()  { printf "  \033[1;31m✗\033[0m %s\n" "$*" >&2; }

# 1) Node 확인
step "Node.js 22+ 확인"
if ! command -v node >/dev/null; then
  err "node 가 설치되어 있지 않습니다. https://nodejs.org 에서 22 이상을 설치하세요."
  exit 1
fi
NODE_MAJOR=$(node -v | sed 's/v\([0-9]*\).*/\1/')
if [ "$NODE_MAJOR" -lt 22 ]; then
  err "Node $NODE_MAJOR 감지. Qualtrics MCP 서버는 Node 22+ 가 필요합니다."
  exit 1
fi
ok "node $(node -v)"

# 2) pnpm + Qualtrics MCP 의존성
step "Qualtrics MCP 서버 의존성 설치 (pnpm)"
if ! command -v pnpm >/dev/null; then
  if command -v corepack >/dev/null; then
    corepack enable >/dev/null 2>&1 || true
  fi
fi
if ! command -v pnpm >/dev/null; then
  warn "pnpm 을 찾을 수 없어 npm 으로 대체합니다."
  (cd vendor/qualtrics-mcp-server && npm install --silent)
else
  (cd vendor/qualtrics-mcp-server && pnpm install --silent)
fi
ok "qualtrics-mcp-server 설치 완료"

# 3) uv + Python 의존성
step "Prolific MCP 서버 의존성 설치 (uv)"
if ! command -v uv >/dev/null; then
  err "uv 가 설치되어 있지 않습니다. pip install uv 또는 https://docs.astral.sh/uv/ 참고."
  exit 1
fi
uv sync --quiet
ok "prolific_mcp 가상환경 동기화 완료"

# 4) .env 확인
step ".env 파일 확인"
if [ ! -f .env ]; then
  cp .env.example .env
  warn ".env 가 없어 .env.example 을 복사했습니다."
  warn "Claude Code 에서 '/setup-keys' 를 실행해 토큰을 입력하세요."
else
  ok ".env 존재"
fi

# 5) doctor
step "API 토큰 진단 (doctor.py)"
if uv run python scripts/doctor.py; then
  ok "준비 완료. Claude Code 에서 '/new-survey' 부터 시작하세요."
else
  warn "doctor 가 일부 실패했습니다. .env 토큰을 확인하고 '/setup-keys' 를 실행하세요."
fi
