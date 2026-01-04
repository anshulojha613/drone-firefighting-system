# Drone Firefighting System - Architecture

## Project Overview

The Drone Firefighting System (DFS) is a distributed autonomous system designed for wildfire detection and suppression using coordinated drone operations. The system consists of three main components:

- **Ground Station (GS)**: Central command and control running on Mac/Linux or Raspberry Pi
- **Scouter Drones (SD)**: Autonomous fire detection and reconnaissance using thermal imaging
- **Firefighter Drones (FD)**: Fire suppression operations with water/retardant delivery

## System Architecture

### High-Level System Diagram

```
                    GROUND STATION
                    (Mac/Linux or Raspberry Pi)
                    ┌─────────────────────────────┐
                    │  Mission Control            │
                    │  Database (SQLite)          │
                    │  Dashboard (Flask/Dash)     │
                    │  Network Manager            │
                    │  IP: 10.10.8.1              │
                    └─────────────┬───────────────┘
                                  │
                         WiFi: FireDrone-GS
                         (10.10.8.x network)
                                  │
              ┌───────────────────┴───────────────────┐
              │                                       │
    ┌─────────▼─────────┐                 ┌─────────▼─────────┐
    │   SD DRONE        │                 │   FD DRONE        │
    │   (Scouter)       │                 │   (Firefighter)   │
    │   - Thermal Cam   │                 │   - Water Tank    │
    │   - GPS           │                 │   - GPS           │
    │   - Fire ML       │                 │   - Suppression   │
    │   - Raspberry Pi  │                 │   - Raspberry Pi  │
    │   - Pixhawk       │                 │   - Pixhawk       │
    └───────────────────┘                 └───────────────────┘
```

### Network Architecture

```
Ground Station (Mac)          WiFi Network          Drone (Raspberry Pi)
┌─────────────────┐          ┌──────────┐          ┌──────────────────┐
│   main.py       │          │          │          │  drone_agent.py  │
│  (orchestrator) │ ─────────┤ 10.10.8.x├─────────>│  (Flask server)  │
│                 │   HTTP   │          │          │                  │
│ GroundStation   │          └──────────┘          │ PixhawkController│
│    Client       │                                 │                  │
└─────────────────┘                                 └────────┬─────────┘
                                                             │
                                                             │ Serial
                                                             ▼
                                                      ┌──────────────┐
                                                      │   Pixhawk    │
                                                      │ /dev/ttyAMA0 │
                                                      └──────────────┘
```

## Project Structure

```
drone_firefighting_system/
├── config/
│   ├── dfs_config.yaml              # System configuration
│   ├── mission_areas.yaml           # Mission area definitions
│   ├── batch_mission_areas_sequential.yaml
│   └── batch_mission_areas_parallel.yaml
├── database/
│   ├── __init__.py                  # Database manager
│   └── models.py                    # SQLAlchemy ORM models
├── mission_control/
│   ├── __init__.py
│   └── orchestrator.py              # Core mission orchestration
├── scouter_drone/
│   ├── __init__.py
│   ├── simulator.py                 # SD mission execution
│   └── executor.py                  # SD mission executor
├── firefighter_drone/
│   ├── __init__.py
│   └── executor.py                  # FD suppression missions
├── drone_control/
│   ├── __init__.py
│   ├── controller_factory.py        # Demo/Hardware abstraction
│   ├── demo_controller.py           # Simulation mode
│   └── pixhawk_controller.py        # Hardware mode (DroneKit)
├── modules/
│   ├── camera_module.py             # Still image capture (rpicam-still)
│   └── fire_detector.py             # ML fire detection
├── hardware_sensors/
│   ├── thermal_sensor.py            # MLX90640 thermal camera
│   └── environment_sensor.py        # DHT22 environment sensor
├── ml_training/
│   ├── train_fire_model.py          # CNN model training (MobileNetV2)
│   ├── test_model.py                # Model testing and benchmarking
│   ├── dataset_utils.py             # Dataset preparation utilities
│   └── fire_detector.py             # Thermal fire detection
├── models/
│   ├── fire_detector.keras          # Full Keras model
│   ├── fire_detector.tflite         # TFLite for deployment
│   └── fire_detector_quantized.tflite  # Quantized for Pi
├── network/
│   ├── drone_agent.py               # Flask server on drone
│   ├── ground_station_client.py     # Ground station network client
│   ├── communication.py             # Network communication layer
│   └── protocol.py                  # Message formats
├── dashboard/
│   └── app.py                       # Web dashboard (Dash/Plotly)
├── requirements/
│   ├── ground_station.txt           # Ground station dependencies
│   ├── sd_drone.txt                 # Scouter drone dependencies
│   ├── fire_drone.txt               # Firefighter drone dependencies
│   └── README.md                    # Requirements documentation
├── data/                            # Mission output data
├── logs/                            # System logs
├── main.py                          # Entry point
├── batch_mission.py                 # Batch mission execution
├── tests.py                         # Consolidated tests
├── emergency_control.py             # Emergency control script
├── deploy_to_pi.sh                  # Deployment script
└── fix_dronekit_py313.py           # DroneKit Python 3.13 fix
```

