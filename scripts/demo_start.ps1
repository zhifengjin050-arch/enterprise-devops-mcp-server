# Check Docker and start MCP in read-only mode.
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "Created .env from .env.example"
}

$env:EXECUTE_TOOLS_ENABLED = "false"
python scripts/demo_list_tools.py
Write-Host "Starting docker compose (read-only default)..."
if (Get-Command docker -ErrorAction SilentlyContinue) {
    docker compose up -d --build
    Write-Host "MCP compose is up. Keep EXECUTE_TOOLS_ENABLED=false unless you have change control."
} else {
    Write-Host "docker not found; run: python scripts/run_devops_mcp.py"
}
