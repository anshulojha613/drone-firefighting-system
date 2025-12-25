# Operations Guide

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
| Start drone agent | `network/drone_agent.py` | `python network/drone_agent.py --drone-id SD-001` | C |

**Modes:** A = Simulation, B = Hardware Testing (no flight), C = Production (actual flight)

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
# ON GROUND STATION (Laptop):
# 1. Start dashboard for monitoring
python main.py --dashboard

# ON DRONE (Raspberry Pi):
# 2. Ensure hardware mode
# config/dfs_config.yaml: drone_control.mode: 'hardware'

# 3. Start drone agent
python network/drone_agent.py --drone-id SD-001 --port 5001

# ON GROUND STATION:
# 4. Execute mission (will communicate with drone over WiFi)
python main.py --demo
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

## Quick Start

### Installation
```bash
cd drone_firefighting_system
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Run Demo Mission
```bash
python main.py --demo
```

### Launch Dashboard
```bash
python main.py --dashboard
# Open: http://localhost:8050
```

## Running Missions

### Demo Mode (Simulation)
```bash
# Single demo mission
python main.py --demo

# With dashboard
python main.py --dashboard &
python main.py --demo
```

### Batch Missions: Sequential vs Parallel Execution

The system supports two execution modes for batch missions:

#### Sequential Mode (Default)
Tasks are executed one after another with configurable delays between missions.

```bash
# Run with default settings (sequential)
python batch_mission.py

# Customize delay between missions
python batch_mission.py --mode sequential --mission-delay 3
```

**Configuration:**
```yaml
# config/dfs_config.yaml or mission_areas.yaml
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

# Customize parallel execution
python batch_mission.py --mode parallel --workers 5 --dispatch-delay 1.0
```

**Configuration:**
```yaml
# config/dfs_config.yaml
mission_planning:
  execution:
    mode: parallel
    parallel_max_workers: 3  # Max concurrent missions
    task_dispatch_delay_sec: 0.5  # Delay between dispatches
```

**Use when:**
- Have multiple idle drones available
- Need faster area coverage
- Simulating real-world multi-drone operations

**Parameters:**
- `--mode`: Choose `sequential` or `parallel`
- `--workers`: Max concurrent missions (parallel only)
- `--dispatch-delay`: Seconds between task dispatches (parallel only)
- `--mission-delay`: Seconds between missions (sequential only)
- `--simulate-fires`: Inject simulated fire detections to trigger FD drone dispatch

#### Simulating Fire Detection

To see Firefighter (FD) drones in action during batch missions, use the `--simulate-fires` flag:

```bash
# Sequential with simulated fires
python batch_mission.py --simulate-fires

# Parallel with simulated fires
python batch_mission.py --mode parallel --workers 3 --simulate-fires
```

This will:
1. Execute SD (Scouter) missions normally
2. Inject a simulated fire detection at the center of each mission area
3. Auto-dispatch FD (Firefighter) drones to suppress the fires
4. Show the complete fire detection → dispatch → suppression workflow

### Custom Mission
```python
from mission_control.orchestrator import MissionOrchestrator

orchestrator = MissionOrchestrator()

flight_area = {
    'corner_a': {'latitude': 33.2271, 'longitude': -96.8252},
    'corner_b': {'latitude': 33.2272, 'longitude': -96.8279},
    'corner_c': {'latitude': 33.2258, 'longitude': -96.8279},
    'corner_d': {'latitude': 33.2257, 'longitude': -96.8252}
}

task = orchestrator.create_scout_task(flight_area, priority='high')
drone = orchestrator.assign_task_to_drone(task.task_id)
```

## Testing

### Run All Tests
```bash
python tests.py
```

### Test Simulation Only
```bash
python tests.py --simulation
```

## ML Fire Detection

The system uses two fire detection modules:
- **`ml_training/fire_detector.py`** - Thermal-based detection (SD drones)
- **`modules/fire_detector.py`** - Visual/ML-based detection (confirmation)

### Detection Pipeline
1. Scouter drone captures thermal frames during flight
2. Thermal detector identifies hotspots (>50C, min 3 pixels)
3. Visual detector confirms fire using color analysis or ML model
4. Only validated detections trigger firefighter dispatch

### Test Fire Detection
```bash
# Test thermal detection
python -c "
import numpy as np
from ml_training.fire_detector import FireDetector

detector = FireDetector(hotspot_threshold_c=50.0, min_pixels=3)

# Create test thermal frame with hotspot
frame = np.random.uniform(20, 35, (24, 32))
frame[10:15, 15:20] = 75  # Simulated fire

gps = {'latitude': 33.227, 'longitude': -96.825, 'altitude': 15.0}
is_fire, info = detector.detect_fire(frame, gps)

print(f'Fire detected: {is_fire}')
print(f'Max temp: {info.get(\"max_temperature_c\", 0):.1f}C')
print(f'Confidence: {info.get(\"confidence\", 0):.2f}')
"
```

### Test Visual Detection
```bash
# Test color-based fire detection on an image
python -c "
import yaml
from modules.fire_detector import FireDetector

with open('config/dfs_config.yaml') as f:
    config = yaml.safe_load(f)

