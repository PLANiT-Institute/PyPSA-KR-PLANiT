#!/bin/bash
# PyPSA Alternative - Automated Setup Script
# This script automates the installation of dependencies and PyPSA-Earth

set -e  # Exit on error

echo "=========================================="
echo "PyPSA Alternative - Setup Script"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Found Python version: $python_version"

# Check if Python 3.9+
required_version="3.9"
if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo -e "${RED}Error: Python 3.9 or higher is required${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Python version OK${NC}"
echo ""

# Step 1: Install project requirements
echo "=========================================="
echo "Step 1: Installing Python dependencies"
echo "=========================================="
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    echo -e "${GREEN}✓ Dependencies installed${NC}"
else
    echo -e "${RED}Error: requirements.txt not found${NC}"
    exit 1
fi
echo ""

# Step 2: Clone PyPSA-Earth
echo "=========================================="
echo "Step 2: Setting up PyPSA-Earth"
echo "=========================================="
if [ -d "pypsa-earth" ]; then
    echo -e "${YELLOW}PyPSA-Earth directory already exists${NC}"
    read -p "Do you want to update it? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Updating PyPSA-Earth..."
        cd pypsa-earth
        git pull
        echo "PyPSA-Earth now ships without a setup.py/pyproject."
        echo "Skipping editable install; dependencies already covered by requirements.txt."
        cd ..
        echo -e "${GREEN}✓ PyPSA-Earth updated${NC}"
    else
        echo "Skipping PyPSA-Earth update"
    fi
else
    echo "Cloning PyPSA-Earth repository..."
    git clone https://github.com/pypsa-meets-earth/pypsa-earth.git pypsa-earth

    echo "Installing PyPSA-Earth..."
    cd pypsa-earth
    echo "PyPSA-Earth now ships without a setup.py/pyproject."
    echo "Skipping editable install; dependencies already covered by requirements.txt."
    cd ..
    echo -e "${GREEN}✓ PyPSA-Earth installed${NC}"
fi
echo ""

# Step 3: Verify installation
echo "=========================================="
echo "Step 3: Verifying Installation"
echo "=========================================="

# Check if pypsa-earth directory exists
if [ -d "pypsa-earth/scripts" ]; then
    echo -e "${GREEN}✓ pypsa-earth directory structure OK${NC}"
else
    echo -e "${RED}✗ pypsa-earth scripts directory not found${NC}"
    exit 1
fi

# Check if earth_osm is importable
python3 -c "import earth_osm" 2>/dev/null
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ earth_osm module OK${NC}"
else
    echo -e "${RED}✗ earth_osm module not found${NC}"
    exit 1
fi

# Check if pypsa is importable
python3 -c "import pypsa" 2>/dev/null
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ pypsa module OK${NC}"
else
    echo -e "${RED}✗ pypsa module not found${NC}"
    exit 1
fi

# Check if geopandas is importable
python3 -c "import geopandas" 2>/dev/null
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ geopandas module OK${NC}"
else
    echo -e "${RED}✗ geopandas module not found${NC}"
    exit 1
fi

echo ""
echo "=========================================="
echo -e "${GREEN}Setup Complete!${NC}"
echo "=========================================="
echo ""
echo "You can now use the following utilities:"
echo ""
echo "1. Download PyPSA-Earth network data:"
echo "   python utils/download_pypsa_earth.py KR --voltage-min 220"
echo ""
echo "2. Geocode addresses:"
echo "   python utils/geocode_addresses.py data/2024 --jitter auto"
echo ""
echo "For more information, see SETUP.md"
echo ""
