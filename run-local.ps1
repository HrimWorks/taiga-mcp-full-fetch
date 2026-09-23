$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

$python = Join-Path $root ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    throw "Virtual environment not found at $python. Create it with: python -m venv .venv; .venv\Scripts\python.exe -m pip install -r requirements.txt"
}

$port = if ($env:PORT) { $env:PORT } else { "8010" }
$hostAddr = if ($env:MCP_BIND_HOST) { $env:MCP_BIND_HOST } else { "127.0.0.1" }

Write-Host "Starting Taiga MCP server on http://${hostAddr}:${port}"
Write-Host "  SSE:            http://${hostAddr}:${port}/sse/"
Write-Host "  Streamable HTTP: http://${hostAddr}:${port}/mcp/"
Write-Host "  Health:         http://${hostAddr}:${port}/healthz"

& $python -m uvicorn app:app --host $hostAddr --port $port