detector = FireDetector(config, simulation_mode=True)

# Test with a sample image (replace with actual path)
# result = detector.detect_fire_in_image('path/to/image.jpg')
print('Visual detector initialized')
print(f'Mode: {\"simulation\" if detector.simulation_mode else \"ML model\"}')
print(f'Confidence threshold: {detector.confidence_threshold}')
"
```

### Configure Detection Thresholds
Edit `config/dfs_config.yaml`:
```yaml
fire_detection:
  thermal:
    hotspot_threshold_c: 50.0    # Min temp to flag as hotspot
    min_confidence: 0.7
    min_hotspot_pixels: 3        # Min pixels above threshold
  image_recognition:
    confidence_threshold: 0.7    # Min confidence for ML detection
    input_size: [224, 224]
    model_path: null             # Path to TFLite model (optional)
```

### Using a Custom ML Model
1. Train a fire detection model (binary classifier)
2. Export to TensorFlow Lite format (.tflite)
3. Update config:
```yaml
fire_detection:
  image_recognition:
    model_path: 'models/fire_detector.tflite'
```
4. Test the model:
```bash
python -c "
import yaml
from modules.fire_detector import FireDetector

with open('config/dfs_config.yaml') as f:
    config = yaml.safe_load(f)

detector = FireDetector(config, simulation_mode=False)
result = detector.detect_fire_in_image('test_image.jpg')
print(f'Detection method: {result[\"method\"]}')
print(f'Fire detected: {result[\"detected\"]}')
"
```

### Pre-Production ML Checklist
- [ ] Thermal threshold tuned for environment (default 50C)
- [ ] Visual confidence threshold set appropriately (default 0.7)
- [ ] Test with sample fire images to verify detection
- [ ] Test with non-fire images to verify no false positives
- [ ] If using ML model: model loaded successfully
- [ ] Run full simulation to verify end-to-end detection

## ML Model Training

### Quick Start: Train Fire Detection Model
```bash
# 1. Setup dataset directory
python ml_training/dataset_utils.py --setup

# 2. Create sample dataset for testing (optional)
python ml_training/train_fire_model.py --create-sample

# 3. Train model
python ml_training/train_fire_model.py --data-dir data/training_images --epochs 20

# 4. Test model
python ml_training/test_model.py --model models/fire_detector.tflite --fire-dir data/training_images/fire
```

### Dataset Preparation
```bash
# Show dataset sources
python ml_training/dataset_utils.py --sources

# Setup directory structure
python ml_training/dataset_utils.py --setup --data-dir data/training_images

# Import images
python ml_training/dataset_utils.py --import-fire /path/to/fire/images
python ml_training/dataset_utils.py --import-no-fire /path/to/normal/images

# Augment dataset to 500 images per category
python ml_training/dataset_utils.py --augment 500

# Resize all images to 224x224
python ml_training/dataset_utils.py --resize 224 224

# Validate images
python ml_training/dataset_utils.py --validate

# Check stats
python ml_training/dataset_utils.py --stats
```

Expected directory structure:
```
data/training_images/
    fire/           # Images containing fire (min 100 recommended)
        fire_001.jpg
        fire_002.jpg
    no_fire/        # Normal images without fire (min 100 recommended)
        normal_001.jpg
        normal_002.jpg
```

### Training Options
```bash
# Basic training (MobileNetV2 transfer learning)
python ml_training/train_fire_model.py --data-dir data/training_images

# Train with fine-tuning (better accuracy, longer training)
python ml_training/train_fire_model.py --data-dir data/training_images --fine-tune

# Train simple CNN (no transfer learning, faster)
python ml_training/train_fire_model.py --data-dir data/training_images --no-transfer

# Custom epochs and batch size
python ml_training/train_fire_model.py --epochs 50 --batch-size 16
```

### Model Output
Training produces three model files in `models/`:
- `fire_detector.keras` - Full Keras model (for further training)
- `fire_detector.tflite` - TFLite model (for deployment)
- `fire_detector_quantized.tflite` - Quantized TFLite (smaller, faster on Pi)

### Testing the Model
```bash
# Show model info and stats
python ml_training/test_model.py --info

# Test single image
python ml_training/test_model.py --image test.jpg

# Test directory of images
python ml_training/test_model.py --dir test_images/

# Test accuracy on labeled datasets
python ml_training/test_model.py --fire-dir data/training_images/fire --no-fire-dir data/training_images/no_fire

# Benchmark inference speed
python ml_training/test_model.py --benchmark test.jpg --iterations 100

# Combined: info + benchmark
python ml_training/test_model.py --info --benchmark test.jpg
```

### Model Info Output
```
[INFO] MODEL DETAILS
   Path: models/fire_detector.tflite
   Type: TFLite
   File Size: 9.08 MB
   Input Size: 224x224
   Input Shape: [1, 224, 224, 3]

[FILES] Available models:
   fire_detector.keras: 11.07 MB
   fire_detector.tflite: 9.08 MB
   fire_detector_quantized.tflite: 4.57 MB
