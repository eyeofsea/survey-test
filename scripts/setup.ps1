# Claude Code (Windows) 부트스트랩 스크립트
# 사용: PowerShell 에서 ./scripts/setup.ps1
#
# setup.sh 와 동일한 단계를 수행합니다:
#   1) Node.js 22+ 확인
#   2) pnpm (corepack) + Qualtrics MCP 의존성 설치
#   3) uv 로 Prolific MCP 의존성 동기화
#   4) .env 존재 여부 확인 (없으면 .env.example 복사)
#   5) doctor.py 실행

$ErrorActionPreference = "Stop"

# 레포 루트로 이동
Set-Location (Join-Path $PSScriptRoot "..")

function Step($msg) { Write-Host "`n▶ $msg" -ForegroundColor Blue }
function Ok($msg)   { Write-Host "  ✓ $msg" -ForegroundColor Green }
function Warn($msg) { Write-Host "  ! $msg" -ForegroundColor Yellow }
function ErrMsg($msg) { Write-Host "  ✗ $msg" -ForegroundColor Red }

# 1) Node.js 22+ 확인
Step "Node.js 22+ 확인"
$nodeCmd = Get-Command node -ErrorAction SilentlyContinue
if (-not $nodeCmd) {
    ErrMsg "node 가 설치되어 있지 않습니다. https://nodejs.org 에서 22 이상을 설치하세요."
    exit 1
}
$nodeVersion = & node -v
$nodeMajor = [int]($nodeVersion -replace '^v(\d+).*', '$1')
if ($nodeMajor -lt 22) {
    ErrMsg "Node $nodeMajor 감지. Qualtrics MCP 서버는 Node 22+ 가 필요합니다."
    exit 1
}
Ok "node $nodeVersion"

# 2) pnpm + Qualtrics MCP 의존성
Step "Qualtrics MCP 서버 의존성 설치 (pnpm)"
$pnpmCmd = Get-Command pnpm -ErrorAction SilentlyContinue
if (-not $pnpmCmd) {
    $corepackCmd = Get-Command corepack -ErrorAction SilentlyContinue
    if ($corepackCmd) {
        & corepack enable 2>$null
    }
    $pnpmCmd = Get-Command pnpm -ErrorAction SilentlyContinue
}
Push-Location vendor/qualtrics-mcp-server
try {
    if ($pnpmCmd) {
        & pnpm install --silent
    } else {
        Warn "pnpm 을 찾을 수 없어 npm 으로 대체합니다."
        & npm install --silent
    }
    if ($LASTEXITCODE -ne 0) { throw "qualtrics-mcp-server 의존성 설치 실패" }
} finally {
    Pop-Location
}
Ok "qualtrics-mcp-server 설치 완료"

# 3) uv + Python 의존성
Step "Prolific MCP 서버 의존성 설치 (uv)"
$uvCmd = Get-Command uv -ErrorAction SilentlyContinue
if (-not $uvCmd) {
    ErrMsg "uv 가 설치되어 있지 않습니다."
    Write-Host "  설치: PowerShell 에서 `irm https://astral.sh/uv/install.ps1 | iex`"
    Write-Host "  또는: pip install uv"
    exit 1
}
& uv sync --quiet
if ($LASTEXITCODE -ne 0) { ErrMsg "uv sync 실패"; exit 1 }
Ok "prolific_mcp 가상환경 동기화 완료"

# 4) .env 확인
Step ".env 파일 확인"
if (-not (Test-Path .env)) {
    Copy-Item .env.example .env
    Warn ".env 가 없어 .env.example 을 복사했습니다."
    Warn "Claude Code 에서 '/setup-keys' 를 실행해 토큰을 입력하세요."
} else {
    Ok ".env 존재"
}

# 5) doctor
Step "API 토큰 진단 (doctor.py)"
& uv run python scripts/doctor.py
if ($LASTEXITCODE -eq 0) {
    Ok "준비 완료. Claude Code 에서 '/new-survey' 부터 시작하세요."
} else {
    Warn "doctor 가 일부 실패했습니다. .env 토큰을 확인하고 '/setup-keys' 를 실행하세요."
}