## Key Features and Capabilities

### Mission Control Features

| Feature | Description | Status |
|---------|-------------|--------|
| Mission Orchestration | Task creation, drone assignment, execution monitoring | Complete |
| Database Management | SQLite ORM for missions, detections, telemetry | Complete |
| Batch Missions | Sequential and parallel mission execution | Complete |
| Network Communication | WiFi-based ground station to drone communication | Complete |
| Real-time Dashboard | Web-based monitoring with Plotly/Dash | Complete |
| Emergency Control | Abort, RTL, land, kill switch commands | Complete |

### Scouter Drone Capabilities

| Capability | Technology | Status |
|------------|-----------|--------|
| Thermal Imaging | MLX90640 (32x24, 110° FOV) | Complete |
| Fire Detection | CNN (MobileNetV2) + thermal thresholding | Complete |
| Still Image Capture | rpicam-still CLI tool | Complete |
| GPS Navigation | Pixhawk GPS module | Complete |
| Autonomous Flight | Lawnmower pattern waypoint generation | Complete |
| Environment Sensing | DHT22 (temperature, humidity) | Complete |

### Firefighter Drone Capabilities

| Capability | Technology | Status |
|------------|-----------|--------|
| Targeted Suppression | GPS-guided water/retardant delivery | Complete |
| Pre/Post Imaging | Before and after suppression photos | Complete |
| Effectiveness Verification | Temperature comparison analysis | Complete |
| Autonomous Navigation | GPS waypoint following | Complete |

### Hardware Modes

| Mode | Description | Use Case |
|------|-------------|----------|
| Demo | Simulated flight on any machine | Development, testing |
| Hardware | Real Pixhawk control via DroneKit | Bench testing, production |
| Network | Ground station controls remote drone | Production operations |

## Process Flow

### Mission Execution Flow

```
1. User starts mission (main.py --demo)
   ↓
2. Orchestrator creates task in database
   ↓
3. Available drone assigned (round-robin)
   ↓
4. Drone executes mission:
   - Generate flight waypoints (lawnmower pattern)
   - Collect GPS telemetry
   - Capture thermal frames
   - Take still images at intervals
   - Run ML fire detection
   ↓
5. If fire detected:
   - Log hotspot to database
   - Dispatch FD drone automatically
   ↓
6. FD drone:
   - Navigate to hotspot location
   - Capture pre-suppression image
   - Deploy suppressant
   - Capture post-suppression image
   - Verify effectiveness
   ↓
7. Mission complete, drone returns to IDLE
```

### Batch Mission Flow

```
Sequential Mode:
Task 1 → Complete → Task 2 → Complete → Task 3 → Complete

Parallel Mode:
Task 1 ─┐
Task 2 ─┼─→ Execute concurrently
Task 3 ─┘
```

