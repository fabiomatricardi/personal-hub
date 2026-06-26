@echo off
echo ============================================
echo   Windows Defender Folder Exclusion Tool
echo ============================================
echo.

if "%~1"=="" (
    echo Usage: exclude-defender.bat "C:\path\to\folder"
    echo.
    echo Example: exclude-defender.bat "C:\Fabio-AI\freeBuff\my_Hub\dist"
    echo.
    pause
    exit /b 1
)

set "FOLDER=%~1"

if not exist "%FOLDER%" (
    echo ERROR: Folder "%FOLDER%" does not exist.
    pause
    exit /b 1
)

echo Adding exclusion for: %FOLDER%
echo This will prompt for administrator access (UAC).
echo.

powershell -Command "Start-Process powershell -Verb RunAs -ArgumentList '-Command Add-MpPreference -ExclusionPath \"%FOLDER%\"'"

if %ERRORLEVEL% equ 0 (
    echo.
    echo Exclusion added successfully!
    echo %FOLDER% is now excluded from Windows Defender scanning.
) else (
    echo.
    echo ERROR: Failed to add exclusion. Make sure you approved the UAC prompt.
)

echo.
pause
