#!/usr/bin/env bash
set -e

# ANSI Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

clear
echo -e "${PURPLE}"
cat << "ASCII"
 __      ________ _____ _____ _____ 
 \ \    / /  ____|  __ \_   _/ ____|
  \ \  / /| |__  | |  | || || |     
   \ \/ / |  __| | |  | || || |     
    \  /  | |____| |__| || || |____ 
     \/   |______|_____/_____\_____|
                                    
       Local AI Operating System
ASCII
echo -e "${NC}"

echo -e "${CYAN}[*] Verifying System Dependencies...${NC}"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}[x] Python3 is not installed. Please install Python 3.10+${NC}"
    exit 1
fi

# Check Docker (for sandbox)
if ! command -v docker &> /dev/null; then
    echo -e "${RED}[x] Docker is not installed. Terminal Sandbox will fail.${NC}"
    exit 1
fi

# Check Ollama
if ! command -v ollama &> /dev/null; then
    echo -e "${RED}[x] Ollama is not installed. The brain is missing!${NC}"
    exit 1
fi

echo -e "${GREEN}[✓] Core dependencies verified.${NC}"

# Setup Virtual Environment
if [ ! -d "venv" ]; then
    echo -e "${CYAN}[*] Creating Python Virtual Environment...${NC}"
    python3 -m venv venv
fi

echo -e "${CYAN}[*] Activating Environment & Updating Dependencies...${NC}"
source venv/bin/activate
pip install -r requirements.txt --quiet || pip install streamlit requests orjson uvloop --quiet

echo -e "${GREEN}[✓] Environment ready.${NC}"

# Build the sandbox if it doesn't exist
if ! docker image inspect vedic-sandbox &> /dev/null; then
    echo -e "${CYAN}[*] Building isolated Terminal Sandbox (this only happens once)...${NC}"
    docker build -t vedic-sandbox . -q
    echo -e "${GREEN}[✓] Sandbox built.${NC}"
fi

echo -e "${PURPLE}=======================================${NC}"
echo -e "${PURPLE}🚀 IGNITING VEDIC OMNI-AGENT ENGINE...${NC}"
echo -e "${PURPLE}=======================================${NC}"

# Start Streamlit
streamlit run app.py
