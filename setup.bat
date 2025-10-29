@echo off
REM PyPSA Alternative - Automated Setup Script for Windows
REM This script automates the installation of dependencies and PyPSA-Earth

echo ==========================================
echo PyPSA Alternative - Setup Script
echo ==========================================
echo.

REM Check Python version
echo Checking Python version...
python --version
if %ERRORLEVEL% NEQ 0 (
    echo Error: Python not found. Please install Python 3.9 or higher.
    pause
    exit /b 1
)
echo.

REM Step 1: Install project requirements
echo ==========================================
echo Step 1: Installing Python dependencies
echo ==========================================
if exist requirements.txt (
    pip install -r requirements.txt
    if %ERRORLEVEL% NEQ 0 (
        echo Error: Failed to install dependencies
        pause
        exit /b 1
    )
    echo Dependencies installed successfully
) else (
    echo Error: requirements.txt not found
    pause
    exit /b 1
)
echo.

REM Step 2: Clone PyPSA-Earth
echo ==========================================
echo Step 2: Setting up PyPSA-Earth
echo ==========================================
if exist pypsa-earth (
    echo PyPSA-Earth directory already exists
    set /p update="Do you want to update it? (y/n): "
    if /i "%update%"=="y" (
        echo Updating PyPSA-Earth...
        cd pypsa-earth
        git pull
        pip install -e .
        cd ..
        echo PyPSA-Earth updated successfully
    ) else (
        echo Skipping PyPSA-Earth update
    )
) else (
    echo Cloning PyPSA-Earth repository...
    git clone https://github.com/pypsa-meets-earth/pypsa-earth.git pypsa-earth
    if %ERRORLEVEL% NEQ 0 (
        echo Error: Failed to clone PyPSA-Earth
        pause
        exit /b 1
    )

    echo Installing PyPSA-Earth...
    cd pypsa-earth
    pip install -e .
    if %ERRORLEVEL% NEQ 0 (
        echo Error: Failed to install PyPSA-Earth
        cd ..
        pause
        exit /b 1
    )
    cd ..
    echo PyPSA-Earth installed successfully
)
echo.

REM Step 3: Verify installation
echo ==========================================
echo Step 3: Verifying Installation
echo ==========================================

REM Check if pypsa-earth directory exists
if exist pypsa-earth\scripts (
    echo [OK] pypsa-earth directory structure
) else (
    echo [ERROR] pypsa-earth scripts directory not found
    pause
    exit /b 1
)

REM Check if earth_osm is importable
python -c "import earth_osm" 2>nul
if %ERRORLEVEL% EQU 0 (
    echo [OK] earth_osm module
) else (
    echo [ERROR] earth_osm module not found
    pause
    exit /b 1
)

REM Check if pypsa is importable
python -c "import pypsa" 2>nul
if %ERRORLEVEL% EQU 0 (
    echo [OK] pypsa module
) else (
    echo [ERROR] pypsa module not found
    pause
    exit /b 1
)

REM Check if geopandas is importable
python -c "import geopandas" 2>nul
if %ERRORLEVEL% EQU 0 (
    echo [OK] geopandas module
) else (
    echo [ERROR] geopandas module not found
    pause
    exit /b 1
)

echo.
echo ==========================================
echo Setup Complete!
echo ==========================================
echo.
echo You can now use the following utilities:
echo.
echo 1. Download PyPSA-Earth network data:
echo    python utils\download_pypsa_earth.py KR --voltage-min 220
echo.
echo 2. Geocode addresses:
echo    python utils\geocode_addresses.py data\2024 --jitter auto
echo.
echo For more information, see SETUP.md
echo.
pause
