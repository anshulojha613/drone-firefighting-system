## Quick Start

### Installation
```bash
cd drone_firefighting_system
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# If you hit DroneKit issues on Python 3.13:
python ./fix_dronekit_py313.py
```

### Run Demo (No Hardware Needed)
```bash
# Simulate a scouting mission
python main.py --demo

# Launch dashboard
python main.py --dashboard
# Open: http://localhost:8050
```

### Field Operation (With Hardware)
```bash
# Connect Pixhawk via USB or GPIO UART
python main.py --real-flight --mission scout

# Monitor from ground station
python main.py --dashboard
```



## Project Structure

```
drone_firefighting_system/
├── database/              # SQLite models for missions, detections
├── mission_control/       # Core orchestration logic
├── scouter_drone/         # Scout drone simulation & control
├── firefighter_drone/     # Suppression drone simulation
├── ml_training/           # Fire detection CNN (MobileNetV2)
├── network/               # WiFi communication layer
├── dashboard/             # Real-time monitoring (Dash/Plotly)
├── config/                # System configuration
├── data/                  # Mission data, thermal recordings
├── logs/                  # System logs
└── main.py               # Entry point
```

## Key Learnings

### Thermal Camera Coverage
Using MLX90640 (110° FOV), here's actual ground coverage:

| Altitude | Coverage Area | Pixel Size | Can Detect |
|----------|---------------|------------|------------|
| 20 ft | 36 × 27 ft | 1.1 × 1.1 ft | 3+ ft fires |
| 30 ft | 55 × 41 ft | 1.7 × 1.7 ft | 5+ ft fires |
| **50 ft** | **91 × 69 ft** | **2.9 × 2.9 ft** | **9+ ft fires** [BEST] |
| 70 ft | 128 × 96 ft | 4.0 × 4.0 ft | 12+ ft fires |
| 100 ft | 183 × 137 ft | 5.7 × 5.7 ft | 17+ ft fires |

**Best altitude for my tests:** 50 feet - good balance between coverage and detection.

### Fire Detection Algorithm
Started with simple temperature threshold (> 50°C). Too many false positives.

**Current approach:**
1. Absolute threshold: > 40°C
2. Relative threshold: > ambient + 15°C
3. Size filter: Must be 3+ pixels
4. Confidence scoring based on temp, size, uniformity

Works pretty well! Still gets confused by really hot car roofs though.

### Battery Life Reality
- **Advertised:** 15-20 minutes
- **Actual (70°F):** 15 minutes
- **Actual (40°F):** 10 minutes
- **With camera/WiFi:** Subtract another minute

Plan missions for 8-10 min max flight time to be safe.

## ML Model Performance

Trained a MobileNetV2-based CNN on Kaggle's fire detection dataset:

| Model | Size | Accuracy | Speed (Pi 4) | Use Case |
|-------|------|----------|--------------|----------|
| fire_detector.keras | 11 MB | 94% | 8 FPS | Training |
| fire_detector.tflite | 9 MB | 93% | 35 FPS | Production |
| fire_detector_quantized.tflite | 4.5 MB | 92% | 115+ FPS | **Raspberry Pi** [BEST] |

Quantized model is fast enough for real-time fire confirmation on the Pi.

## Data Format

All sensor data uses standard CSV/NPY formats compatible with analysis tools:

### GPS Log (CSV)
```csv
timestamp,latitude,longitude,altitude,heading,satellites,fix_type,mode
1703097234.5,33.2365,-96.8265,50.2,90,12,3,AUTO
```

### Thermal Data (NPY + metadata)
- 32×24 numpy arrays saved as `.npy` files
- Metadata in JSON (timestamp, detection results, temperatures)

### Environment Data (CSV)
```csv
timestamp,temperature,humidity,pressure,baro_altitude,baro_temperature,mode,note
1703097234.5,8.5,65,1013.25,0,9.2,AUTO,scouting
```

## Network Configuration

### Primary Network (TP-Link AC600)
- **SSID:** FireDrone-GS
- **IP:** 10.10.8.1/24
- **Range:** 200-300 feet (line of sight)

### Backup Network (Built-in WiFi)
- **SSID:** raspAP
- **IP:** 10.3.141.1/24
- **Range:** 50-100 feet

System automatically fails over to backup if primary drops.

## Future Improvements (If I Had More Time/Money)

1. **Better Thermal Camera:** MLX90641 (192×144) instead of MLX90640 (32×24) - $200 vs $60
2. **Gimbal:** Even a cheap 2-axis gimbal would make footage way clearer
3. **Bigger Battery:** 8000mAh would give 20+ min flight time
4. **Multiple Drones:** Built one due to budget, but swarm is way cooler
5. **LoRa Telemetry:** More reliable than WiFi for long-range
6. **Real Fire Tests:** Need fire department supervision + permit (didn't have time)
7. **Retardant System:** Actually suppress fires, not just detect them

## System Requirements

- Python 3.8+ (3.13 works with my DroneKit patch)
- 2GB RAM minimum (4GB recommended)
- 10GB disk space for data
- Linux (tested on Raspberry Pi OS Bookworm)
- WiFi adapter with AP mode support

## Troubleshooting

### "collections.MutableMapping" Error
```bash
# Fix DroneKit for Python 3.13
python fix_dronekit_py313.py
```

### Thermal Camera Not Detected
```bash
# Enable I2C
sudo raspi-config nonint do_i2c 0
sudo reboot

# Check detection
sudo i2cdetect -y 1
# Should see 0x33
```

### WiFi Access Point Won't Start
```bash
# Check interface state
ip link show wlan1

# Bring up manually
sudo ip link set wlan1 up
sudo systemctl restart hostapd
```

### Low Battery Life
- Keep batteries warm before flight
- Set voltage alarm to 3.8V/cell (not 3.7V)
- Reduce camera streaming resolution