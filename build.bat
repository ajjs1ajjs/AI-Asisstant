@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

echo AI Coding IDE Build Script
echo ==========================

if exist ".venv312\Scripts\python.exe" (
    set "PYTHON_EXE=.venv312\Scripts\python.exe"
) else (
    set "PYTHON_EXE=python"
)

%PYTHON_EXE% --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python is not available.
    pause
    exit /b 1
)

set PYTHONIOENCODING=utf-8
%PYTHON_EXE% build_exe.py

if %errorlevel% equ 0 (
    echo.
    echo Build successful.
    echo Output: dist\AI_IDE_v6.0\
) else (
    echo.
    echo Build failed. Check the logs above.
)

pause
