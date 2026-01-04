# Drone Firefighting System - Operations Guide

## Choose Your Path

| I want to... | Script | Command | Mode |
|--------------|--------|---------|------|
| Run a quick demo | `main.py` | `python main.py --demo` | A |
| Monitor system visually | `main.py` | `python main.py --dashboard` | A, B, C |
| Run multiple missions | `batch_mission.py` | `python batch_mission.py` | A, C |
| Verify system works | `tests.py` | `python tests.py` | A, B |
| Test with simulation | `tests.py` | `python tests.py --simulation` | A |
| Test hardware connection | `tests.py` | `python tests.py --hardware` | B |
| Reset stuck drones | `tests.py` | `python tests.py --reset` | A, B, C |
| Clean all records | `tests.py` | `python tests.py --clean` | A, B, C |
| Run baseline tests | `run_baseline_tests.sh` | `./run_baseline_tests.sh` | A |
| Fix DroneKit for Python 3.13 | `fix_dronekit_py313.py` | `python fix_dronekit_py313.py` | B, C |
| Deploy to Raspberry Pi | `deploy_to_pi.sh` | `./deploy_to_pi.sh --drone-type sd` | B, C |
| Start drone agent | `network/drone_agent.py` | `python network/drone_agent.py --drone-id SD-001` | C |
| Emergency abort mission | `emergency_control.py` | `python emergency_control.py --ip 10.10.8.1 --abort` | C |

**Modes:** A = Simulation, B = Hardware Testing (no flight), C = Production (actual flight)

---

## Quick Start

### Installation

#### Option 1: Ground Station (Mac/Linux)
```bash
cd drone_firefighting_system
python3 -m venv venv
source venv/bin/activate
pip install -r requirements/ground_station.txt

# If you hit DroneKit issues on Python 3.13:
python fix_dronekit_py313.py
```

#### Option 2: Scouter Drone (Raspberry Pi)
```bash
cd drone_firefighting_system
python3 -m venv venv
source venv/bin/activate
pip install -r requirements/sd_drone.txt
```

#### Option 3: Firefighter Drone (Raspberry Pi)
```bash
cd drone_firefighting_system
python3 -m venv venv
source venv/bin/activate
pip install -r requirements/fire_drone.txt
```

#### Option 4: Automated Deployment to Raspberry Pi
```bash
# Deploy Scouter Drone
./deploy_to_pi.sh --drone-type sd

# Deploy Firefighter Drone
./deploy_to_pi.sh --drone-type fd

# Deploy Ground Station
./deploy_to_pi.sh --drone-type gs

# Deploy with custom settings
./deploy_to_pi.sh --drone-type sd --pi-host 10.10.8.2 --drone-id SD-002 --pi-user myuser

# Show help
./deploy_to_pi.sh --help
```

### Run Demo Mission (No Hardware Needed)
```bash
# Simulate a scouting mission
python main.py --demo

# Launch dashboard
python main.py --dashboard
# Open: http://localhost:8050
```

---

## Component-Specific Requirements

The system uses modular requirements files to minimize installation size and optimize performance for different components.

### Requirements Files Overview

| File | Platform | Size | Purpose |
|------|----------|------|---------|
| `requirements/ground_station.txt` | Mac/Linux | ~200MB | Dashboard, network client, visualization |
| `requirements/sd_drone.txt` | Raspberry Pi | ~150MB | Thermal camera, fire detection, drone agent |
| `requirements/fire_drone.txt` | Raspberry Pi | ~100MB | Flight control, water pump, drone agent |

### Component Breakdown

#### Ground Station
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

#### Scouter Drone
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

#### Firefighter Drone
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

### Migration from Single requirements.txt

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

---

## Simulation vs Hardware vs Production

### Option A: Simulation Mode (Development/Testing)
Use this on your laptop or any machine without drone hardware.

