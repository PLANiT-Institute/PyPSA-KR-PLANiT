@echo off
REM ============================================
REM PyPSA Alternative - Automated Setup Script for Windows
REM ============================================
REM This script automates the installation of dependencies and PyPSA-Earth
REM
REM Requirements:
REM   - Python 3.9 or higher
REM   - Git (for cloning PyPSA-Earth)
REM   - Internet connection
REM
REM Usage:
REM   setup.bat
REM
REM ============================================

setlocal enabledelayedexpansion

echo ==========================================
echo PyPSA Alternative - Setup Script
echo ==========================================
echo.
echo This script will:
echo   1. Verify Python installation
echo   2. Install Python dependencies
echo   3. Clone and configure PyPSA-Earth
echo   4. Verify installation
echo.
echo Press any key to continue or Ctrl+C to cancel...
pause >nul
echo.

REM ============================================
REM Step 0: Check Prerequisites
REM ============================================
echo ==========================================
echo Step 0: Checking Prerequisites
echo ==========================================

REM Check Python installation
echo Checking Python installation...
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python not found. Please install Python 3.9 or higher.
    echo Download from: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Get and display Python version
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo [OK] Found Python !PYTHON_VERSION!

REM Check if Python version is 3.9+
REM Note: This is a simplified check
for /f "tokens=1,2 delims=." %%a in ("!PYTHON_VERSION!") do (
    set MAJOR=%%a
    set MINOR=%%b
)
if !MAJOR! LSS 3 (
    echo [ERROR] Python 3.9+ required, found !PYTHON_VERSION!
    pause
    exit /b 1
)
if !MAJOR! EQU 3 if !MINOR! LSS 9 (
    echo [ERROR] Python 3.9+ required, found !PYTHON_VERSION!
    pause
    exit /b 1
)

REM Check Git installation
echo Checking Git installation...
git --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [WARNING] Git not found. Git is required for PyPSA-Earth setup.
    echo Download from: https://git-scm.com/downloads
    set /p continue="Continue without Git? (y/n): "
    if /i not "!continue!"=="y" exit /b 1
) else (
    echo [OK] Git is installed
)

echo.

REM ============================================
REM Step 1: Install Python Dependencies
REM ============================================
echo ==========================================
echo Step 1: Installing Python Dependencies
echo ==========================================
echo This may take several minutes...
echo.

if not exist requirements.txt (
    echo [ERROR] requirements.txt not found in current directory
    echo Please run this script from the pypsa_alternative root directory
    pause
    exit /b 1
)

echo Installing packages from requirements.txt...
pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to install dependencies
    echo Try running: pip install --upgrade pip
    pause
    exit /b 1
)
echo [OK] Dependencies installed successfully
echo.

REM ============================================
REM Step 2: Setup PyPSA-Earth
REM ============================================
echo ==========================================
echo Step 2: Setting up PyPSA-Earth
echo ==========================================

if exist pypsa-earth (
    echo PyPSA-Earth directory already exists
    set /p update="Do you want to update it? (y/n): "
    if /i "!update!"=="y" (
        echo Updating PyPSA-Earth...
        cd pypsa-earth
        git pull
        if %ERRORLEVEL% NEQ 0 (
            echo [WARNING] Failed to update PyPSA-Earth
            cd ..
        ) else (
            echo [NOTE] PyPSA-Earth now ships without a setup.py/pyproject.
            echo Skipping editable install; dependencies already covered.
            cd ..
            echo [OK] PyPSA-Earth updated successfully
        )
    ) else (
        echo Skipping PyPSA-Earth update
    )
) else (
    echo Cloning PyPSA-Earth repository...
    git clone https://github.com/pypsa-meets-earth/pypsa-earth.git pypsa-earth
    if %ERRORLEVEL% NEQ 0 (
        echo [ERROR] Failed to clone PyPSA-Earth
        echo Please check your internet connection and Git installation
        pause
        exit /b 1
    )
    echo [NOTE] PyPSA-Earth now ships without a setup.py/pyproject.
    echo Skipping editable install; dependencies already covered.
    echo [OK] PyPSA-Earth cloned successfully
)
echo.

REM ============================================
REM Step 3: Create Required Directories
REM ============================================
echo ==========================================
echo Step 3: Creating Required Directories
echo ==========================================

if not exist data mkdir data
if not exist output mkdir output
if not exist cache mkdir cache
if not exist config mkdir config

echo [OK] Directory structure verified
echo.

REM ============================================
REM Step 4: Verify Installation
REM ============================================
echo ==========================================
echo Step 4: Verifying Installation
echo ==========================================

set VERIFICATION_FAILED=0

REM Check pypsa-earth directory structure
if exist pypsa-earth\scripts (
    echo [OK] pypsa-earth directory structure
) else (
    echo [ERROR] pypsa-earth scripts directory not found
    set VERIFICATION_FAILED=1
)

REM Check critical Python modules
echo Checking Python modules...

python -c "import pypsa" 2>nul
if %ERRORLEVEL% EQU 0 (
    echo [OK] pypsa module
) else (
    echo [ERROR] pypsa module not found
    set VERIFICATION_FAILED=1
)

python -c "import pandas" 2>nul
if %ERRORLEVEL% EQU 0 (
    echo [OK] pandas module
) else (
    echo [ERROR] pandas module not found
    set VERIFICATION_FAILED=1
)

python -c "import geopandas" 2>nul
if %ERRORLEVEL% EQU 0 (
    echo [OK] geopandas module
) else (
    echo [ERROR] geopandas module not found
    set VERIFICATION_FAILED=1
)

python -c "import earth_osm" 2>nul
if %ERRORLEVEL% EQU 0 (
    echo [OK] earth_osm module
) else (
    echo [WARNING] earth_osm module not found (optional for network download)
)

python -c "import geopy" 2>nul
if %ERRORLEVEL% EQU 0 (
    echo [OK] geopy module
) else (
    echo [WARNING] geopy module not found (optional for geocoding)
)

python -c "import matplotlib" 2>nul
if %ERRORLEVEL% EQU 0 (
    echo [OK] matplotlib module
) else (
    echo [WARNING] matplotlib module not found (optional for visualization)
)

echo.

if !VERIFICATION_FAILED! EQU 1 (
    echo ==========================================
    echo Installation Incomplete
    echo ==========================================
    echo Some required modules are missing.
    echo Try running: pip install -r requirements.txt --upgrade
    pause
    exit /b 1
)

REM ============================================
REM Setup Complete
REM ============================================
echo ==========================================
echo Setup Complete!
echo ==========================================
echo.
echo Your PyPSA Alternative environment is ready to use.
echo.
echo Next Steps:
echo.
echo 1. Run main analysis scripts:
echo    python main_singlenode.py
echo    python main_province.py
echo    python main_group.py
echo.
echo 2. Use utility tools:
echo    python utils\utils_gui.py
echo    python utils\geocode_addresses.py data\2024 --jitter auto
echo    python utils\download_pypsa_earth.py KR --voltage-min 220
echo.
echo 3. Check documentation in the documentation\ directory
echo.
echo For more information, see README.md
echo.
pause
