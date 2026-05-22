# Claude Code (Windows) bootstrap script
# Usage: PowerShell -> ./scripts/setup.ps1
#
# Steps (mirrors setup.sh on macOS/Linux):
#   1) Verify Node.js 22+
#   2) Install Qualtrics MCP server deps via pnpm (corepack fallback to npm)
#   3) Sync Prolific MCP Python deps via uv
#   4) Ensure .env exists (copy from .env.example if missing)
#   5) Run doctor.py to check API tokens (Korean output handled by Python)

$ErrorActionPreference = "Stop"

# Force UTF-8 console so doctor.py Korean output is not garbled
try { [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new() } catch { }

# Move to repo root
Set-Location (Join-Path $PSScriptRoot "..")

function Step($msg) { Write-Host "`n>> $msg" -ForegroundColor Blue }
function Ok($msg)   { Write-Host "  [ok] $msg" -ForegroundColor Green }
function Warn($msg) { Write-Host "  [!]  $msg" -ForegroundColor Yellow }
function ErrMsg($msg) { Write-Host "  [x] $msg" -ForegroundColor Red }

# 1) Node.js 22+
Step "Check Node.js 22+"
$nodeCmd = Get-Command node -ErrorAction SilentlyContinue
if (-not $nodeCmd) {
    ErrMsg "node not installed. Get Node 22+ from https://nodejs.org"
    exit 1
}
$nodeVersion = & node -v
$nodeMajor = [int]($nodeVersion -replace '^v(\d+).*', '$1')
if ($nodeMajor -lt 22) {
    ErrMsg "Node $nodeMajor detected. Qualtrics MCP server requires Node 22+."
    exit 1
}
Ok "node $nodeVersion"

# 2) pnpm + Qualtrics MCP deps
Step "Install Qualtrics MCP server deps (pnpm)"
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
        Warn "pnpm not found, falling back to npm."
        & npm install --silent
    }
    if ($LASTEXITCODE -ne 0) { throw "qualtrics-mcp-server install failed" }
} finally {
    Pop-Location
}
Ok "qualtrics-mcp-server installed"

# 3) uv + Python deps
Step "Install Prolific MCP server deps (uv)"
$uvCmd = Get-Command uv -ErrorAction SilentlyContinue
if (-not $uvCmd) {
    ErrMsg "uv not installed."
    Write-Host "  Install via PowerShell: irm https://astral.sh/uv/install.ps1 | iex"
    Write-Host "  Or: pip install uv"
    exit 1
}
& uv sync --quiet
if ($LASTEXITCODE -ne 0) { ErrMsg "uv sync failed"; exit 1 }
Ok "prolific_mcp venv synced"

# 4) .env file
Step "Check .env"
if (-not (Test-Path .env)) {
    Copy-Item .env.example .env
    Warn ".env was missing. Copied .env.example -> .env"
    Warn "In Claude Code, run /setup-keys to fill the tokens."
} else {
    Ok ".env exists"
}

# 5) doctor (Korean output produced by Python)
Step "Run doctor.py (Korean output)"
& uv run python scripts/doctor.py
if ($LASTEXITCODE -eq 0) {
    Ok "Ready. In Claude Code, start with /new-survey."
} else {
    Warn "doctor reported issues. Check .env tokens and run /setup-keys in Claude Code."
}
