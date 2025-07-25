#!/bin/bash

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' 

echo -e "${YELLOW}Setting up virtual environment in mind/${NC}"
cd mind
python3.10 -m venv env || { echo -e "${RED} Failed to create mind/env virtual envoronment${NC}"; exit 1; }
echo -e "${GREEN}Created mind/env${NC}"

echo -e "${YELLOW}Activating mind/env and installing requirements...${NC}"
source env/bin/activate
pip install --upgrade pip
pip install -r requirements.txt || { echo -e "${RED} Failed to install requirements for mind/env virtual environment${NC}"; exit 1; }
deactivate
cd ..

echo -e "${YELLOW}Setting up virtual environment in project root${NC}"
python3 -m venv env || { echo -e "${RED} Failed to create env virtual environment${NC}"; exit 1; }
echo -e "${GREEN}Created root env${NC}"

echo -e "${YELLOW}Activating root env and installing requirements...${NC}"
source env/bin/activate
pip install --upgrade pip
pip install -r requirements.txt || { echo -e "${RED} Failed to install requirements for env"; exit 1; }
deactivate
echo -e "${GREEN}Setup complete!${NC}"
