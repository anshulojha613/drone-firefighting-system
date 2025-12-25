#!/bin/bash
# Deploy Drone Firefighting System to Raspberry Pi

# Configuration
PI_USER="anshul"
PI_HOST="192.168.7.195"  # Raspi IP using JaaK SSID
# PI_HOST="10.10.8.1"  # Raspi IP using FireDrone-GS SSID

PI_DIR="/home/anshul/drone-firefighting-system"
DRONE_ID="SD-001"

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
echo -e "${GREEN}✓ Connection OK${NC}"
echo ""

# Create directory on Pi
echo "Creating directory on Raspberry Pi..."
ssh $PI_USER@$PI_HOST "mkdir -p $PI_DIR"
echo -e "${GREEN}✓ Directory created${NC}"
echo ""

# Copy files
echo "Copying files to Raspberry Pi..."
rsync -avz --exclude 'venv' \
           --exclude '__pycache__' \
           --exclude '*.pyc' \
           --exclude '.git' \
           --exclude 'data' \
           --exclude 'database/dfs.db' \
           ./ $PI_USER@$PI_HOST:$PI_DIR/

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Files copied${NC}"
else
    echo -e "${RED}Error: File copy failed${NC}"
    exit 1
fi
echo ""

# Setup virtual environment
echo "Setting up Python virtual environment..."
ssh $PI_USER@$PI_HOST "cd $PI_DIR && python3 -m venv venv && source venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Virtual environment ready${NC}"
else
    echo -e "${YELLOW}⚠ Virtual environment setup may have issues${NC}"
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
cat << 'EOF'
sudo tee /etc/systemd/system/drone-agent.service > /dev/null << 'SERVICEEOF'
[Unit]
Description=Drone Agent for Firefighting System
After=network.target

[Service]
Type=simple
User=anshul
WorkingDirectory=/home/anshul/drone-firefighting-system
ExecStart=/home/anshul/drone-firefighting-system/venv/bin/python network/drone_agent.py --drone-id SD-001 --port 5001
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
echo "  ✅ DEPLOYMENT COMPLETE"
echo "======================================================================="
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
