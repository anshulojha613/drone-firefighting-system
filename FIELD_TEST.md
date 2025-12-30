# Field Testing Guide

## Overview

This document details the field testing process, results, and analysis from real-world drone operations conducted in Prosper, TX during October-December 2025.

## Test Environment

### Location
- **Primary Site:** Open field near Prosper, TX 75078
- **Coordinates:** 33.2265°N, -96.8265°W (approximate)
- **Terrain:** Flat, tilled agricultural land
- **Conditions:** No grass or vegetation (safe for controlled fire testing)
- **Access:** Public field with clear line of sight

### Test Dates & Conditions
- **Period:** October - December 2025
- **Temperature Range:** 35-45°F (cold weather testing)
- **Wind Conditions:** <10 mph (flight-safe conditions)
- **Weather Challenges:** Limited flight windows due to Texas winter winds

### Safety Setup
- Fire extinguisher on-site
- Observer present for all flights
- RC transmitter ready for manual override
- Clear 100+ ft radius around test area
- No dry vegetation nearby

## Test Equipment

### Fire Simulation
**Initial Attempt (Failed):**
- Heated gravel stones to 180°F (82°C) in oven
- Transported in insulated case
- **Problem:** Temperature dropped too quickly in cold outdoor conditions
- **Result:** Insufficient thermal signature for detection at altitude

**Final Solution (Successful):**
- GasOne Diethylene 6 Hour Wick Liquid Gel Fuel Cans
- Stable flame temperature
- Consistent thermal signature
- Safe, controlled burn
- Easy to extinguish

### Visual Reference
- Colored bed sheets on ground for visual confirmation
- Used to validate camera autofocus and image capture
- Provided scale reference for altitude testing

## Test Phases

### Phase 1: Bench Testing (Study Desk)
**Duration:** October 2025

**Setup:**
- Portable test unit: Pixhawk + Raspberry Pi + sensors
- Mounted on styrofoam block with paper tape
- Connected to portable power bank
- Side-by-side with Mac for development

**Tests Performed:**
- Sensor integration validation
- Software deployment and triggering
- Data collection verification
- Communication protocol testing

**Results:**
- Rapid iteration on code changes
- Identified sensor compatibility issues
- Validated data formats
- Established baseline performance

### Phase 2: Backyard Flight Testing
**Duration:** October-November 2025

**Setup:**
- Custom flight harness system
- Maximum height: 6 ft (safety tether)
- Propeller guards installed
- Battery monitoring active

**Tests Performed:**
- Flight calibration
- Motor lift and power verification
- ESC tuning
- GPS lock acquisition
- Sensor operation during flight vibration
- Battery drain under load

**Results:**
- Validated flight-worthy status
- Identified vibration issues with camera
- Calibrated PID settings
- Confirmed 10-12 min flight time in cold weather

### Phase 3: Field Flight Testing
**Duration:** November-December 2025

**Altitude Tests:**

| Altitude | Coverage Area | Thermal Detection | Visual Quality | Notes |
|----------|---------------|-------------------|----------------|-------|
| 20 ft | 36 × 27 ft | Excellent | Very clear | Too low, limited coverage |
| 30 ft | 55 × 41 ft | Excellent | Clear | Good for small areas |
| **50 ft** | **91 × 69 ft** | **Good** | **Good** | **Optimal balance** |
| 70 ft | 128 × 96 ft | Fair | Moderate | Detection accuracy drops |
| 100 ft | 183 × 137 ft | Poor | Poor | Too high for reliable detection |

**Optimal Altitude:** 50 feet
- Best balance of coverage vs detection accuracy
- Thermal signature clearly visible
- Visual confirmation reliable
- Safe altitude for emergency procedures

## Test Results

### Thermal Detection Performance

**MLX90640 Sensor (32×24 pixels, 110° FOV):**
- **Detection Range:** Effective up to 50 ft
- **Minimum Fire Size:** ~3 ft diameter at 50 ft altitude
- **Temperature Threshold:** 50°C (122°F) above ambient
- **Frame Rate Achieved:** 8 Hz (target was 16 Hz, limited by hardware)
- **False Positive Rate:** <5% with dual confirmation (thermal + visual)

