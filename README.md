# Fire Fighting Drone System

**Author:** Anshul Ojha  
**Email:** anshulojha2018@gmail.com
**December 2025**

---

## Why I Built This

Living in Texas, I've watched brush fires get out of control way too fast, especially during dry winters. 
One of the biggest challenges in wildfire management is slow response time. Fires can double in size every minute under the right conditions, yet it often takes hours for crews to reach remote or rugged areas. By the time firefighting teams arrive, thousands of acres may already be burning. In recent wildfires, delays in detection and deployment have led to the destruction of entire neighborhoods within a single day.

Things took a turn personally inside me when I saw Califormia Palisades Jan 2025 fire creating huge devastation and human tragedy. I started thinking how can I build an exhaustive Fire Fighting System using swarm of specialized Drones to detect and suppress before they grow big.

That question turned into a few months of project in researching, finding possible approach, conceptualizing, whiteboarding ideas, CAD designing the drone and mechanisms, 3D printng, building each and every components of the drone, buying compatible hardware for drone flight, compute module and sensor  ectronics. It was a super learning and arduos journey of  integrating, home testing, field testing, calibrating in an iteration, gathering data, analyzing further modifying the design and finally making it work as a system.


## What I Actually Built

This isn't just a simulation or paper design - I built real hardware and flew it (when Texas weather cooperated  :) ).
It was a tremendqous journey and I learned a lot about drone flight, compute module, networking, sensor  ectronics, hardware integration, machine learning for fire detection and building a complex software system to manage swarm of drones and provide a consolidated dashboard to see it all in realtime.

Here's what actually works:

### Hardware

**Electronics:**
- **Flight Controller:** Pixhawk 2.4.8 32 Bit ARM Flight controller running ArduCopter 4.6.3 for managing the flight stability and flight modes instruction from Raspbery pi drone programs.
- **Companion Computer:** Raspberry Pi 4 (4GB) as main compute model running my Drone Code (python) and all integrations with onboard sensors and pixhawk, ground station controllers and backup RC controller.
- **Drone ESC:** Readytosky 2-4S 40A Brushless ESC Electronic Speed Controller 5V/3A BEC for F450 450mm S500 ZD550 RC Helicopter Quadcopter(4PCS)
- **WiFi:** TP-Link AC600 USB WiFi Adapter, Dual Band (2.4GHz and 5GHz), 5dBi High gain antenna, Dual Band, wanted more than 200 ft ft+ range compared to built-in wifi on Raspberry pi.
- **Power distribution board:** Acxico 2 pcs Drone Power Distribution Board XT60 3-4S 9-18V 5V 12V Output PDB      
- **Flight Transmitter:** Flysky FS-i6X 6-10(Default 6)CH 2.4GHz AFHDS RC Transmitter w/ FS-iA6B Receiver

**Sensors:**
- **Thermal Camera:** MLX90640 (32x24 pixels, 110° FOV) for capturing thermal image at ~50ft. Taking pics every 1 second (configurable) + periodic video (full HD format) and streaming on demand during field testing.
- **Temperature and Humidity Sensor:** SHILLEHTEK DHT22 Digital Temperature and Humidity Sensor for capturing temperature and humidity at ~50ft.
- **Visual Camera:** Arducam IMX708 Autofocus Pi Camera V3 120°(D) for fire detection still confirmation shots + intermediate videos/streaming on demand during testing. 
- **GPS Module:** NEO-M8N GPS Module      

**Drone:**
- **Drone Frame:** Custom designed from scracth and 3D printed. Arms, Stand, Body Modules (2 layers), Electronics Bay, Shock pad, Camera Enclosure and Swivel Mounts
- **Drone Motors:** CW Emax Mt2213 935kv 2212 Brushless Motor CW for F450 X525 Quadcopter Hexcopter
- **Drone Propellers:** QWinOut 3k Carbon Fiber Propeller Cw CCW 1045 
- **Battery:** Zeee 4S Lipo Battery 14.8V 5200mAh 100C with EC5 Plug (~ 12-15 min flight time at peak performance, less in cold weather as most of my testing happened in Oct, Nov, Dec 2025)
- **Battery Charger:** IMAX B6 80W Lipo Battery Balance Charger 6A Discharger

**Design and Build Tools:**
- **CAD:** Onshape
- **3D Printer:** Bambu Lab - P1S Combo 3D Printer
- **3D Printer Filament:** PETG for Drone Arms and Stand, PLA for Electronics Bay, Shock Pad and Camera Enclosure and Swivel Mounts

