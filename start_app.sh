#!/bin/bash

# Navigate to the project root directory
cd "$(dirname "$0")"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Starting Voter List Extractor...${NC}"

# Determine which venv to use
if [ -d "venv312" ]; then
    source venv312/bin/activate
elif [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "Warning: No virtual environment found. Running with global python."
fi

echo -e "${GREEN}Launching Desktop App...${NC}"
python app.py