```bash
# 1. Ensure demo mode in config
# config/dfs_config.yaml: drone_control.mode: 'demo'

# 2. Run demo mission
python main.py --demo

# 3. Or run batch missions
python batch_mission.py --config config/mission_areas.yaml

# Validate config only
python batch_mission.py --validate-only

# Sequential execution (default)
python batch_mission.py --mode sequential --mission-delay 2

# Parallel execution (multiple drones simultaneously)
python batch_mission.py --mode parallel --workers 3 --dispatch-delay 0.5

# Use custom config file
python batch_mission.py --config my_areas.yaml
```

### Option B: Hardware Testing (Bench Test - No Flight)
Use this on Raspberry Pi with Pixhawk connected but NOT flying.

```bash
# 1. Install DroneKit
pip install dronekit pymavlink
python fix_dronekit_py313.py

# 2. Set hardware mode in config
# config/dfs_config.yaml: drone_control.mode: 'hardware'

# 3. Test Pixhawk connection (no flight)
python tests.py --hardware

# 4. Verify battery, GPS, telemetry
python -c "
from drone_control import ControllerFactory
ctrl = ControllerFactory.create_controller('SD-001')
ctrl.connect()
print(f'Battery: {ctrl.get_battery()}%')
print(f'GPS: {ctrl.get_position()}')
ctrl.disconnect()
"
```

### Option C: Production Execution (Actual Flight)
Use this for real drone operations. **Requires proper safety setup.**

```bash
# ON GROUND STATION (Mac/Linux):
# 1. Start dashboard for monitoring
python main.py --dashboard

# ON DRONE (Raspberry Pi):
# 2. Ensure hardware mode
# config/dfs_config.yaml: drone_control.mode: 'hardware'

# 3. Start drone agent
python network/drone_agent.py --drone-id SD-001 --port 5001

# ON GROUND STATION:
# 4. Execute mission (will communicate with drone over WiFi)
python main.py --demo --network --drone-id SD-001

# Or for multiple areas:
python batch_mission.py
```

**Production Checklist:**
- [ ] Pixhawk connected and calibrated
- [ ] GPS lock acquired
- [ ] Battery > 80%
- [ ] WiFi network (FireDrone-GS) operational
- [ ] RC transmitter ready for manual override
- [ ] Clear flight area
- [ ] Observer present

---

## Deployment to Raspberry Pi

### Deployment Script Usage

The `deploy_to_pi.sh` script automatically deploys the system to Raspberry Pi with component-specific requirements.

#### Command-Line Options

| Option | Description | Example |
|--------|-------------|---------|
| `--drone-type TYPE` | Drone type: sd, fd, gs | `--drone-type sd` |
| `--pi-user USER` | Raspberry Pi username | `--pi-user anshul` |
| `--pi-host HOST` | Raspberry Pi IP address | `--pi-host 10.10.8.1` |
| `--drone-id ID` | Drone ID | `--drone-id SD-001` |
| `--help` | Show help message | `--help` |

#### Deployment Examples

```bash
# Deploy Scouter Drone (default settings)
./deploy_to_pi.sh --drone-type sd

# Deploy Firefighter Drone to different Pi
./deploy_to_pi.sh --drone-type fd --pi-host 10.10.8.2

# Deploy Ground Station
./deploy_to_pi.sh --drone-type gs

# Deploy with all custom settings
./deploy_to_pi.sh \
  --drone-type sd \
  --pi-host 10.10.8.101 \
  --pi-user myuser \
  --drone-id SD-002
```

#### What the Deployment Script Does

1. Tests connection to Raspberry Pi
2. Creates project directory on Pi
3. Syncs files (incremental, only changed files)
4. Sets up Python virtual environment
5. Installs component-specific requirements
6. Provides systemd service setup instructions

---

## Network Mode Setup

### Architecture Overview

Network mode allows your ground station (Mac/Linux) to send missions over WiFi to the Raspberry Pi on the drone, which then controls the Pixhawk hardware.

```
Ground Station (Mac)  →  WiFi  →  Drone (Pi)  →  Serial  →  Pixhawk
```

### Step 1: Configure Drone IP Addresses

Edit `config/dfs_config.yaml` and set the IP addresses for your drones:

```yaml
drone_pool:
  drone_registry:
    SD-001:
      ip: 10.10.8.101  # Change to your drone's actual IP
      port: 5001
    SD-002:
      ip: 10.10.8.102
      port: 5001
    FD-001:
      ip: 10.10.8.103
      port: 5001
```

### Step 2: Network Configuration

Ensure both your ground station and Raspberry Pi are on the same WiFi network:

| Parameter | Value |
|-----------|-------|
| Network SSID | FireDrone-GS |
| Subnet | 10.10.8.0/24 |
| Ground Station | 10.10.8.1 |
| Drones | 10.10.8.101, 10.10.8.102, etc. |

### Step 3: Start Drone Agent on Raspberry Pi

```bash
# SSH to Raspberry Pi
ssh anshul@10.10.8.101

# Navigate to project directory
cd ~/drone-firefighting-system

# Activate virtual environment
source venv/bin/activate

# Ensure config has hardware mode enabled
# Edit config/dfs_config.yaml:
#   drone_control.mode: hardware
#   drone_control.hardware.connection_string: /dev/ttyAMA0

# Start the drone agent
python -m network.drone_agent --drone-id SD-001 --port 5001
```

**What the drone agent does:**
- Starts a Flask server on port 5001
- Listens for mission commands from ground station
- Controls the Pixhawk via `/dev/ttyAMA0`
- Sends telemetry back to ground station

### Step 4: Run Mission from Ground Station

```bash
# On your Mac/Linux ground station
cd ~/Documents/coding/drone_firefighting_system
source venv/bin/activate

# Run in network mode
python main.py --demo --network --drone-id SD-001
```

### Network Mode Comparison

| Mode | Command | Description |
|------|---------|-------------|
| Local Demo | `python main.py --demo` | Simulated flight on Mac (no hardware) |
| Network Mode | `python main.py --demo --network` | Ground station → WiFi → Pi → Pixhawk |

---

## Running Missions

### Single Demo Mission

```bash
# Simulation mode (no hardware)
python main.py --demo

# With dashboard monitoring
python main.py --dashboard &
python main.py --demo
```

### Batch Missions

The system supports two execution modes for batch missions:

#### Sequential Mode (Default)
Tasks are executed one after another with configurable delays between missions.

```bash
# Run with default settings (sequential)
python batch_mission.py

# Customize delay between missions
python batch_mission.py --mode sequential --mission-delay 3

# Use custom config file
python batch_mission.py --config config/batch_mission_areas_sequential.yaml
```

**Configuration:**
```yaml
# config/batch_mission_areas_sequential.yaml
execution:
  mode: sequential
  delay_between_missions_sec: 2
```

**Use when:**
- Testing with limited drones
- Need predictable execution order
- Debugging mission flow

#### Parallel Mode
Multiple tasks are dispatched simultaneously with staggered delays, allowing multiple drones to work concurrently.

```bash
# Run in parallel mode
python batch_mission.py --mode parallel

# Customize workers and dispatch delay
python batch_mission.py --mode parallel --workers 3 --dispatch-delay 0.5

# Use custom config file
python batch_mission.py --config config/batch_mission_areas_parallel.yaml
```

**Configuration:**
```yaml
# config/batch_mission_areas_parallel.yaml
execution:
  mode: parallel
  max_workers: 3
  dispatch_delay_sec: 0.5
```

**Use when:**
- Multiple drones available
- Need faster area coverage
- Production operations

---

## Dashboard Monitoring

### Starting the Dashboard

```bash
# Start dashboard server
python main.py --dashboard

# Open in browser
# http://localhost:8050
```

### Dashboard Features

| Feature | Description |
|---------|-------------|
| Real-time Map | Live drone positions and mission areas |
| Drone Status | Battery, state, current task |
| Fire Detections | Hotspot locations and confidence |
| Telemetry | Altitude, speed, GPS data |
| Mission History | Completed tasks and results |

---

## Emergency Control

During mission execution, you have multiple ways to send emergency commands to your drone.

### Safety Levels

| Command | Safety Level | Description |
|---------|--------------|-------------|
| ABORT | Safest | Stops mission, returns to launch |
| RTL | Safe | Returns to home position |
| LAND | Caution | Lands at current position |
| KILL | DANGEROUS | Immediate motor stop (drone will fall) |

