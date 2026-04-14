@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ====================================
echo   AI Coding IDE v6.0
echo ====================================
echo.

if exist "dist\AI_IDE_v6.0\AI_IDE_v6.0.exe" (
    echo Launching built EXE...
    start "" "dist\AI_IDE_v6.0\AI_IDE_v6.0.exe"
) else if exist "main.py" (
    echo Launching from source...
    if exist ".venv312\Scripts\python.exe" (
        ".venv312\Scripts\python.exe" main.py
    ) else (
        python main.py
    )
) else (
    echo Error: project files not found.
    pause
    exit /b 1
)

echo.
echo Done
pause