## Data Flow

### Mission Data Flow

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

### Network Communication Flow

```
Ground Station                    Drone Agent
     │                                 │
     ├── Mission Assign ──────────────>│
     │   POST /api/mission/assign      │
     │                                 │
     │<── Acknowledgment ───────────────┤
     │   200 OK                        │
     │                                 │
     ├── Mission Start ───────────────>│
     │   POST /api/mission/start       │
     │                                 │
     │<── Status Updates ───────────────┤
     │   (every 2 sec)                 │
     │                                 │
     │<── Hotspot Alert ────────────────┤
     │   (on fire detection)           │
     │                                 │
     ├── Emergency Command ────────────>│
     │   POST /api/mission/abort       │
     │                                 │
     │<── Acknowledgment ───────────────┤
```

**Communication Protocol:**
- **Transport:** HTTP/REST over WiFi (10.10.8.x network)
- **Port:** 5001 (configurable)
- **Data Format:** JSON
- **Timeout:** 30 sec (mission commands), 5 sec (status checks)

**API Endpoints:**

| Direction | Endpoint | Method | Purpose | Frequency |
|-----------|----------|--------|---------|-----------|
| GS → Drone | `/api/mission/assign` | POST | Assign mission with waypoints | On mission start |
| GS → Drone | `/api/mission/start` | POST | Start mission execution | After assignment |
| GS → Drone | `/api/mission/abort` | POST | Abort mission and RTL | Emergency |
| GS → Drone | `/api/rtl` | POST | Return to launch | Emergency |
| GS → Drone | `/api/land` | POST | Emergency land | Emergency |
| GS → Drone | `/api/kill` | POST | Kill motors (DANGEROUS) | Emergency |
| GS → Drone | `/api/status` | GET | Get drone status | On-demand |
| Drone → GS | Status callback | POST | Telemetry updates | Every 2 seconds |
| Drone → GS | Hotspot callback | POST | Fire detection alert | Event-driven |

**JSON Payload Examples:**

Mission Assignment:
```json
{
  "task_id": "TASK-20251223-0001",
  "waypoints": [{"lat": 33.236, "lon": -96.826, "alt": 50}],
  "area_bounds": {"north": 33.237, "south": 33.235, "east": -96.825, "west": -96.827}
}
```

Status Update:
```json
{
  "drone_id": "SD-001",
  "state": "EXECUTING",
  "battery": 75.5,
  "position": {"lat": 33.236, "lon": -96.826, "alt": 50.2}
}
```

Hotspot Alert:
```json
{
  "drone_id": "SD-001",
  "location": {"lat": 33.2265, "lon": -96.8265},
  "temperature_c": 65.5,
  "confidence": 0.95
}
```

## State Management

### Drone States

```
IDLE → ASSIGNED → FLYING → RETURNING → IDLE
  ↑                                      │
  └──────────────────────────────────────┘
```

| State | Description | Transitions |
|-------|-------------|-------------|
| IDLE | Drone available for assignment | → ASSIGNED |
| ASSIGNED | Task assigned, preparing for flight | → FLYING |
| FLYING | Mission execution in progress | → RETURNING |
| RETURNING | Returning to launch position | → IDLE |

### Task States

```
CREATED → ASSIGNED → EXECUTING → COMPLETED
   │                                  ↑
   └──────────── FAILED ──────────────┘
```

| State | Description | Transitions |
|-------|-------------|-------------|
| CREATED | Task created, awaiting assignment | → ASSIGNED |
| ASSIGNED | Assigned to drone, not started | → EXECUTING |
| EXECUTING | Mission in progress | → COMPLETED, FAILED |
| COMPLETED | Mission successfully completed | Terminal state |
| FAILED | Mission failed or aborted | Terminal state |

## Database Schema

### Tables Overview