### Method 1: Same Terminal (Ctrl+C)

While mission is running, press **Ctrl+C** to abort:

```bash
python main.py --demo --network --drone-id SD-001

# Press Ctrl+C during execution
^C
[WARN] Mission abort requested by user
[ABORT] Sending abort command to drone...
[OK] Abort command sent - drone returning to launch
```

### Method 2: Separate Terminal (Full Control)

#### Interactive Mode (Recommended)

Open a **new terminal** while mission is running:

```bash
python emergency_control.py --ip 10.10.8.1
```

You'll see an interactive menu:

```
======================================================================
  EMERGENCY CONTROL - DRONE OPERATIONS
======================================================================
  Drone: 10.10.8.1:5001
======================================================================

[OK] Connected to drone
   State: EXECUTING
   Mode: hardware
   Task: TASK-20251226-0003

----------------------------------------------------------------------
Emergency Commands:
  1. ABORT    - Abort mission and return to launch
  2. RTL      - Return to launch (safe return home)
  3. LAND     - Emergency land at current position
  4. KILL     - Kill switch (immediate motor stop - DANGEROUS!)
  5. STATUS   - Check drone status
  6. EXIT     - Exit emergency control
----------------------------------------------------------------------

Enter command (1-6):
```

#### Quick Commands

For immediate action without menu:

```bash
# Abort mission
python emergency_control.py --ip 10.10.8.1 --abort

# Return to launch
python emergency_control.py --ip 10.10.8.1 --rtl

# Emergency land
python emergency_control.py --ip 10.10.8.1 --land

# Check status
python emergency_control.py --ip 10.10.8.1 --status

# Kill switch (requires confirmation)
python emergency_control.py --ip 10.10.8.1 --kill
```

### Complete Workflow Example

#### Terminal 1: Start Mission
```bash
# On Mac (Ground Station)
python main.py --demo --network --drone-id SD-001

[COMM] Running in NETWORK mode (Ground Station -> WiFi -> Drone)
[TARGET] Target drone: SD-001
...
[WAIT] Waiting for mission completion...
[TIP] Press Ctrl+C to abort mission and RTL
   Status: EXECUTING
```

#### Terminal 2: Emergency Control (if needed)
```bash
# Open new terminal on Mac
python emergency_control.py --ip 10.10.8.1

# Select option:
# 1 - ABORT (safest)
# 2 - RTL
# 3 - LAND
# 4 - KILL (dangerous!)
```

### API Endpoints for Emergency Control

| Endpoint | Method | Action | Safety |
|----------|--------|--------|--------|
| `/api/mission/abort` | POST | Abort mission + RTL | Safe |
| `/api/rtl` | POST | Return to launch | Safe |
| `/api/land` | POST | Emergency land | Caution |
| `/api/kill` | POST | Kill motors | Dangerous |
| `/api/status` | GET | Get drone status | Info |

### Manual API Calls with curl

```bash
# Abort mission
curl -X POST http://10.10.8.1:5001/api/mission/abort

# Return to launch
curl -X POST http://10.10.8.1:5001/api/rtl

# Emergency land
curl -X POST http://10.10.8.1:5001/api/land

# Check status
curl http://10.10.8.1:5001/api/status

# Kill switch
curl -X POST http://10.10.8.1:5001/api/kill
```

---

## Testing and Validation

### System Tests

```bash
# Run all tests
python tests.py

# Run simulation tests only
python tests.py --simulation

# Test hardware connection (no flight)
python tests.py --hardware

# Reset stuck drones
python tests.py --reset

# Clean all database records
python tests.py --clean
```

### Baseline Tests

```bash
# Run comprehensive baseline tests
./run_baseline_tests.sh
```

### Testing Without Propellers

For safe bench testing:

1. **Start mission normally:**
   ```bash
   python main.py --demo --network --drone-id SD-001
   ```

2. **In separate terminal, test emergency commands:**
   ```bash
   # Test abort
   python emergency_control.py --ip 10.10.8.1 --abort
   
   # Check if it worked
   python emergency_control.py --ip 10.10.8.1 --status
   ```

