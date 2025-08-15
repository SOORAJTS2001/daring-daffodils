@echo off
title WebSocket Mouse Controller - Complete Setup

echo ===================================================
echo    WebSocket Mouse Controller - Complete Setup
echo ===================================================
echo.
echo This script will start both required servers:
echo 1. WebSocket Server (localhost:8765)
echo 2. Mobile Page Server (localhost:8000)
echo.
echo Press any key to continue...
pause >nul

echo.
echo [1/2] Installing Python dependencies...
pip install -r requirements.txt

echo.
echo [2/2] Starting servers...
echo.

REM Start WebSocket server in a new window
echo Starting WebSocket Server...
start "WebSocket Server" cmd /k "echo WebSocket Server (localhost:8765) && python websocket_server.py"

REM Wait a moment for WebSocket server to start
timeout /t 2 >nul

REM Start Mobile Page server in a new window
echo Starting Mobile Page Server...
start "Mobile Page Server" cmd /k "echo Mobile Page Server (localhost:8000) && python start_mobile_server.py"

echo.
echo ✅ Both servers are starting!
echo.
echo Next steps:
echo 1. Load the browser extension from the 'browser_extension' folder
echo 2. Open http://localhost:8000/index.html for the mobile interface
echo 3. The WebSocket connection will be established automatically
echo.
echo 💡 Tip: Both server windows will stay open. Close them when done.
echo.
pause