**Software Tools:**
- **IDE:** Visual Studio Code
- **Version Control:** Git and Github
- **AI usage** Cluade.ai for getting help in sensor adapter packages and integration, networking research and machine learning model training
- **ML Model** Tensorflow Lite for my embedded system and Keras for training
- **ML Training Datasets** Trained on my custom dataset of fire and non fire images based on drone images captured in field testing. For larger Ground Control Station (GCS) and Drone, I used Kaggle dataset. https://www.kaggle.com/datasets/phylake1337/fire-dataset as its light weight with 1000 images and overall built model is < 50mb to be processed on edge on my drone.
- **Data Storage** SQLite for mission/detection logging
- **Dashboard** Dash for real-time dashboard

- **3D Printer:** Bambu Lab - P1S Combo 3D Printer
- **3D Printer Filament:** PETG for Drone Arms and Stand for heavy load and durability with high 3D infill prints, PLA for Electronics Bay, Shock Pad and Camera Enclosure and Swivel Mounts

### Software Stack
- Python 3.13 (had to patch DroneKit to work - more on that below)
- DroneKit for Pixhawk communication via MAVLink
- OpenCV for image processing
- Custom thermal analysis algorithms
- SQLite for mission/detection logging
- Dash for real-time dashboard
- Other opensource mentioned in requirements.txt

## Features That Work
[Built] **Drone Fire Fighting System:** Complete system capable of working with configutable no of SD (Scout Drones) and FD (Fire Drones), Area of operation Flight Configuration, Electronics/Sensor Configuration, Mode of operation from Validation, Test, Simulation, Hardware (test) to full production mode. 
[Built] **Autonomous Flight:** Pre-programmed waypoint missions with every aspect configurable, See @dfs_config.yaml, @mission_area.yaml for more details. 
[Built] **Fire Detection:** Thermal + visual confirmation (ML model trained on Kaggle dataset)  
[Built] **Mission Planning:** Generate search patterns (serpentine) based on area size. During my research figured serpentine is the most effective way to cover a larger area for scouting.  
[Built] **Data Logging:** GPS, thermal, environmental data in standard formats. 
[Built] **Swarm Simulation:** Multi-drone coordination. This was heart of me building this Ground Station control, building the Drone Swarm Network and Ground Station to Drone communication. Though I built a single drone, the system scales for any number of drones. So to visualize I built the complete system, various type of simulation as single operation, batch operation, fire injection to see how it will all work together. The code is a production ready code where one can add drones, configure the IPs and do some basic integration testing to fly all in a mission. This was a very ambitious goal and I am extremely proud of it.
[Built] **Drone Fire Fighting System - Mission Control:** Real-time dashboard to monitor the mission and control the drones. This is where you can see the visualization of drone as they fly for different missions set through configuration files @dfs_config.yaml, @mission_area.yaml.

## My Testing Setup

**Location:** Open field near my community in Prosper, TX, 75078, https://maps.app.goo.gl/su4V1r5PobqoLV4S7
  
**Test Dates:** Oct, Nov, Dec 2025  
**Weather Conditions:** 35-45°F, 5-12 mph winds (when I could actually fly)  
**Test Method:** GasOne Diethylene 6 Hour Wick Liquid Gel Fuel Can, flew at 30-50 ft altitude

**Why heated gravel did not work?**  
Can't exactly start real fires in a public field. Heated gravel in my oven to 180°F (82°C), spread it out, and the thermal camera picked it up perfectly from 50 feet. But while taking it in a insualted case it dropped temp pretty fast in open field and I was testing in cold weather. So used food warmer spirit can and had fire extinguiser for safety. It was tested in a isolated, no grass, land with no dry garss or vegitation near by. 

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

## Things That Went Wrong (And How I Fixed Them)

### 1. The DroneKit Python 3.13 Disaster
Upgraded to Python 3.13 and DroneKit immediately broke. Error: `collections.MutableMapping` doesn't exist anymore (moved in Python 3.11+). Spent half a day debugging before writing a patch script (`fix_dronekit_py313.py`) to fix it automatically.

**Solution:** Monkey-patch the library on import. Not pretty, but works.