| Table | Purpose | Key Fields |
|-------|---------|-----------|
| drones | Fleet management | id, state, battery, position, last_seen |
| tasks | Mission tasks | id, area_id, status, drone_id, results |
| fire_detections | Hotspot events | id, task_id, location, temperature, confidence |
| telemetry | Real-time drone data | id, drone_id, timestamp, position, altitude |
| system_logs | Events and errors | id, timestamp, level, message, component |

### Drone Table Schema

```sql
CREATE TABLE drones (
    id VARCHAR PRIMARY KEY,
    state VARCHAR,
    battery_percent FLOAT,
    latitude FLOAT,
    longitude FLOAT,
    altitude FLOAT,
    last_seen DATETIME
);
```

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| id | VARCHAR | Unique drone identifier | SD-001, FD-001 |
| state | VARCHAR | Current drone state | IDLE, ASSIGNED, FLYING, RETURNING |
| battery_percent | FLOAT | Battery level (0-100) | 75.5 |
| latitude | FLOAT | Current GPS latitude | 33.2365 |
| longitude | FLOAT | Current GPS longitude | -96.8265 |
| altitude | FLOAT | Current altitude in feet | 50.2 |
| last_seen | DATETIME | Last telemetry update | 2025-12-23 14:30:45 |

### Task Table Schema

```sql
CREATE TABLE tasks (
    id VARCHAR PRIMARY KEY,
    area_id VARCHAR,
    status VARCHAR,
    drone_id VARCHAR,
    created_at DATETIME,
    started_at DATETIME,
    completed_at DATETIME,
    results JSON
);
```

| Column | Type | Description | Example |
|--------|------|-------------|------|
| id | VARCHAR | Unique task identifier | TASK-20251223-0001 |
| area_id | VARCHAR | Mission area identifier | area_1, north_field |
| status | VARCHAR | Task status | CREATED, ASSIGNED, EXECUTING, COMPLETED, FAILED |
| drone_id | VARCHAR | Assigned drone ID | SD-001, FD-001 |
| created_at | DATETIME | Task creation timestamp | 2025-12-23 14:00:00 |
| started_at | DATETIME | Mission start timestamp | 2025-12-23 14:05:30 |
| completed_at | DATETIME | Mission completion timestamp | 2025-12-23 14:15:45 |
| results | JSON | Mission results and metadata | {"hotspots": 2, "images": 15} |

### Fire Detection Table Schema

```sql
CREATE TABLE fire_detections (
    id INTEGER PRIMARY KEY,
    task_id VARCHAR,
    latitude FLOAT,
    longitude FLOAT,
    temperature_c FLOAT,
    confidence FLOAT,
    detected_at DATETIME
);
```

| Column | Type | Description | Example |
|--------|------|-------------|------|
| id | INTEGER | Auto-increment primary key | 1, 2, 3 |
| task_id | VARCHAR | Associated task ID | TASK-20251223-0001 |
| latitude | FLOAT | Hotspot GPS latitude | 33.2265 |
| longitude | FLOAT | Hotspot GPS longitude | -96.8265 |
| temperature_c | FLOAT | Detected temperature in Celsius | 65.5 |
| confidence | FLOAT | Detection confidence (0-1) | 0.95 |
| detected_at | DATETIME | Detection timestamp | 2025-12-23 14:10:22 |

## Hardware Configuration

### Ground Station Specifications

| Component | Specification |
|-----------|--------------|
| Platform | Mac/Linux or Raspberry Pi 4/5 |
| Network | WiFi adapter (TP-Link AC600) |
| IP Address | 10.10.8.1 (FireDrone-GS network) |
| Software | Python 3.11+, Flask, Dash, SQLAlchemy |
| Storage | 10GB minimum for data and logs |

### Scouter Drone Specifications

