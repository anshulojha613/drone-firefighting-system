#!/bin/bash
# Deploy Drone Firefighting System to Raspberry Pi

# Configuration
PI_USER="anshul"
#PI_HOST="192.168.7.195"  # Raspi IP using JaaK SSID
PI_HOST="10.10.8.1"  # Raspi IP using FireDrone-GS SSID

PI_DIR="/home/anshul/drone-firefighting-system"
DRONE_ID="SD-001"

# Drone type for requirements installation
# Options: "sd" (Scouter Drone), "fd" (Firefighter Drone), "gs" (Ground Station)
DRONE_TYPE="sd"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --drone-type)
            DRONE_TYPE="$2"
            shift 2
            ;;
        --pi-user)
            PI_USER="$2"
            shift 2
            ;;
        --pi-host)
            PI_HOST="$2"
            shift 2
            ;;
        --drone-id)
            DRONE_ID="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --drone-type TYPE    Drone type: sd (Scouter), fd (Firefighter), gs (Ground Station)"
            echo "  --pi-user USER       Raspberry Pi username (default: anshul)"
            echo "  --pi-host HOST       Raspberry Pi IP address (default: 10.10.8.1)"
            echo "  --drone-id ID        Drone ID (default: SD-001)"
            echo "  --help               Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0 --drone-type sd                    # Deploy Scouter Drone"
            echo "  $0 --drone-type fd --pi-host 10.10.8.2 # Deploy Firefighter Drone to different Pi"
            echo "  $0 --drone-type gs                    # Deploy Ground Station"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "======================================================================="
echo "  🚁 DRONE FIREFIGHTING SYSTEM - RASPBERRY PI DEPLOYMENT"
echo "======================================================================="
echo ""

# Check if PI_HOST is set
if [ -z "$PI_HOST" ]; then
    echo -e "${RED}Error: PI_HOST not set${NC}"
    echo "Please edit this script and set PI_HOST to your Raspberry Pi IP address"
    echo "Example: PI_HOST=\"10.10.8.100\""
    exit 1
fi

echo "Target: $PI_USER@$PI_HOST"
echo "Directory: $PI_DIR"
echo "Drone ID: $DRONE_ID"
echo "Drone Type: $DRONE_TYPE"
echo ""

# Test connection
echo "Testing connection to Raspberry Pi..."
if ! ping -c 1 -W 2 $PI_HOST > /dev/null 2>&1; then
    echo -e "${RED}Error: Cannot reach $PI_HOST${NC}"
    echo "Please check:"
    echo "  1. Raspberry Pi is powered on"
    echo "  2. Connected to same network (FireDrone-GS)"
    echo "  3. IP address is correct"
    exit 1
fi
echo -e "${GREEN}Connection OK${NC}"
echo ""

# Create directory on Pi
echo "Creating directory on Raspberry Pi..."
ssh $PI_USER@$PI_HOST "mkdir -p $PI_DIR"
echo -e "${GREEN}Directory created${NC}"
echo ""

# Copy files (incremental - only changed files)
echo "Syncing files to Raspberry Pi (incremental)..."
echo "Excluding: venv, __pycache__, .git, data, models, ML files, database"
echo ""

rsync -avz \
    --checksum \
    --update \
    --progress \
    --exclude 'venv/' \
    --exclude '__pycache__/' \
    --exclude '*.pyc' \
    --exclude '*.pyo' \
    --exclude '.git/' \
    --exclude '.gitignore' \
    --exclude 'data/' \
    --exclude 'database/dfs.db' \
    --exclude 'database/dfs.db-journal' \
    --exclude 'models/' \
    --exclude 'ml_training/' \
    --exclude '*.h5' \
    --exclude '*.tflite' \
    --exclude '*.keras' \
    --exclude '*.pt' \
    --exclude '*.pth' \
    --exclude '*.onnx' \
    --exclude 'logs/*.log' \
    --exclude '.DS_Store' \
    --exclude '*.swp' \
    --exclude '*.swo' \
    --exclude '.vscode/' \
    --exclude '.idea/' \
    --include '*.py' \
    --include '*.yaml' \
    --include '*.yml' \
    --include '*.txt' \
    --include '*.md' \
    --include '*.sh' \
    --include '*.json' \
    ./ $PI_USER@$PI_HOST:$PI_DIR/

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}Files synced (only changed files copied)${NC}"
else
    echo -e "${RED}Error: File sync failed${NC}"
    exit 1
