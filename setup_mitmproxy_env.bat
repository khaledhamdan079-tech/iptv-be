@echo off
REM Create a separate virtual environment for mitmproxy to avoid dependency conflicts

echo Creating virtual environment for mitmproxy...
python -m venv mitmproxy_env

echo Activating virtual environment...
call mitmproxy_env\Scripts\activate.bat

echo Installing mitmproxy...
pip install --upgrade pip
pip install mitmproxy

echo.
echo ========================================
echo Setup complete!
echo ========================================
echo.
echo To use mitmproxy:
echo   1. Run: mitmproxy_env\Scripts\activate.bat
echo   2. Run: mitmproxy -p 8080
echo.
echo Or use the run_mitmproxy.bat script
echo.

pause

