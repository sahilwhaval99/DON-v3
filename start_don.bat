@echo off
REM ============================================================
REM  DON v3.0 launcher — double-click this file to start DON.
REM  It activates the virtual environment and runs the app.
REM ============================================================

REM Move to the folder this .bat file lives in (works no matter
REM where you double-click it from).
cd /d "%~dp0"

echo ============================================================
echo   Starting DON v3.0 ...
echo ============================================================

REM If the virtual environment doesn't exist yet, create it and
REM install dependencies (first-time setup).
if not exist ".venv\Scripts\activate.bat" (
    echo First run: setting up the environment. This may take a few minutes...
    python -m venv .venv
    call ".venv\Scripts\activate.bat"
    python -m pip install --upgrade pip
    pip install -r requirements.txt
) else (
    call ".venv\Scripts\activate.bat"
)

REM Launch DON (this also opens your browser to the dashboard).
python main.py

REM Keep the window open if DON stops or errors, so you can read messages.
echo.
echo DON has stopped. Press any key to close this window.
pause >nul
