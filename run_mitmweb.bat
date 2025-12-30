@echo off
REM Run mitmweb (web UI) in isolated environment

echo Activating mitmproxy environment...
call mitmproxy_env\Scripts\activate.bat

echo Starting mitmweb on port 8080...
echo.
echo Web UI will be available at: http://127.0.0.1:8081
echo.
echo Configure your Android device:
echo   - Proxy Host: Your computer IP
echo   - Proxy Port: 8080
echo.
echo Press Ctrl+C to stop
echo.

mitmweb -p 8080