**Thermal Anomalies Detected:**
- Fire (gel fuel cans): 100% detection rate
- Hot car roofs: Filtered by size/shape analysis
- Sunlit rocks: Filtered by temporal consistency check
- Human body heat: Filtered by temperature threshold

### Visual Detection Performance

**Arducam IMX708 Camera (120° FOV):**
- **Image Resolution:** 1920×1080 (Full HD)
- **Autofocus Performance:** Good at 50 ft, degraded in high wind
- **ML Model Accuracy:** 92% on field-captured dataset
- **Capture Interval:** 1 second (configurable)
- **Storage:** ~500 MB per 10-minute mission

### GPS & Navigation

**NEO-M8N GPS Module:**
- **Satellite Lock:** 12+ satellites typical
- **Position Accuracy:** ±2 ft horizontal (with smoothing)
- **Altitude Accuracy:** ±3 ft vertical
- **Lock Time:** 30-60 seconds from cold start
- **Drift:** ±2 ft constant variation (averaged over 10 readings)

**Waypoint Navigation:**
- **Pattern:** Serpentine (lawnmower) most effective
- **Waypoint Accuracy:** Within 3 ft of target
- **Speed:** 3-5 m/s cruise speed
- **Coverage:** ~2 acres per 10-minute flight at 50 ft

### Battery Performance

**Zeee 4S 5200mAh LiPo:**

| Condition | Flight Time | Notes |
|-----------|-------------|-------|
| 70°F, no payload | 15 min | Baseline performance |
| 70°F, full sensors | 13-14 min | Production configuration |
| 40°F, full sensors | 10-12 min | Cold weather penalty |
| High wind (15+ mph) | 8-10 min | Increased power draw |

**Cold Weather Mitigation:**
- Keep batteries inside jacket until flight
- Set voltage alarm to 3.8V/cell (vs 3.7V standard)
- Reduced flight time planning to 8-10 min max

### Communication Range

**TP-Link AC600 WiFi Adapter:**
- **Line of Sight:** 200-250 ft reliable
- **With Obstacles:** 100-150 ft
- **Telemetry Rate:** 1 Hz (position, battery, status)
- **Image Transfer:** 2-3 seconds per full-res image
- **Connection Stability:** 95%+ in open field

**Raspberry Pi Built-in WiFi (Backup):**
- **Range:** 50-100 ft
- **Used for:** Emergency fallback only

## Data Collected

### Mission Data Structure
```
data/SD-001_YYYYMMDD_HHMMSS/
├── gps/
│   └── SD-001_YYYYMMDD_HHMMSS_gps.csv
├── thermal/
│   ├── frame_0001.npy (32×24 thermal array)
│   ├── frame_0001.csv (metadata)
│   └── ... (1 frame per second)
├── environment/
│   └── SD-001_YYYYMMDD_HHMMSS_environment.csv
├── images/
│   ├── img_0001.jpg
│   ├── img_0001_metadata.json
│   └── ... (1 image per second)
└── logs/
    └── mission_log.json
```

### Sample Data Statistics

**Typical 10-Minute Mission:**
- GPS Points: ~600 (1 Hz)
- Thermal Frames: ~600 (8 Hz target, achieved ~1 Hz in practice)
- Visual Images: ~600 (1 Hz)
- Total Data Size: ~800 MB
- Fire Detections: 0-5 (depending on test scenario)

## Key Findings

### What Worked Well

1. **Thermal Detection System**
   - Reliable fire detection at 50 ft altitude
   - Low false positive rate with dual confirmation
   - Effective temperature threshold tuning

2. **Autonomous Flight**
   - Waypoint navigation accurate within 3 ft
   - Serpentine pattern provides complete coverage
   - Stable flight in calm conditions

3. **Data Collection**
   - All sensor data synchronized and logged
   - Standard formats (CSV, NPY, JSON) for analysis
   - Complete mission telemetry captured

4. **System Integration**
   - Pixhawk + Raspberry Pi communication stable
   - Sensor integration reliable
   - Network communication functional

### Challenges Encountered

1. **Weather Dependency**
   - Limited flight windows due to wind (>15 mph = no flight)
   - Cold weather reduced battery life 20-30%
   - Multiple weekends lost to weather

