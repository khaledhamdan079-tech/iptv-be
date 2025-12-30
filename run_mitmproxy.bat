@echo off
REM Run mitmproxy in isolated environment

echo Activating mitmproxy environment...
call mitmproxy_env\Scripts\activate.bat

echo Starting mitmproxy on port 8080...
echo.
echo Configure your Android device:
echo   - Proxy Host: Your computer IP
echo   - Proxy Port: 8080
echo.
echo Press Ctrl+C to stop
echo.

mitmproxy -p 8080

