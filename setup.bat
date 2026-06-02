@echo off
setlocal enabledelayedexpansion

echo ========================================================
echo  Terminal AI Assistant - Windows Installer
echo ========================================================
echo.

:: Check for Python
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python was not found on your system.
    echo Please install Python 3.8 or newer from https://python.org and try again.
    echo Make sure to check the box "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

echo [INFO] Python found. Setting up virtual environment...
if not exist ".venv" (
    python -m venv .venv
    if !errorlevel! neq 0 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
) else (
    echo [INFO] Virtual environment already exists. Skipping creation.
)

echo [INFO] Installing/updating requirements in virtual environment...
call .venv\Scripts\activate.bat
python.exe -m pip install --upgrade pip
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install dependencies.
    pause
    exit /b 1
)

echo.
echo [INFO] Setup complete. Deploying global launcher shortcut...

:: Resolve User AppData PATH directory
set "LAUNCHER_DIR=%USERPROFILE%\AppData\Local\Microsoft\WindowsApps"
set "LAUNCHER_PATH=%LAUNCHER_DIR%\ai.bat"

if not exist "%LAUNCHER_DIR%" (
    echo [WARNING] Default WindowsApps directory was not found: %LAUNCHER_DIR%
    echo Creating alternative local execution script instead...
    set "LAUNCHER_PATH=%~dp0ai.bat"
)

:: Create launcher batch file with full reference paths
echo @echo off > "%LAUNCHER_PATH%"
echo "%~dp0.venv\Scripts\python.exe" "%~dp0ai.py" %%* >> "%LAUNCHER_PATH%"

echo [SUCCESS] Setup and installation complete.
echo ========================================================
echo.
echo Global launcher deployed to: %LAUNCHER_PATH%
echo.
echo You can now use the assistant from ANY PowerShell, CMD, or Terminal by typing:
echo   ai
echo.
echo Examples:
echo   ai                      - Starts beautiful interactive chat loop
echo   ai "what is DNS?"       - Runs a fast one-shot query
echo   ai -m deepseek          - Force interactive session using DeepSeek
echo   ai --clear              - Clears conversation history
echo.
echo Note: If you have a GitHub account, you can generate a free Personal Access Token
echo and set the GITHUB_TOKEN environment variable. Terminal AI will automatically detect it
echo and elevate you to ultra-stable Premium GitHub Models like GPT-4o, DeepSeek-R1, Llama 3.1.
echo.
pause
