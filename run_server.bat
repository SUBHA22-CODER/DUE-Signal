@echo off
setlocal
cd /d "%~dp0"

echo [DueSignal] Checking for existing process on port 8000...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000 ^| findstr LISTENING') do (
    echo [DueSignal] Freeing port 8000 (PID: %%a)...
    taskkill /F /PID %%a >nul 2>&1
)

if exist ".venv\Scripts\activate.bat" (
    echo [DueSignal] Activating virtual environment...
    call .venv\Scripts\activate.bat
) else (
    echo [DueSignal] Warning: .venv not found. Running with global python...
)

echo [DueSignal] Starting DueSignal MCP server on http://127.0.0.1:8000 ...
python -m mcp_server.server
pause