2. **GPS Drift**
   - Constant ±2 ft position variation
   - Required averaging for accurate positioning
   - Loiter mode unreliable due to GPS/EKF issues

3. **Thermal Camera Limitations**
   - 32×24 resolution limits detection range
   - Could not achieve >8 Hz frame rate reliably
   - Occasional frame corruption at higher rates

4. **Camera Autofocus**
   - Degraded performance in high wind/vibration
   - Gimbal would improve image quality significantly
   - Manual focus more reliable but less flexible

5. **Flight Controller Tuning**
   - Required extensive calibration for custom frame
   - Loiter mode caused one crash (GPS/EKF reset mid-flight)
   - Manual override essential for safety

6. **ML Model Training**
   - Public datasets (forest fires) didn't match field conditions
   - Required custom dataset from actual drone footage
   - Retrained model on field-captured images for 92% accuracy

## Lessons Learned

### Technical

1. **Altitude Selection Critical**
   - 50 ft is optimal for MLX90640 sensor
   - Higher = more coverage but worse detection
   - Lower = better detection but inefficient coverage

2. **Sensor Refresh Rates**
   - Target 8 Hz for thermal (achieved in practice)
   - 1 Hz sufficient for GPS/visual in scouting missions
   - Higher rates cause data corruption with current hardware

3. **Battery Management**
   - Always plan for worst-case (cold weather) flight time
   - Keep batteries warm until flight
   - Set conservative voltage alarms

4. **Testing Methodology**
   - Portable bench setup accelerated development 10x
   - Backyard harness testing prevented costly crashes
   - Field testing revealed real-world issues simulation missed

### Operational

1. **Safety First**
   - RC transmitter manual override essential
   - Clear flight area mandatory
   - Observer improves situational awareness
   - Weather monitoring critical

2. **Iterative Development**
   - Each crash improved design
   - Version numbers tell the story (v1, v2, v3, v4)
   - 3D printing enabled rapid iteration

3. **Data Validation**
   - Post-flight data review essential
   - Identified sensor issues early
   - Validated detection algorithms with ground truth

## Performance Metrics

### Mission Success Rate
- **Total Missions:** 25+ field flights
- **Successful Completions:** 22 (88%)
- **Aborted (Weather):** 2 (8%)
- **Crashes:** 1 (4% - GPS/EKF issue in Loiter mode)

### Detection Accuracy
- **True Positives:** 47/50 (94%)
- **False Positives:** 3/50 (6%)
- **False Negatives:** 3/50 (6%)
- **Overall Accuracy:** 94%

### System Reliability
- **Pixhawk Connection:** 100% (no failures)
- **Sensor Operation:** 98% (occasional thermal glitches)
- **WiFi Communication:** 95% (range-dependent)
- **GPS Lock:** 100% (30-60 sec acquisition)

## Recommendations for Future Testing

### Immediate Improvements
1. Upgrade to MLX90641 (192×144) thermal camera
2. Add 2-axis gimbal for camera stabilization
3. Implement RTK GPS for better position accuracy
4. Use carbon fiber frame to reduce weight
5. Upgrade to higher capacity battery (8000mAh)

### Testing Enhancements
1. Test in warmer weather (60-80°F) for baseline battery performance
2. Conduct multi-drone swarm tests with 2-3 drones
3. Test LoRa communication for extended range
4. Validate fire suppression system (if/when built)
5. Test in varied terrain (hills, trees, obstacles)

### Data Collection
1. Expand training dataset to 1000+ images per category
2. Collect data across different fire types and sizes
3. Test detection in various lighting conditions
4. Validate detection at different altitudes systematically

## Conclusion

Field testing validated the core system design and identified critical real-world constraints. The drone successfully detected simulated fires at 50 ft altitude with 94% accuracy. Key limitations are thermal camera resolution, cold weather battery performance, and GPS drift. The system is production-ready for scouting missions with the understanding that weather and environmental conditions significantly impact performance.

**Overall Assessment:** System performs as designed within documented constraints. Ready for expanded testing with multiple drones and varied scenarios.

---

**Last Updated:** December 2025  
**Test Location:** Prosper, TX 75078  

