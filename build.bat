@echo off
setlocal enabledelayedexpansion

echo 🚀 AI Coding IDE Build Script
echo ============================

:: Check for Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python is not installed or not in PATH.
    pause
    exit /b 1
)

:: Check for PyInstaller
pyinstaller --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠️ PyInstaller not found. Attempting to install...
    pip install pyinstaller
    if !errorlevel! neq 0 (
        echo ❌ Failed to install PyInstaller.
        pause
        exit /b 1
    )
)

:: Build Command
echo 📦 Building executable using ai_ide.spec...
pyinstaller --noconfirm ai_ide.spec

if %errorlevel% equ 0 (
    echo.
    echo ✅ Build successful!
    echo 📂 Output is in: dist\AI_Coding_IDE_v2\
) else (
    echo.
    echo ❌ Build failed. Please check the logs above.
)

pause
