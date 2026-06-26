@echo off
echo ============================================
echo   MyHub Build Script
echo ============================================
echo.

echo [1/5] Installing Python dependencies...
call uv sync
if %ERRORLEVEL% neq 0 (
    echo ERROR: uv sync failed
    pause
    exit /b 1
)

echo.
echo [2/5] Installing frontend dependencies...
cd frontend
call npm install
if %ERRORLEVEL% neq 0 (
    echo ERROR: npm install failed
    cd ..
    pause
    exit /b 1
)

echo.
echo [3/5] Building frontend...
call npm run build
if %ERRORLEVEL% neq 0 (
    echo ERROR: npm run build failed
    cd ..
    pause
    exit /b 1
)
cd ..

echo.
echo [4/5] Building MyHub.exe with PyInstaller...
call uv run python build.py
if %ERRORLEVEL% neq 0 (
    echo ERROR: PyInstaller build failed
    pause
    exit /b 1
)

echo.
echo [5/5] Adding Windows Defender exclusion for dist folder...
powershell -Command "Start-Process powershell -Verb RunAs -ArgumentList '-Command Add-MpPreference -ExclusionPath \"%CD%\dist\"'" 2>nul
if %ERRORLEVEL% equ 0 (
    echo Exclusion added successfully.
) else (
    echo NOTE: If exclusion failed, manually add %CD%\dist to Windows Security exclusions.
)

echo.
echo ============================================
echo   Build complete!
echo   Output: dist\MyHub.exe
echo ============================================
pause