3. **Watch drone agent logs on Pi** to see commands received

---

## Troubleshooting

### Connection Issues

#### "Cannot connect to SD-001 at 10.10.8.101:5001"

**Cause:** Drone agent not running or network issue

**Solutions:**
1. Check drone agent is running on Pi:
   ```bash
   ssh anshul@10.10.8.101
   ps aux | grep drone_agent
   ```

2. Test network connectivity:
   ```bash
   ping 10.10.8.101
   curl http://10.10.8.101:5001/api/status
   ```

3. Check firewall on Pi:
   ```bash
   sudo ufw status
   sudo ufw allow 5001/tcp
   ```

#### "Drone SD-001 not found in drone_registry config"

**Cause:** Drone not registered in config file

**Solution:** Add drone to `config/dfs_config.yaml`:
```yaml
drone_pool:
  drone_registry:
    SD-001:
      ip: 10.10.8.101
      port: 5001
```

### Hardware Issues

#### "Connection failed: device does not exist: /dev/ttyAMA0"

**Cause:** Running in hardware mode but Pixhawk not connected

**Solutions:**
1. Check Pixhawk is connected to Pi:
   ```bash
   ls -la /dev/ttyAMA* /dev/ttyACM* /dev/ttyUSB*
   ```

2. Update connection string in config if device is different:
   ```yaml
   drone_control:
     hardware:
       connection_string: /dev/ttyACM0  # or /dev/serial0
   ```

3. Enable UART on Raspberry Pi:
   ```bash
   sudo raspi-config
   # Interface Options -> Serial Port
   # Login shell: No
   # Serial hardware: Yes
   sudo reboot
   ```

#### "collections.MutableMapping" Error (DroneKit)

**Cause:** DroneKit incompatibility with Python 3.13

**Solution:**
```bash
python fix_dronekit_py313.py
```

#### Thermal Camera Not Detected

**Cause:** I2C not enabled or camera not connected

**Solution:**
```bash
# Enable I2C
sudo raspi-config nonint do_i2c 0
sudo reboot

# Check detection
sudo i2cdetect -y 1
# Should see 0x33 for MLX90640
```

#### WiFi Access Point Won't Start

**Cause:** Interface not up or hostapd not running

**Solution:**
```bash
# Check interface state
ip link show wlan1

# Bring up manually
sudo ip link set wlan1 up
sudo systemctl restart hostapd
```

### Mission Issues

#### "Abort command failed"

**Possible causes:**
- Drone may have already completed mission
- Network communication issue
- Drone agent not responding

**Solutions:**
1. Check status first: `python emergency_control.py --ip 10.10.8.1 --status`
2. Try RTL or LAND instead
3. Check drone agent logs on Pi
4. Manually SSH to Pi and check process

#### Mission keeps running after abort

**Solutions:**
1. Check drone agent logs on Pi
2. Manually SSH to Pi and check process
3. Use kill switch as last resort (only if safe)

---

## Configuration Files

### Main Configuration (dfs_config.yaml)

```yaml
# Drone control mode
drone_control:
  mode: demo  # Options: demo, hardware
  hardware:
    connection_string: /dev/ttyAMA0
    baud: 57600

# Drone registry for network mode
drone_pool:
  drone_registry:
    SD-001:
      ip: 10.10.8.101
      port: 5001
    FD-001:
      ip: 10.10.8.102
      port: 5001

# Network configuration
network:
  primary:
    ssid: FireDrone-GS
    ip: 10.10.8.1
    subnet: 255.255.255.0
```

### Mission Areas (mission_areas.yaml)

```yaml
areas:
  area_1:
    name: "North Field"
    bounds:
      north: 33.2365
      south: 33.2355
      east: -96.8255
      west: -96.8275
    altitude: 50
    mission_type: scout
```

---

## Safety Recommendations

### Pre-Flight Checklist

