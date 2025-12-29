@echo off
REM Script to set up virtual environment on Windows
echo Creating virtual environment...
python -m venv venv

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Upgrading pip...
python -m pip install --upgrade pip

echo Installing dependencies...
pip install -r requirements.txt

echo.
echo Setup complete! Virtual environment is activated.
echo To activate it in the future, run: venv\Scripts\activate
pause