```

### Deploy Model
1. Copy model to drone:
```bash
scp models/fire_detector.tflite anshul@192.168.7.195:~/drone-firefighting-system/models/
```

2. Update config:
```yaml
# config/dfs_config.yaml
fire_detection:
  image_recognition:
    model_path: 'models/fire_detector.tflite'
```

3. Test on drone:
```bash
python ml_training/test_model.py --model models/fire_detector.tflite --image test.jpg
```

### Training Tips
- **Minimum dataset**: 100 images per category (more is better)
- **Image sources**: Kaggle fire datasets, FLAME dataset, custom drone footage
- **Augmentation**: Use `--augment` to expand small datasets
- **Transfer learning**: Recommended for small datasets (<1000 images)
- **Fine-tuning**: Enable with `--fine-tune` for better accuracy
- **Quantized model**: Use `fire_detector_quantized.tflite` on Raspberry Pi for faster inference

### Test Network Communication
```bash
# On drone (Raspberry Pi)
python network/drone_agent.py --drone-id SD-001 --port 5001

# On ground station
python tests.py --network --drone-ip 10.10.8.100
```

### Test Hardware Connection
```bash
# Requires Pixhawk connected
python tests.py --hardware
```

## Configuration

Edit `config/dfs_config.yaml`:

### Switch Between Demo/Hardware Mode
```yaml
drone_control:
  mode: 'demo'      # or 'hardware'
  hardware:
    connection_string: '/dev/ttyAMA0'
    baud: 57600
```

### Drone Pool Size
```yaml
drone_pool:
  scouter_drones:
    count: 5
  firefighter_drones:
    count: 3
```

### Fire Detection Thresholds
```yaml
fire_detection:
  thermal:
    hotspot_threshold_c: 50.0
  image_recognition:
    confidence_threshold: 0.7
```

## Database Operations

### View Database
```bash
sqlite3 database/dfs.db
.tables
SELECT * FROM drones;
SELECT * FROM tasks ORDER BY created_at DESC LIMIT 5;
SELECT * FROM fire_detections;
```

### Reset Database
```bash
rm database/dfs.db
python main.py  # Reinitializes
```

### Reset Drone States
```bash
python -c "
from database import DatabaseManager
db = DatabaseManager()
db.reset_all_drones_to_idle()
print('All drones reset to IDLE')
"
```

## Deployment to Raspberry Pi

### Copy Files
```bash
scp -r drone_firefighting_system anshul@192.168.7.195:~/
```

### Or Use Deploy Script
```bash
./deploy_to_pi.sh
```

### Start Drone Agent on Pi
```bash
ssh anshul@192.168.7.195
cd drone-firefighting-system
source venv/bin/activate
python network/drone_agent.py --drone-id SD-001 --port 5001
```

### Auto-Start on Boot
```bash
# On Raspberry Pi
sudo systemctl enable drone-agent
sudo systemctl start drone-agent
```

## Hardware Mode (Pixhawk)

### Prerequisites
```bash
pip install dronekit pymavlink
python fix_dronekit_py313.py  # Patch for Python 3.13
```

### Test Pixhawk Connection
```bash
python -c "
from drone_control import ControllerFactory
ctrl = ControllerFactory.create_controller('SD-001')
ctrl.connect()
print(f'Battery: {ctrl.get_battery()}%')
ctrl.disconnect()
"
```

### Switch to Hardware Mode
Edit `config/dfs_config.yaml`:
```yaml
drone_control:
  mode: 'hardware'
```

## Troubleshooting

### Module Not Found
```bash
# Ensure virtual environment is active
source venv/bin/activate
```

### Database Locked
```bash
# Kill any running processes
pkill -f "main.py"
rm database/dfs.db
```

### Network Connection Failed
```bash
# Check drone agent is running
ping 10.10.8.100
curl http://10.10.8.100:5001/api/status
```

### DroneKit Import Error (Python 3.13)
```bash
python fix_dronekit_py313.py
```

### No Drones Available
```bash
sqlite3 database/dfs.db "UPDATE drones SET state='idle';"
```

## Data Output

### Mission Data Location
```
data/
└── SD-001_20251223_120000/
    ├── gps/
    │   └── SD-001_20251223_120000_gps.csv
    ├── thermal/
    │   ├── frame_0001.npy
    │   └── frame_0001.csv
    ├── environment/
    │   └── SD-001_20251223_120000_environment.csv
    ├── images/
    │   ├── img_0000.jpg
    │   └── img_0000_metadata.json
    └── logs/
        └── suppression_log.json
```

### Clean Test Output
```bash
rm -rf data/test_output/*
```

## System Status Check

```python
from mission_control.orchestrator import MissionOrchestrator

orchestrator = MissionOrchestrator()
status = orchestrator.get_system_status()

print(f"Total Drones: {status['drones']['total']}")
print(f"Idle Drones: {status['drones']['idle']}")
print(f"Active Tasks: {status['tasks']['executing']}")
print(f"Fire Detections: {status['detections']['total']}")
```

## Logs

### View System Logs
```bash
tail -f logs/dfs.log
```

### View Drone Agent Logs
```bash
# On Raspberry Pi
journalctl -u drone-agent -f
```
