# Network Mode - Ground Station to Drone Communication

This guide explains how to run the Drone Firefighting System in **network mode**, where your Mac (ground station) sends missions over WiFi to the Raspberry Pi on the drone, which then controls the Pixhawk hardware.

## Architecture

```
Ground Station (Mac)          WiFi Network          Drone (Raspberry Pi)
┌─────────────────┐          ┌──────────┐          ┌──────────────────┐
│   main.py       │          │          │          │  drone_agent.py  │
│  (orchestrator) │ ─────────┤ 10.10.8.x├─────────▶│  (Flask server)  │
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

## Setup

### 1. Configure Drone IP Addresses

Edit `config/dfs_config.yaml` and set the IP addresses for your drones in the `drone_registry` section:

```yaml
drone_pool:
  drone_registry:
    SD-001:
      ip: 10.10.8.101  # Change to your drone's actual IP
      port: 5000
    SD-002:
      ip: 10.10.8.102
      port: 5000
    # ... etc
```

### 2. Network Configuration

Ensure both your Mac and Raspberry Pi are on the same WiFi network:

- **Network SSID**: `FireDrone-GS` (or as configured in `network.primary.ssid`)
- **Subnet**: `10.10.8.x`
- **Ground Station**: `10.10.8.1` (your Mac)
- **Drones**: `10.10.8.101`, `10.10.8.102`, etc.

### 3. Raspberry Pi Setup

On each Raspberry Pi (on the drone):

```bash
# Navigate to project directory
cd ~/drone-firefighting-system

# Activate virtual environment
source venv/bin/activate

# Ensure config has hardware mode enabled
# Edit config/dfs_config.yaml:
#   drone_control.mode: hardware
#   drone_control.hardware.connection_string: /dev/ttyAMA0

# Start the drone agent
python -m network.drone_agent --drone-id SD-001
```

The drone agent will:
- Start a Flask server on port 5000
- Listen for mission commands from ground station
- Control the Pixhawk via `/dev/ttyAMA0`
- Send telemetry back to ground station

### 4. Ground Station Setup (Mac)

On your Mac:

```bash
# Navigate to project directory
cd ~/Documents/coding/drone_firefighting_system

# Activate virtual environment
source venv/bin/activate

# Run in network mode
python main.py --demo --network
```

## Usage

### Local Demo Mode (Simulation on Mac)
```bash
python main.py --demo
```
- Runs entirely on your Mac
- Uses `DemoController` (simulated flight)
- No hardware required
- Good for testing mission logic

### Network Mode (Mac → WiFi → Pi → Pixhawk)
```bash
python main.py --demo --network
```
- Ground station (Mac) sends mission to drone over WiFi
- Drone agent (Pi) executes mission on real hardware
- Pixhawk controls actual flight
- **This is production mode**

## Troubleshooting

### "Cannot connect to SD-001 at 10.10.8.101:5000"

**Cause**: Drone agent not running or network issue

**Solutions**:
1. Check drone agent is running on Pi:
   ```bash
   ssh pi@10.10.8.101
   ps aux | grep drone_agent
   ```

2. Test network connectivity:
   ```bash
   ping 10.10.8.101
   curl http://10.10.8.101:5000/api/status
   ```

3. Check firewall on Pi:
   ```bash
   sudo ufw status
   sudo ufw allow 5000/tcp
   ```

### "Drone SD-001 not found in drone_registry config"

**Cause**: Drone not registered in config file

**Solution**: Add drone to `config/dfs_config.yaml`:
```yaml
drone_pool:
  drone_registry:
    SD-001:
      ip: 10.10.8.101
      port: 5000
```

### "Connection failed: device does not exist: /dev/ttyAMA0"

**Cause**: Running in hardware mode but Pixhawk not connected

**Solutions**:
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

## Testing Network Connection

Test connection to a drone:

```bash
python -c "
from network.ground_station_client import GroundStationClient
import yaml

with open('config/dfs_config.yaml') as f:
    config = yaml.safe_load(f)

client = GroundStationClient(config)
client.register_drone('SD-001', '10.10.8.101', 5000)
client.test_connection('SD-001')
"
```

## API Endpoints

The drone agent exposes these endpoints:

- `GET /api/status` - Get drone status
- `POST /api/mission/assign` - Assign mission to drone
- `POST /api/mission/start` - Start mission execution
- `POST /api/mission/abort` - Abort current mission
- `POST /api/rtl` - Return to launch
- `POST /api/heartbeat` - Heartbeat check

Example:
```bash
curl http://10.10.8.101:5000/api/status
```

## Configuration Summary

### Ground Station (Mac)
- Run: `python main.py --demo --network`
- Mode: Uses `GroundStationClient`
- No hardware required on Mac

### Drone (Raspberry Pi)
- Run: `python -m network.drone_agent --drone-id SD-001`
- Mode: `drone_control.mode: hardware`
- Requires Pixhawk connected to `/dev/ttyAMA0`

## Next Steps

1. ✅ Configure drone IPs in `config/dfs_config.yaml`
2. ✅ Start drone agent on Pi: `python -m network.drone_agent --drone-id SD-001`
3. ✅ Test connection from Mac: `python main.py --demo --network`
4. Monitor mission execution on dashboard: `python main.py --dashboard`
