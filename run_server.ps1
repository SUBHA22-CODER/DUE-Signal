# DueSignal One-Click PowerShell Startup Script
$ErrorActionPreference = "SilentlyContinue"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   Starting DueSignal MCP Server        " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Check for existing process on port 8000
$conn = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue
if ($conn) {
    Write-Host "[!] Found existing process on port 8000 (PID: $($conn.OwningProcess)). Terminating..." -ForegroundColor Yellow
    Stop-Process -Id $conn.OwningProcess -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 1
}

if (Test-Path ".\.venv\Scripts\Activate.ps1") {
    Write-Host "[✓] Activating virtual environment..." -ForegroundColor Green
    & ".\.venv\Scripts\Activate.ps1"
}

Write-Host "[✓] Launching DueSignal on http://127.0.0.1:8000 ..." -ForegroundColor Green
Start-Process "http://127.0.0.1:8000/"

python -m mcp_server.server