| Component | Specification |
|-----------|--------------|
| Computer | Raspberry Pi Zero W / Pi 4 |
| Flight Controller | Pixhawk (APM/PX4 firmware) |
| Thermal Camera | MLX90640 (32x24, 110° FOV, I2C) |
| RGB Camera | Arducam IMX708 (rpicam-still) |
| Environment Sensor | DHT22 (temperature, humidity) |
| GPS | Pixhawk integrated GPS module |
| Connection | /dev/ttyAMA0 (UART) or /dev/ttyACM0 (USB) |

### Firefighter Drone Specifications

| Component | Specification |
|-----------|--------------|
| Computer | Raspberry Pi 4 |
| Flight Controller | Pixhawk (APM/PX4 firmware) |
| Payload | Water/retardant tank with release mechanism |
| GPS | Pixhawk integrated GPS module |
| Connection | /dev/ttyAMA0 (UART) or /dev/ttyACM0 (USB) |

### Thermal Camera Coverage

Using MLX90640 (110° FOV), ground coverage at different altitudes:

| Altitude | Coverage Area | Pixel Size | Can Detect |
|----------|---------------|------------|------------|
| 20 ft | 36 × 27 ft | 1.1 × 1.1 ft | 3+ ft fires |
| 30 ft | 55 × 41 ft | 1.7 × 1.7 ft | 5+ ft fires |
| 50 ft | 91 × 69 ft | 2.9 × 2.9 ft | 9+ ft fires (OPTIMAL) |
| 70 ft | 128 × 96 ft | 4.0 × 4.0 ft | 12+ ft fires |
| 100 ft | 183 × 137 ft | 5.7 × 5.7 ft | 17+ ft fires |

**Recommended altitude:** 50 feet - optimal balance between coverage and detection accuracy.

## Communication Protocol

### Message Formats

#### Ground Station to Drone - Mission Assignment

```json
{
  "type": "mission_assign",
  "task_id": "TASK-20251223-0001",
  "mission_type": "scout",
  "area_bounds": {
    "north": 33.2365,
    "south": 33.2355,
    "east": -96.8255,
    "west": -96.8275
  },
  "waypoints": [
    {"lat": 33.236, "lon": -96.826, "alt": 50},
    {"lat": 33.236, "lon": -96.827, "alt": 50}
  ],
  "parameters": {
    "altitude": 50,
    "speed": 5,
    "thermal_interval": 2
  }
}
```

#### Drone to Ground Station - Status Report

```json
{
  "type": "status_report",
  "drone_id": "SD-001",
  "state": "EXECUTING",
  "battery": 75.5,
  "position": {
    "lat": 33.226,
    "lon": -96.826,
    "alt": 50.2
  },
  "task_id": "TASK-20251223-0001",
  "timestamp": 1703097234.5
}
```

#### Drone to Ground Station - Fire Alert

```json
{
  "type": "hotspot_alert",
  "drone_id": "SD-001",
  "task_id": "TASK-20251223-0001",
  "location": {
    "lat": 33.2265,
    "lon": -96.8265,
    "alt": 50.0
  },
  "confidence": 0.95,
  "temperature_c": 65.5,
  "timestamp": 1703097234.5
}
```

### API Endpoints

#### Drone Agent Endpoints

| Endpoint | Method | Description | Parameters |
|----------|--------|-------------|------------|
| `/api/status` | GET | Get drone status | None |
| `/api/mission/assign` | POST | Assign mission to drone | mission_config (JSON) |
| `/api/mission/start` | POST | Start mission execution | None |
| `/api/mission/abort` | POST | Abort current mission | None |
| `/api/rtl` | POST | Return to launch | None |
| `/api/land` | POST | Emergency land | None |
| `/api/kill` | POST | Kill motors (DANGEROUS) | None |
| `/api/heartbeat` | POST | Heartbeat check | None |

## Network Configuration

### Primary Network

| Parameter | Value |
|-----------|-------|
| SSID | FireDrone-GS |
| IP Range | 10.10.8.0/24 |
| Ground Station | 10.10.8.1 |
| Drones | 10.10.8.101, 10.10.8.102, etc. |
| Range | 200-300 feet (line of sight) |

