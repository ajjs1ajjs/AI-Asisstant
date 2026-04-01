@echo off
chcp 65001 >nul
echo ====================================
echo   🧠 AI Coding IDE v2.0
echo ====================================
echo.

cd /d "%~dp0"

if exist "dist\AI_Coding_IDE_v2.exe" (
    echo 🚀 Запуск EXE версії...
    start "" "dist\AI_Coding_IDE_v2.exe"
) else if exist "main.py" (
    echo 🐍 Запуск з вихідників...
    python main.py
) else (
    ❌ Помилка: Файли не знайдено!
    pause
    exit /b 1
)

echo.
echo ✅ Завершено
pause
