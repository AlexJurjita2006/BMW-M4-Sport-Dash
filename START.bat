@echo off
REM BMW M4 Dual Display System Launcher (Batch Version)
REM Simpler, more reliable way to start the simulators

cd /d "%~dp0"

echo.
echo ===============================================================================
echo.
echo   BMW M4 DUAL DISPLAY SYSTEM LAUNCHER
echo.
echo ===============================================================================
echo.
echo   DIMENSIUNI RECOMANDATE:
echo.
echo   [1] Standard (1100x600 ^& 1000x700) - RECOMMENDED
echo.
echo   [2] Large (1280x720 ^& 1200x800)
echo.
echo   [3] Small (1024x600 ^& 800x550)
echo.
echo   [4] Full HD (1920x1080 ^& 1600x1000)
echo.
echo ===============================================================================
echo.

set /p choice="Choose [1-4] (default 1): "

if "%choice%"=="" set choice=1
if "%choice%"=="1" (
    echo.
    echo Starting with Standard sizing (1100x600 and 1000x700)...
) else if "%choice%"=="2" (
    echo.
    echo Starting with Large sizing (1280x720 and 1200x800)...
) else if "%choice%"=="3" (
    echo.
    echo Starting with Small sizing (1024x600 and 800x550)...
) else if "%choice%"=="4" (
    echo.
    echo Starting with Full HD sizing (1920x1080 and 1600x1000)...
) else (
    echo.
    echo Invalid choice, using Standard sizing...
    set choice=1
)

echo.
echo Launching both simulators...
echo.

timeout /t 1 /nobreak

REM Try to run with Python from registry or available path
python launcher.py

if %errorlevel% neq 0 (
    echo.
    echo ERROR: Python not found or launcher.py could not run
    echo.
    echo Please make sure Python is installed and in your PATH
    echo You can download Python from: https://www.python.org/downloads/
    echo.
    pause
)