fi
echo ""

# Setup virtual environment
echo "Setting up Python virtual environment..."

# Determine requirements file based on drone type
case "$DRONE_TYPE" in
    "sd")
        REQUIREMENTS_FILE="requirements/sd_drone.txt"
        echo "Installing Scouter Drone requirements (thermal camera, fire detection)..."
        ;;
    "fd")
        REQUIREMENTS_FILE="requirements/fire_drone.txt"
        echo "Installing Firefighter Drone requirements (flight control, water pump)..."
        ;;
    "gs")
        REQUIREMENTS_FILE="requirements/ground_station.txt"
        echo "Installing Ground Station requirements (dashboard, network client)..."
        ;;
    *)
        echo -e "${RED}Error: Invalid DRONE_TYPE '$DRONE_TYPE'${NC}"
        echo "Valid options: sd (Scouter Drone), fd (Firefighter Drone), gs (Ground Station)"
        exit 1
        ;;
esac

# Install requirements
ssh $PI_USER@$PI_HOST "cd $PI_DIR && python3 -m venv venv && source venv/bin/activate && pip install --upgrade pip && pip install -r $REQUIREMENTS_FILE"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}Virtual environment ready${NC}"
else
    echo -e "${YELLOW}Virtual environment setup may have issues${NC}"
fi
echo ""

# Create systemd service (manual step - requires sudo)
echo ""
echo "======================================================================="
echo "  SYSTEMD SERVICE SETUP (Manual Step)"
echo "======================================================================="
echo ""
echo "To enable auto-start on boot, run these commands on the Raspberry Pi:"
echo ""
echo -e "${YELLOW}ssh $PI_USER@$PI_HOST${NC}"
echo ""
echo "Then run:"
echo ""
cat << EOF
sudo tee /etc/systemd/system/drone-agent.service > /dev/null << 'SERVICEEOF'
[Unit]
Description=Drone Agent for Firefighting System ($DRONE_TYPE)
After=network.target

[Service]
Type=simple
User=$PI_USER
WorkingDirectory=$PI_DIR
ExecStart=$PI_DIR/venv/bin/python network/drone_agent.py --drone-id $DRONE_ID --port 5001
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
SERVICEEOF

sudo systemctl daemon-reload
sudo systemctl enable drone-agent
sudo systemctl start drone-agent
sudo systemctl status drone-agent
EOF
echo ""
echo "======================================================================="

echo ""
echo "======================================================================="
echo "  DEPLOYMENT COMPLETE"
echo "======================================================================="
echo ""
echo "Deployment Summary:"
echo "  Target: $PI_USER@$PI_HOST"
echo "  Directory: $PI_DIR"
echo "  Drone Type: $DRONE_TYPE"
echo "  Drone ID: $DRONE_ID"
echo "  Requirements: $REQUIREMENTS_FILE"
echo ""
echo "Files deployed to: $PI_HOST:$PI_DIR"
echo ""
echo "Next steps:"
echo ""
echo "OPTION 1: Quick Test (Manual Start)"
echo "  1. SSH to Raspberry Pi:"
echo "     ssh $PI_USER@$PI_HOST"
echo ""
echo "  2. Start drone agent manually:"
echo "     cd $PI_DIR"
echo "     source venv/bin/activate"
echo "     python network/drone_agent.py --drone-id $DRONE_ID --port 5001"
echo ""
echo "  3. Test from ground station (new terminal):"
echo "     python test_network.py --drone-id $DRONE_ID --ip $PI_HOST --port 5001"
echo ""
echo "OPTION 2: Auto-Start Service (see instructions above)"
echo ""
echo "To view logs:"
echo "  ssh $PI_USER@$PI_HOST"
echo "  tail -f $PI_DIR/logs/*.log"
echo ""
echo "======================================================================="