### 2. WiFi Range Was Terrible
Pi's built-in WiFi? Maybe 50-100 feet on a good day. Tried the ALFA AWUS036ACH (everyone recommends it) but it weighs 250 grams - too heavy for my frame.

**Solution:** Found TP-Link AC600 Nano adapters. Only 3 grams, 200+ foot range. Game changer.

### 3. Cold Weather Battery Death
Texas winters aren't that cold (35-45°F) but LiPo batteries HATE it. Lost 30% capacity just from temperature. Flight time dropped from 15 min to 10 min.

**Solution:** Keep batteries inside my jacket until flight time. Also learned to set voltage alarm higher (3.8V vs 3.7V per cell).

### 4. GPS Drift Is Annoying
Even with 12+ satellites, GPS position bounces around ±2 feet constantly. Makes it hard to return to exact locations for repeat measurements.

**Solution:** Average position over 10 readings. Also added GPS smoothing in post-processing.

### 5. MLX90640 Quirks
Thermal camera randomly glitches if you read too fast. Needs minimum 2 seconds between frames or data gets corrupted.

**Solution:** Set refresh rate to 8Hz max. Also added error handling to skip bad frames.

### 6. Wind Is The Enemy
Can't fly in winds over 15 mph with my setup. Drone becomes unstable and thermal footage is unusable (too much vibration).

**Solution:** Check weather forecast. Only fly on calm days. Lost several weekends to this.

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


## Development Notes

This project went through several iterations:

**Stage 0 (Q1/2025):** Identification of problem, California Jan 2025 Palisades wildfires    
**Stage 1 (Q2 2025):** Conceptualization, Research, Built CAD model, showcased in my PCIS (Prosper Career Independent Study) and to my mentors. Till this point I was not committed to build a field drone and real system. I built a Python Visual Simulation model how it will work but no idea how to build a real system.
https://www.anshulojha.com/pcis
https://www.anshulojha.com/dp
https://youtu.be/oCuLS8m1QiQ
 and research and planning, Pure simulation to test mission logic  

**Stage 2 (Sep 2025):** Felt strong desire to build, brainsormed, white boarded, identified components and areas to focus. Still not sure whether I will just build the drone from scratch with sensors or will move forward with complete system.

**Stage 3 (Oct 2025):** Got the 3D Printer, Started getting parts and electronics. Went through numerous iteration of CAD design for components, part brekage during minor and mahor crashes, rectifying designs. Extensive research on elctronics, compatibility, limits, software adapters. Still things are pretty meshy and not fully integrated.

**Stage 4 (Nov 2025):** Lot of effort went in creating Test bed, Test Harness in my backyard, Simulating Fire which is safe to do without violating local laws and regulations. A portable module which I can keep it near my desk and do hardware and sensor test without spending lot of time in assembling onto drone and weight for right weather with low windspeed < 5-10 mph>

**Phase 5 (final) (Dec 2025):** Lot of field testing, discovered all the "real world" problems and rectified them. Built the complete software system to manage swarm of drones. Various visualization utility to see the thermal, gps, temp and flight data.


## Resources I Used

- **DroneKit Documentation:** For MAVLink protocol
- **ArduPilot Wiki:** Flight controller setup
- **Stack Overflow:** Probably 50+ questions
- **YouTube - Painless360:** Pixhawk setup tutorials
- **Adafruit MLX90640 Guide:** Thermal camera integration
- **Kaggle Fire Dataset:** ML model training data
- **GitHub - aircrack-ng/rtl8812au:** WiFi driver
- **Copilot and Claude - Haversine Formula:** GPS distance calculations

## Acknowledgments

Thanks to:
- The ArduPilot community for flight controller help
- Adafruit for great sensor documentation
- GitHub user morrownr for WiFi driver patches
- Everyone on Stack Overflow who answered my questions
- My parents for funding and letting me buy hardware, electronics. Helped me in doing field testing and supporting throughout.

## License

Apache License 2.0 - See LICENSE file for details.

This license provides patent protection for the fire detection algorithms and 
mission planning methods. You can use, modify, and distribute this code, 
including commercially, as long as you include the license and NOTICE file.

## Contact

**Anshul Ojha**  
Email: anshulojha613@gmail.com  
GitHub: [@anshulojha613](https://github.com/anshulojha613)

---

**December 2025**

*This project spanned over two qtrs with most of build and testing in Oct, Nov, Dec 2025. It represents if you put your mind and passion, you can build amazing thing. It's not perfect, but it's mine.*
