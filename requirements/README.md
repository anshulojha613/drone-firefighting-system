# Drone Firefighting System - Requirements

This directory contains split requirements files for different components to minimize installation size and optimize performance.

## Files Overview

| File | Purpose | Platform | Size | Key Features |
|------|---------|----------|------|-------------|
| `ground_station.txt` | Ground Station & Dashboard | Mac/Linux | Large | Web dashboard, network client, visualization |
| `sd_drone.txt` | Scouter Drone (SD) | Raspberry Pi | Medium | Thermal camera, fire detection, drone agent |
| `fire_drone.txt` | Firefighter Drone (FD) | Raspberry Pi | Small | Flight control, water pump, drone agent |

## Installation

### Ground Station (Mac/Linux)
```bash
cd /path/to/drone-firefighting-system
pip install -r requirements/ground_station.txt
```

### Scouter Drone (Raspberry Pi)
```bash
cd /home/pi/drone-firefighting-system
pip install -r requirements/sd_drone.txt
```

### Firefighter Drone (Raspberry Pi)
```bash
cd /home/pi/drone-firefighting-system
pip install -r requirements/fire_drone.txt
```

## Size Comparison

| Component | Packages | Approx. Size |
|-----------|----------|--------------|
| Ground Station | ~25 packages | ~200MB |
| Scouter Drone | ~18 packages | ~150MB |
| Firefighter Drone | ~12 packages | ~100MB |
| **Total (All)** | ~35 packages | ~300MB |

## Component Breakdown

### Ground Station
**Includes:**
- Web dashboard (Flask, Dash, Plotly)
- Database (SQLAlchemy, Alembic)
- Network client (requests, socketio)
- Visualization (matplotlib, folium)
- Testing framework (pytest)

**Excludes:**
- Drone hardware libraries
- Camera/thermal sensors
- TensorFlow/ML libraries

### Scouter Drone
**Includes:**
- Drone communication (pymavlink, dronekit)
- Thermal camera (MLX90640 libraries)
- Fire detection (OpenCV, Pillow)
- Environment sensors (DHT22)
- Drone agent (Flask, requests)

**Excludes:**
- Web dashboard
- Visualization libraries
- Testing framework
- TensorFlow (optional)

### Firefighter Drone
**Includes:**
- Drone communication (pymavlink, dronekit)
- Environment sensors (DHT22)
- Drone agent (Flask, requests)
- Basic data processing

**Excludes:**
- Web dashboard
- Camera/thermal sensors
- Image processing
- Visualization libraries
- TensorFlow/ML libraries

## Usage Examples

### Quick Demo Script
```bash
#!/bin/bash
# quick_demo.sh

# Install component-specific requirements
pip install -r requirements/ground_station.txt  # or sd_drone.txt / fire_drone.txt

echo "[INFO] Starting quick demo..."
python tests.py --clean
python main.py --demo
```

### Deployment Script
```bash
#!/bin/bash
# deploy.sh

# Detect platform and install appropriate requirements
if [[ "$HOSTNAME" == *"raspberry"* ]] || [[ "$HOSTNAME" == *"pi"* ]]; then
    # Raspberry Pi - install drone requirements
    if [[ "$1" == "sd" ]]; then
        pip install -r requirements/sd_drone.txt
    elif [[ "$1" == "fd" ]]; then
        pip install -r requirements/fire_drone.txt
    else
        echo "Usage: ./deploy.sh [sd|fd]"
        exit 1
    fi
else
    # Mac/Linux - install ground station requirements
    pip install -r requirements/ground_station.txt
fi
```

## Migration from Single requirements.txt

**Before:**
```bash
pip install -r requirements.txt  # ~300MB, all packages
```

**After:**
```bash
# Ground Station
pip install -r requirements/ground_station.txt  # ~200MB

# Scouter Drone  
pip install -r requirements/sd_drone.txt        # ~150MB

# Firefighter Drone
pip install -r requirements/fire_drone.txt      # ~100MB
```

## Troubleshooting

### Common Issues

1. **ImportError on Raspberry Pi**
   ```bash
   # Ensure you're using the correct requirements file
   pip install -r requirements/sd_drone.txt  # for scouter drone
   pip install -r requirements/fire_drone.txt  # for firefighter drone
   ```

2. **Camera not working on Scouter Drone**
   ```bash
   # Install system packages (not in requirements.txt)
   sudo apt install rpicam-apps
   sudo raspi-config  # Enable camera interface
   ```

3. **Dashboard not loading on Ground Station**
   ```bash
   # Ensure all web dependencies are installed
   pip install -r requirements/ground_station.txt
   ```

### Platform-Specific Notes

**Raspberry Pi:**
- Camera uses `rpicam-still` CLI tool (pre-installed)
- Thermal sensors require GPIO access (enable in raspi-config)
- TensorFlow optional (basic fire detection uses thermal thresholding)

**Mac/Linux:**
- Hardware sensors run in simulation mode
- Full dashboard and visualization capabilities
- No GPIO access needed

## Maintenance

To update requirements:
1. Update the specific requirements file
2. Test on target platform
3. Update this README if needed

For development/testing, use `requirements.txt` (all packages).
