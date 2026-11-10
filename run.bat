@echo off
setlocal
cd /d "%~dp0"

if exist "%~dp0clean_info.py" (
    set "SCRIPT=%~dp0clean_info.py"
) else (
    echo ERROR: clean_info.py was not found in this folder.
    echo Place this BAT file next to the Python script.
    pause
    exit /b 1
)

py -3 "%SCRIPT%"
set "STATUS=%ERRORLEVEL%"
if not "%STATUS%"=="0" echo ERROR: Python exited with code %STATUS%.
echo.
pause
exit /b %STATUS%
