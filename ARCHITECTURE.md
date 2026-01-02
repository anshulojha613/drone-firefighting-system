# System Architecture

## Overview

The Drone Firefighting System (DFS) is a distributed system with three main actors:
- **Ground Station (GS)**: Central command running on Raspberry Pi or server
- **Scouter Drones (SD)**: Fire detection and reconnaissance
- **Firefighter Drones (FD)**: Fire suppression operations

## System Diagram

```
                    GROUND STATION
                    (Raspberry Pi / Server)
                    ┌─────────────────────────────┐
                    │  Mission Control            │
                    │  Database (SQLite)          │
                    │  Dashboard (Flask/Dash)     │
                    │  Network Manager            │
                    │  IP: 10.10.8.1              │
                    └─────────────┬───────────────┘
                                  │
                         WiFi: FireDrone-GS
                                  │
              ┌───────────────────┼───────────────────┐
              │                   │                   │
    ┌─────────▼─────────┐ ┌──────▼──────┐ ┌─────────▼─────────┐
    │   SD DRONE        │ │  SD DRONE   │ │   FD DRONE        │
    │   (Scouter)       │ │  (Scouter)  │ │   (Firefighter)   │
    │   - Thermal Cam   │ │             │ │   - Water Tank    │
    │   - GPS           │ │             │ │   - GPS           │
    │   - Fire ML       │ │             │ │   - Suppression   │
    └───────────────────┘ └─────────────┘ └───────────────────┘
```

## Project Structure

```
drone_firefighting_system/
├── config/
│   └── dfs_config.yaml       # System configuration
├── database/
│   ├── __init__.py
│   └── models.py             # SQLAlchemy ORM models
├── mission_control/
│   ├── __init__.py
│   └── orchestrator.py       # Core mission logic
├── scouter_drone/
│   ├── __init__.py
│   └── executor.py           # SD mission execution
├── firefighter_drone/
│   ├── __init__.py
│   └── executor.py           # FD suppression missions
├── drone_control/
│   ├── __init__.py
│   ├── controller_factory.py # Demo/Hardware abstraction
│   ├── demo_controller.py    # Simulation mode
│   └── pixhawk_controller.py # Hardware mode (DroneKit)
├── modules/
│   ├── camera_module.py      # Still image capture
│   └── fire_detector.py      # ML fire detection
├── ml_training/
│   ├── train_fire_model.py   # CNN model training (MobileNetV2)
│   ├── test_model.py         # Model testing and benchmarking
│   ├── dataset_utils.py      # Dataset preparation utilities
│   └── fire_detector.py      # Thermal fire detection
├── models/
│   ├── fire_detector.keras   # Full Keras model
│   ├── fire_detector.tflite  # TFLite for deployment
│   └── fire_detector_quantized.tflite  # Quantized for Pi
├── network/
│   ├── drone_agent.py        # Flask server on drone
│   ├── ground_station_client.py
│   └── protocol.py           # Message formats
├── dashboard/
│   └── app.py                # Web dashboard (Dash)
├── data/                     # Mission output data
├── logs/                     # System logs
├── main.py                   # Entry point
└── tests.py                  # Consolidated tests
```

## Data Flow

```
User Command → Mission Orchestrator → Database
                      ↓
              Drone Assignment
                      ↓
              SD Drone Execution
                      ↓
    ┌─────────────────┼─────────────────┐
    ↓                 ↓                 ↓
GPS Data      Thermal Scan      Still Images
    ↓                 ↓                 ↓
    └─────────────────┼─────────────────┘
                      ↓
              Fire Detection (ML)
                      ↓
              Hotspot Alert → FD Dispatch
                      ↓
              Suppression Mission
                      ↓
              Mission Complete → Dashboard
```

## Mission Execution Flow

```
1. User starts mission (main.py --demo)
2. Orchestrator creates task in database
3. Available drone assigned (round-robin)
4. Drone executes mission:
   - Generate flight waypoints (lawnmower pattern)
   - Collect GPS telemetry
   - Capture thermal frames
   - Take still images at intervals
   - Run ML fire detection
5. If fire detected:
   - Log hotspot to database
   - Dispatch FD drone automatically
6. FD drone:
   - Capture pre-suppression image
   - Deploy suppressant
   - Capture post-suppression image
   - Verify effectiveness
7. Mission complete, drone returns to IDLE
```

## Database Schema

### Tables
- **drones**: Fleet management (state, battery, position)
- **tasks**: Mission tasks (area, status, results)
- **fire_detections**: Hotspot events (location, temp, confidence)
- **telemetry**: Real-time drone data
- **system_logs**: Events and errors

### Drone States
`idle` → `assigned` → `flying` → `returning` → `idle`

### Task States
`created` → `assigned` → `executing` → `completed`

## Hardware Configuration

### Ground Station
- Raspberry Pi 4/5 or laptop
- WiFi adapter (TP-Link AC600)
- Network: 10.10.8.1 (FireDrone-GS)

### SD Drone
- Raspberry Pi Zero W / Pi 4
- Pixhawk flight controller
- MLX90640 thermal sensor (32x24)
- Arducam IMX708 camera
- GPS module

### FD Drone
- Raspberry Pi 4
- Pixhawk flight controller
- Water/retardant tank
- Release mechanism
- GPS module

## Communication Protocol

### Ground Station → Drone
```json
{
  "type": "mission_assign",
  "task_id": "TASK-20251223-0001",
  "waypoints": [...],
  "area_bounds": {...}
}
```

### Drone → Ground Station
```json
{
  "type": "status_report",
  "drone_id": "SD-001",
  "state": "EXECUTING",
  "battery": 75.5,
  "position": {"lat": 33.226, "lon": -96.826}
}
```

### Fire Alert
```json
{
  "type": "hotspot_alert",
  "drone_id": "SD-001",
  "location": {"lat": 33.2265, "lon": -96.8265},
  "confidence": 0.95,
  "temperature_c": 65.5
}
```

## Network Configuration

### Primary Network
- SSID: FireDrone-GS
- IP: 10.10.8.1
- Subnet: 255.255.255.0

### Backup Network
- SSID: raspAP
- IP: 10.3.141.1
- Auto-failover enabled

## Current Implementation Status

| Component | Status |
|-----------|--------|
| Mission Control | Complete |
| Database | Complete |
| SD Executor | Complete |
| FD Executor | Complete |
| Camera Module | Complete |
| Fire Detection ML | Complete |
| Network Layer | Complete |
| Dashboard | Complete |
| Hardware Mode | Tested |