### Backup Network

| Parameter | Value |
|-----------|-------|
| SSID | raspAP |
| IP Range | 10.3.141.0/24 |
| Ground Station | 10.3.141.1 |
| Range | 50-100 feet |
| Failover | Automatic |

## Machine Learning Model Performance

### Fire Detection Models

| Model | Size | Accuracy | Speed (Pi 4) | Use Case |
|-------|------|----------|--------------|----------|
| fire_detector.keras | 11 MB | 94% | 8 FPS | Training |
| fire_detector.tflite | 9 MB | 93% | 35 FPS | Production |
| fire_detector_quantized.tflite | 4.5 MB | 92% | 115+ FPS | Raspberry Pi (OPTIMAL) |

### Fire Detection Algorithm

**Multi-stage approach:**

1. **Absolute threshold:** Temperature > 40°C
2. **Relative threshold:** Temperature > ambient + 15°C
3. **Size filter:** Hotspot must be 3+ pixels
4. **Confidence scoring:** Based on temperature, size, and uniformity

## Data Formats

### GPS Log (CSV)

```csv
timestamp,latitude,longitude,altitude,heading,satellites,fix_type,mode
1703097234.5,33.2365,-96.8265,50.2,90,12,3,AUTO
```

### Thermal Data (NPY + JSON)

- **Format:** 32×24 numpy arrays saved as `.npy` files
- **Metadata:** JSON file with timestamp, detection results, temperatures

### Environment Data (CSV)

```csv
timestamp,temperature,humidity,pressure,baro_altitude,baro_temperature,mode,note
1703097234.5,8.5,65,1013.25,0,9.2,AUTO,scouting
```

## System Requirements

### Software Requirements

| Component | Version | Purpose |
|-----------|---------|---------|
| Python | 3.11+ (tested on 3.13) | Core runtime |
| SQLAlchemy | 2.0.35+ | Database ORM |
| Flask | 3.0.0 | Web framework |
| Dash | 2.14.2 | Dashboard |
| DroneKit | 2.9.2+ | Pixhawk communication |
| OpenCV | 4.8.0+ | Image processing |
| NumPy | 1.26.0+ | Data processing |

### Hardware Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| RAM | 2GB | 4GB |
| Storage | 10GB | 20GB |
| WiFi | 802.11n | 802.11ac |
| OS | Linux (Raspberry Pi OS) | Raspberry Pi OS Bookworm |

## Component Implementation Status

| Component | Status | Notes |
|-----------|--------|-------|
| Mission Control | Complete | Full orchestration and task management |
| Database | Complete | SQLAlchemy ORM with all tables |
| SD Executor | Complete | Thermal scanning and fire detection |
| FD Executor | Complete | Suppression mission execution |
| Camera Module | Complete | rpicam-still CLI integration |
| Fire Detection ML | Complete | MobileNetV2 CNN with quantization |
| Network Layer | Complete | Ground station and drone agent |
| Dashboard | Complete | Real-time monitoring with Plotly |
| Hardware Mode | Tested | DroneKit integration with Pixhawk |
| Emergency Control | Complete | Abort, RTL, land, kill commands |
| Batch Missions | Complete | Sequential and parallel execution |
| Deployment Script | Complete | Automated Pi deployment |

## Future Enhancements

### Potential Improvements

| Enhancement | Description | Priority |
|-------------|-------------|----------|
| Higher Resolution Thermal | MLX90641 (192×144) instead of MLX90640 (32×24) | High |
| Gimbal Integration | 2-axis gimbal for stabilized footage | Medium |
| Extended Battery | 8000mAh for 20+ min flight time | High |
| Multi-Drone Swarm | Coordinated swarm operations | Medium |
| LoRa Telemetry | Long-range communication backup | Low |
| Real Fire Testing | Field tests with fire department supervision | High |
| Advanced Suppression | Precision retardant delivery system | Medium |
