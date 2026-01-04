#!/bin/bash
# Make sure latest code is deployed to raspbery pi drones
echo "[INFO] setting up environment if not already set up..."
cd /home/pi/drone-firefighting-system
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
if [ ! -f "venv/bin/activate" ]; then
    echo "[ERROR] virtual environment not found. Please run 'python3 -m venv venv' to create it."
    exit 1
fi
source venv/bin/activate
# for simplicity install all requirements though it can be grouped for Ground Sation, SD Drone and Fire Drone separately to reduce binary space
# pip install -r requirements.txt
pip install -r requirements/ground_station.txt
pip install -r requirements/sd_drone.txt
pip install -r requirements/fire_drone.txt
./deploy.sh

echo "[INFO] Starting quick demo..."
python tests.py --clean
python main.py --demo
python batch_mission.py --config config/batch_mission_areas_sequential.yaml --mode sequential --mission-delay 2
python batch_mission.py --config config/batch_mission_areas_parallel.yaml --mode parallel --workers 2 --mission-delay 1
echo "[INFO] Demo completed!"