- [ ] Always test without propellers first
- [ ] Keep emergency control terminal ready
- [ ] Verify battery level > 80%
- [ ] Confirm GPS lock acquired
- [ ] Check WiFi network connectivity
- [ ] Have RC transmitter ready for manual override
- [ ] Ensure clear flight area
- [ ] Have observer present

### Emergency Abort Options (in order)

1. **First try:** Ctrl+C in mission terminal
2. **Second try:** ABORT from emergency control
3. **Third try:** RTL or LAND
4. **Last resort:** KILL (only if necessary)

### Monitoring During Operations

1. Monitor drone agent logs on Pi during testing
2. Have physical access to Pi for manual shutdown
3. Keep dashboard open for real-time monitoring
4. Have emergency control script ready in separate terminal

---

## Advanced Operations

### Systemd Service Setup (Auto-Start on Boot)

After deploying to Raspberry Pi, you can set up the drone agent to start automatically:

```bash
# SSH to Raspberry Pi
ssh anshul@10.10.8.1

# Create systemd service file
sudo tee /etc/systemd/system/drone-agent.service > /dev/null << 'EOF'
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
EOF

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable drone-agent
sudo systemctl start drone-agent

# Check status
sudo systemctl status drone-agent

# View logs
sudo journalctl -u drone-agent -f
```

### Testing Network Connection

Test connection to a drone programmatically:

```bash
python -c "
from network.ground_station_client import GroundStationClient
import yaml

with open('config/dfs_config.yaml') as f:
    config = yaml.safe_load(f)

client = GroundStationClient(config)
client.register_drone('SD-001', '10.10.8.101', 5001)
client.test_connection('SD-001')
"
```

### Battery Life Optimization

| Tip | Impact |
|-----|--------|
| Keep batteries warm before flight | +2-3 min |
| Set voltage alarm to 3.8V/cell | Safer landing |
| Reduce camera streaming resolution | +1 min |
| Fly at optimal altitude (50 ft) | Better efficiency |
| Plan missions for 8-10 min max | Safety margin |

**Battery Life Reality:**
- Advertised: 15-20 minutes
- Actual (70°F): 15 minutes
- Actual (40°F): 10 minutes
- With camera/WiFi: Subtract 1 minute

---

## Data Management

### Data Output Locations

| Data Type | Location | Format |
|-----------|----------|--------|
| GPS Logs | `data/gps/` | CSV |
| Thermal Frames | `data/thermal/` | NPY + JSON |
| Still Images | `data/images/` | JPG |
| Environment Data | `data/environment/` | CSV |
| Mission Reports | `data/reports/` | JSON |
| System Logs | `logs/` | TXT |

### Data Format Examples

**GPS Log (CSV):**
```csv
timestamp,latitude,longitude,altitude,heading,satellites,fix_type,mode
1703097234.5,33.2365,-96.8265,50.2,90,12,3,AUTO
```

**Environment Data (CSV):**
```csv
timestamp,temperature,humidity,pressure,baro_altitude,baro_temperature,mode,note
1703097234.5,8.5,65,1013.25,0,9.2,AUTO,scouting
```

---

## Next Steps

### For Development
1. Install ground station requirements
2. Run demo mission to verify setup
3. Launch dashboard for monitoring
4. Test batch missions

### For Hardware Testing
1. Deploy to Raspberry Pi using deployment script
2. Connect Pixhawk and verify connection
3. Test hardware mode without propellers
4. Verify emergency control commands

### For Production Operations
1. Complete pre-flight checklist
2. Start drone agent on Raspberry Pi
3. Configure drone registry in config
4. Test network connectivity
5. Run mission from ground station
6. Monitor via dashboard
7. Keep emergency control ready

---

## Support and Documentation

### Additional Resources

| Resource | Location |
|----------|----------|
| Architecture Details | `ARCHITECTURE.md` |
| Requirements Documentation | `requirements/README.md` |
| Field Testing Guide | `FIELD_TEST.md` |
| Logging Guide | `LOGGING.md` |

### Getting Help

For issues or questions:
1. Check troubleshooting section above
2. Review system logs in `logs/` directory
3. Check drone agent logs on Raspberry Pi
4. Verify configuration files
5. Test network connectivity
