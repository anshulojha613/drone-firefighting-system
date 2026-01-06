# Fire Fighting Drone System

**Author:** Anshul Ojha  
**Email:** anshulojha2018@gmail.com  
**Website:** www.anshulojha.com  
**Project:** https://www.anshulojha.com/dp  

**Project Short Video:** https://youtu.be/9RFP4sJX1Sg  


**December 2025**


## Why I Built This

Living in Texas, I've watched brush fires get out of control way too fast, especially during dry winters. 
One of the biggest challenges in wildfire management is slow response time. Fires can double in size every minute under the right conditions, yet it often takes hours for crews to reach remote or rugged areas. By the time firefighting teams arrive, thousands of acres may already be burning. In recent wildfires, delays in detection and deployment have led to the destruction of entire neighborhoods within a single day.

Things took a turn personally inside me when I saw California Palisades Jan 2025 fire creating huge devastation and human tragedy. I started thinking how can I build an exhaustive Fire Fighting System using swarm of specialized Drones to detect and suppress before they grow big.

That question turned into a few months of project in researching, finding possible approach, conceptualizing, whiteboarding ideas, CAD designing the drone and mechanisms, 3D printng, building each and every components of the drone, buying compatible hardware for drone flight, compute module and sensor electronics. It was a super learning and arduos journey of  integrating, home testing, field testing, calibrating in an iteration, gathering data, analyzing further modifying the design and finally making it work as a system.


## What I Actually Built

This isn't just a simulation or paper design - I built real hardware and flew it (when Texas weather cooperated  :).
It was a tremendous journey and I learned a lot about drone flight, compute module, networking, sensor  electronics, hardware integration, machine learning for fire detection and building a complex software system to manage swarm of drones and provide a consolidated dashboard to see it all in realtime.


## Hardware Used

### Electronics:
- **Flight Controller:** Pixhawk 2.4.8 32 Bit ARM Flight controller running ArduCopter 4.6.3 for managing the flight stability and flight modes instruction from Raspbery pi drone programs.
https://www.amazon.com/Controller-Wireless-Telemetry-Quadcopter-Multirotor/dp/B07NRMFTXL?
- **Companion Computer:** Raspberry Pi 4 (4GB) as main compute model running my Drone Code (python) and all integrations with onboard sensors and pixhawk, ground station controllers and backup RC controller. https://www.amazon.com/Raspberry-Model-2019-Quad-Bluetooth/dp/B07TC2BK1X
- **Drone ESC:** Readytosky 2-4S 40A Brushless ESC Electronic Speed Controller 5V/3A BEC for F450 450mm S500 ZD550 RC Helicopter Quadcopter(4PCS). https://www.amazon.com/dp/B09G5S9YYG
- **WiFi:** TP-Link AC600 USB WiFi Adapter, Dual Band (2.4GHz and 5GHz), 5dBi High gain antenna, Dual Band, wanted more than 200 ft ft+ range compared to built-in wifi on Raspberry pi.https://www.amazon.com/dp/B07P5PRK7J
- **Power distribution board:** Acxico 2 pcs Drone Power Distribution Board XT60 3-4S 9-18V 5V 12V Output PDB. https://www.amazon.com/Acxico-Drone-Power-Distribution-Output/dp/B0B2PF6YPQ     
- **Flight Transmitter:** Flysky FS-i6X 6-10(Default 6)CH 2.4GHz AFHDS RC Transmitter w/ FS-iA6B Receiver. https://www.amazon.com/Flysky-FS-i6X-Transmitter-FS-iA6B-Receiver/dp/B0744DPPL8

### Sensors:
- **Thermal Camera:** MLX90640 (32x24 pixels, 110° FOV) for capturing thermal image at ~50ft. Taking pics every 1 second (configurable) + periodic video (full HD format) and streaming on demand during field testing. https://www.amazon.com/dp/B0FQJDLBFC
- **Temperature and Humidity Sensor:** SHILLEHTEK DHT22 Digital Temperature and Humidity Sensor for capturing temperature and humidity at ~50ft. https://www.amazon.com/SHILLEHTEK-Digital-Temperature-Humidity-Sensor/dp/B0CN5PN225
- **Visual Camera:** Arducam IMX708 Autofocus Pi Camera V3 120°(D) for fire detection still confirmation shots + intermediate videos/streaming on demand during testing. https://www.amazon.com/dp/B0C5D97DRJ
- **GPS Module:** NEO-M8N GPS Module. https://www.amazon.com/QWinOut-Mini-Module-NEO-M8N-PIXHAWK-Controller/dp/B01FXKQY1A


### Drone:
- **Drone Frame:** Custom designed from scracth and 3D printed. Arms, Stand, Body Modules (2 layers), Electronics Bay, Shock pad, Camera Enclosure and Swivel Mounts
- **Drone Motors:** CW Emax Mt2213 935kv 2212 Brushless Motor CW for F450 X525 Quadcopter Hexcopter. https://www.amazon.com/Hobbypower-Mt2213-Brushless-Quadcopter-Hexcopter/dp/B00EDHXZSK
- **Drone Propellers:** QWinOut 3k Carbon Fiber Propeller Cw CCW 1045. amazon.com/QWinOut-Carbon-Propeller-Quadcopter-Hexacopter/dp/B08132CJFT
- **Battery:** Zeee 4S Lipo Battery 14.8V 5200mAh 100C with EC5 Plug (~ 12-15 min flight time at peak performance, less in cold weather as most of my testing happened in Oct, Nov, Dec 2025). https://www.amazon.com/Zeee-Battery-Quadcopter-Airplane-Helicopter/dp/B093DG3W3C
- **Battery Charger:** IMAX B6 80W Lipo Battery Balance Charger 6A Discharger. https://www.amazon.com/Havcybin-Battery-Balance-Discharger-Batteries/dp/B093P2L2XC

### Design and Build Tools:
- **CAD:** Onshape. https://www.onshape.com/
- **3D Printer:** Bambu Lab - P1S Combo 3D Printer. https://us.store.bambulab.com/products/p1s?srsltid=AfmBOop0QcUaoLAecaGk9fMSnUuecMRg3kze8IqRhrdfz1jMpUOwoGPU
- **3D Printer Filament:** PETG for Drone Arms and Stand, PLA for Electronics Bay, Shock Pad and Camera Enclosure and Swivel Mounts

    **Overall Drone Build Cost:** ~ `$950`, excludding 3D Printer.

## Software Tech Stack and Tools

### Tech Stack
- Python 3.13 (had to patch DroneKit to work - more on that below). Will face some compatibility issues with latest version of DroneKit and few packages. Use requirements.txt for packages and will not face any issues. Make sure you Python virtual environment and requirements.txt is activated. Also use my fix_dronekit_py313.py script to patch DroneKit for Python 3.13 compatibility.
- DroneKit for Pixhawk communication via MAVLink
- OpenCV for image processing
- Custom thermal analysis algorithms
- SQLite for mission/detection logging
- Dash for real-time dashboard
- Other opensource mentioned in requirements.txt

**For detail version use `requirements.txt` at the project root** 


### Tools/Framework Used

| Category | Tool | Description |
|------------------------|------------------------|-------------|
|- **IDE** | Visual Studio Code | IDE for development and debugging
|- **Version Control**| Git and Github | Version control for source code and documentation
|- **AI usage**| Claude.ai |for getting help in sensor adapter packages and integration, networking research and machine learning model training
|- **ML Model**| Tensorflow Lite | for ML model for fire detection system and Keras for training
|- **ML Training Datasets** | Kaggle.com | Trained on my custom dataset of fire and non fire images based on drone images captured in field testing. For larger Ground Control Station (GCS) and Drone, I used Kaggle dataset. https://www.kaggle.com/datasets/phylake1337/fire-dataset as its light weight with 1000 images and overall built model is < 50mb to be processed on edge on my drone.
|- **Data Storage** | SQLite |for mission/detection and logging persistence and all state management and orchestration between drones
|- **Dashboard** | Python Dash package |for real-time dashboard for ground station to monitor the mission and control the drones.


## Project Architecture
Please refer to `ARCHITECTURE.md` for project architecture details.
For quickly setting up the project, please refer to `QUICKSTART.md`. 
For detail validation, testing, simulation and run, please refer to `OPERATIONS.md`.
For field test data/analysis and sample results, please refer to `FIELD_TEST.md`.

## Features Built for this Project

| Feature | Description |
|---------|-------------|
| **Drone Fire Fighting System** | Complete system capable of working with configurable number of SD (Scout Drones) and FD (Fire Drones), Area of operation Flight Configuration, Electronics/Sensor Configuration, Mode of operation from Validation, Test, Simulation, Hardware (test) to full production mode. |
| **Autonomous Flight** | Pre-programmed waypoint missions with every aspect configurable. See `dfs_config.yaml`, `mission_area.yaml` for more details. |
| **Fire Detection** | Thermal + visual confirmation (ML model trained on Kaggle dataset) |
| **Mission Planning** | Generate search patterns (serpentine) based on area size. During my research figured serpentine is the most effective way to cover a larger area for scouting. |
| **Data Logging** | GPS, thermal, environmental data in standard formats. |
| **Swarm Simulation** | Multi-drone coordination. This was heart of me building this Ground Station control, building the Drone Swarm Network and Ground Station to Drone communication. Though I built a single drone, the system scales for any number of drones. So to visualize I built the complete system, various type of simulation as single operation, batch operation, fire injection to see how it will all work together. The code is a production ready code where one can add drones, configure the IPs and do some basic integration testing to fly all in a mission. This was a very ambitious goal and I am extremely proud of it. |
| **Drone Fire Fighting System - Mission Control** | Real-time dashboard to monitor the mission and control the drones. This is where you can see the visualization of drone as they fly for different missions set through configuration files `dfs_config.yaml`, `mission_area.yaml`. |


## Process I followed

This project went through several iterations:

**Stage 0 (Q1/2025):** Identification of problem, California Jan 2025 Palisades wildfires    
**Stage 1 (Q2 2025):** Conceptualization, Research, Built CAD model, showcased in my PCIS (Prosper Career Independent Study) and to my mentors. Till this point I was not committed to build a field drone and real system. I built a Python Visual Simulation model how it will work but no idea how to build a real system. 
https://www.anshulojha.com/pcis
https://www.anshulojha.com/dp
https://youtu.be/oCuLS8m1QiQ
 
**Stage 2 (Sep 2025):** Felt strong desire to build, brainstormed, white boarded, identified components and areas to focus. Still not sure whether I will ONLY build the drone from scratch with sensors or will move forward with complete system with fire detection, field testing and data collection.

**Stage 3 (Oct 2025):** Got the 3D Printer in the summer after some convincing with my parents. Started getting parts and electronics. Went through numerous iteration of CAD design for components, part breakage during minor and major crashes, rectifying designs. Extensive research on elctronics, compatibility, limits, software adapters. Still things are pretty meshy and not fully integrated.

**Stage 4 (Nov 2025):** Lot of effort went in creating Test bed on my study table, Test Harness in my backyard, Simulating Fire which is safe to do without violating local laws and regulations. A portable module which I can keep it near my desk and do hardware and sensor test without spending lot of time in assembling onto drone and weight for right weather with low windspeed < 5-10 mph.

**Stage 5 (final) (Dec 2025):** Lot of field testing, discovered all the "real world" problems and rectified them. Built the complete software system to manage swarm of drones. Various visualization utility to see the thermal, gps, temp and flight data.


## My Setup

### Test Setup
- **Location:** 
    - Inital Testing mostly sensors, integration, coding, simulation at my study desk
    - Flight calibration, flight worthy and sensor tests in my backyard. I invented my own flight harness system to hold the drone max at 6 ft height to test the flight calibration, lift, power, etc.
    - Actual flight tests happened field near my community in Prosper, TX, 75078, https://maps.app.goo.gl/su4V1r5PobqoLV4S7. After lot of tries, finally used a gas can to create a fire and flew the drone at 30-50 ft altitude. Use color bed sheet for visual confirmation of fire since I had no land with grass or vegetation to use as reference. It was a barren tilled land and very safe for my testing.

- **Test Dates:** Oct, Nov, Dec 2025  
- **Weather Conditions:** 35-45°F, < 10 mph winds (when I could actually fly)  
- **Test Method:** GasOne Diethylene 6 Hour Wick Liquid Gel Fuel Can, flew at 30-50 ft altitude
- **Why heated gravel stone did not work?**  
Can't exactly start real fires in a public field. Heated gravel in my oven to 180°F (82°C), spread it out, and the thermal camera picked it up perfectly from 50 feet. But while taking it in a insulated case it dropped temp pretty fast in open field and I was testing in cold weather. So used food warmer spirit can and had fire extinguiser for safety. It was tested in a isolated, no grass, land with no dry grass or vegetation near by. 


## Key Highlights

- **Testing Ability :** Code is refactored to include various toggle and config to allow to test in pure test/validation, simulation without hardware integrated, with h/w integrated with no flight and with actual flight when env and time permits. This was built iteratively as the situation demanded where I could do one vs others and I am extremeley proud of

- **Base System Solidly Built :** Base foundation is built where anyone can fork my code or download, with minimal config changes can make it operational so your focus is on testing and data gathered

- **Networking :** Situation forced me to think and built "network as a code" where I often faced issues with no network or signal. System is capable of building a Swarm Network on Raspberry pi and Drone using WiFi and TCP/IP + can use built in WiFi on Raspberry pi to connect to Ground Control Station (GCS). In Future one can use Lora or other high bandwith communication to connect to GCS even using data card for direct internet access.

- **Edge Computing (raspberry pi) :** Drone program will run as service post reboot and can also be triggered over network. The data gets stored locally and can be transmitted over TCP/IP as well as UDP (for streaming) to Ground Control Station.



## Things That Went Wrong (And How I Fixed Them)

- ### The DroneKit Python 3.13 Disaster
    Upgraded to Python 3.13 and DroneKit immediately broke. Error: `collections.MutableMapping` doesn't exist anymore (moved in Python 3.11+). Spent half a day debugging before writing a patch script (`fix_dronekit_py313.py`) to fix it automatically.
- **Solution:** Monkey-patch the library on import. Not pretty, but works.

- ### WiFi Range Was Terrible
    Pi's built-in WiFi? Maybe 50-100 feet on a good day. Tried the ALFA AWUS036ACH (everyone recommends it) but it weighs 250 grams - too heavy for my frame.
- **Solution:** Found TP-Link AC600 adapters. much lighter, 200+ foot range. Game changer.

- ### Cold Weather Battery Death
    Texas winters aren't that cold (35-45°F) but LiPo batteries HATE it. Lost 30% capacity just from temperature. Flight time dropped from 15 min to 10 min.
- **Solution:** Keep batteries inside my jacket until flight time. Also learned to set voltage alarm higher (3.8V vs 3.7V per cell).

- ### GPS Drift Is Annoying
    Even with 12+ satellites, GPS position bounces around ±2 feet constantly. Makes it hard to return to exact locations for repeat measurements.
- **Solution:** Average position over 10 readings. Also added GPS smoothing in post-processing.

- ### MLX90640 Quirks
    Thermal camera randomly glitches if you read too fast. Needs minimum 2 seconds between frames or data gets corrupted.
- **Solution:** Set refresh rate to 8Hz max. Also added error handling to skip bad frames.

- ### Wind Is The Enemy
    Can't fly in winds over 15 mph with my setup. Drone becomes unstable and thermal footage is unusable (too much vibration).
- **Solution:** Check weather forecast. Only fly on calm days. Lost several weekends to this.

## Key Challenges and Learnings

- ### Drone Weight:
    Overall weight increased due to non carbon fiber frame, not so great battery and stand and guard weight to protect propellers as can not afford to break frequently during flight tests and safety. This reduced overall flight time.

- ### 3D Print Limitations:
    PETG and PLA are not as durable as Carbon Fiber and can break.

- ### Unpredictability of Flight Controller Loitter mode:
    Had a crash due to unreliable GPS and EKS reset mid flight. So programmable flight should be used with lot of caution, manual overide and open space for flight.

- ### Sensor Limitations:
    Since I was using relatively not so expensive sensors, they had limits of accuracy and range. Also I never achieved higher frequency like 16, 30 or 60HZ for smoother thermal image as my HW and Sensors were erroring out

- ### Flight Controller:
    One need to really master Flight Controller and its settings to safely operate under programmable flight mode. Its really hard than sounds. Requires lot of trial and testing as every drone built is different in its weight, shape, propellers, motors, battery, ESC, so calibration and limit settings are very important.

- ### Weather and environment:
    Had lot of delay due to TX weather conditions - wind gusts over > 20+ mph. Flight path was shaking un reliable and camera autofocus was bad. So having a gymbal mount would be good if you have budget and weight to spare.

- ### Machine Learning:
    ML Training publicly available data was on actual forrest fire. Since my testing was in open field with no grass or vegetation, so it was not able to detect fire. I had to build a custom dataset of fire and non fire images based on drone images captured in field testing.

- ### Testing (Really important and one of my greatest learnings !!!):
    You have to be creative here. I realized I need to pack all sensors with PxiHawk and Raspberry pi into a small portable unit for writing code, deploying and software trigger, testing side by side with my mac on my desktop. Also easy enough to hand held and carry to the backyard for testing, sensor study, calibration. I used a small styrofoam block and paper tape to bind them together with small portable power bank. So I always had the complete gadgets with out the drone for writing software and testing. This helped me speed up things and identify issues than integrating with in drone which I can only do on weekends or early school dismissals days (which is very few)


## Future Improvements (If I Had More Time/Money)

1. **Better Drone Build Material:** Build on carbon fibre to reduce weight
1. **Better GPS Module:** To avoid GPS dropouts, Loitter mode issues and unpredictable flight behavior
2. **Gimbal:** Even a cheap 2-axis gimbal would make footage way clearer
1. **Better Thermal Camera:** MLX90641 (192×144) instead of MLX90640 (32×24) - $200 vs $60
3. **Better Battery:** Better Capacity to weight ratio with 4S, may be will give me additional flight time
4. **Multiple Drones:** I could afford to build 1 Drone, but swarm will be cooler to see few in action
5. **LoRa Telemetry:** ESP32+ Lora - More reliable than WiFi for long-range


## What I wanted to see in this field
1. **Research** on type of portable fire extinuisher and methods to address spot and small forest fire based on local conditions, size, effectiveness and weight/design considerations**
2. **Ground Station Machine Learning model** refinement based on better detection model publicly available, better training datasets.**
3. **Data Science/ML Model** How Ground Station can use past weather data, forecasts and local fire data to plan effective scout mission for effective coverage and optimization of resources
4. **Advance Design** I have a conceptual model and draft built of a CAD model how a Un Manned Ground Station POD will look like in remote region where a Truck Trailer will place it and it has all the necessary components open, expand, charge and unlesh SD and FD drones and do the whole operation with remote management from centralized unit somewhere from the city.


## Resources I Used

- **DroneKit Documentation:** For MAVLink protocol. https://dronekit-python.readthedocs.io/en/latest/guide/mavlink_messages.html
- **ArduPilot Wiki:** Flight controller setup. https://ardupilot.org/copter/docs/initial-setup.html
- **Stack Overflow:** Probably 50+ questions
- **YouTube - Painless360:** Pixhawk setup tutorials. https://www.youtube.com/watch?v=uH2iCRA9G7k&list=PLYsWjANuAm4r4idFZY24pP6s1K6ABMU0p
- **Adafruit MLX90640 Guide:** Thermal camera integration. https://learn.adafruit.com/adafruit-mlx90640-ir-thermal-camera/arduino-thermal-camera
- **Kaggle Fire Dataset:** ML model training data. https://www.kaggle.com/datasets/phylake1337/fire-dataset
- **GitHub - aircrack-ng/rtl8812au:** WiFi driver. https://github.com/aircrack-ng/rtl8812au
- **Copilot and Claude - Haversine Formula:** GPS distance calculations. https://copilot.github.com/

For Simulation, I had to generate data related GPS Noise Simulation, Winddrift Effects, Navigation, Environment, Thermal, Fire, FOV (field of view). So I used Claude.ai and Copilot to help me with the code samples and data generation.

|Formula Category |Primary Source/Reference (Claude/Copilot)|
|---|---|
|Haversine Formula|Standard geodetic formula;|
|Bearing Calculation|Spherical trigonometry|
|FOV Ground Coverage|Geometric optics, similar triangles|
|Barometric Altitude|International Standard Atmosphere (ISA) model|
|GPS Error Modeling|Gaussian distribution for GPS noise simulation|
|Heat Distribution|Gaussian/exponential decay models for thermal physics|
|Atmospheric Pressure|Hydrostatic pressure gradient (~12 Pa/m)|
|Coordinate Transformations|Standard geodetic and rotation matrix mathematics|
|Flight Dynamics|Basic kinematics (distance = speed × time)|

## Acknowledgments

Thanks to:
- The ArduPilot community for flight controller help
- Adafruit for great sensor documentation
- GitHub user morrownr for WiFi driver patches
- Everyone on Stack Overflow who answered my questions
- My parents for funding and letting me buy hardware, electronics. Helped me in doing field testing and supporting throughout.

## License

Apache License 2.0 - See `LICENSE` file for details.

This license provides patent protection for the fire detection algorithms and 
mission planning methods. You can use, modify, and distribute this code, 
including commercially, as long as you include the license and `NOTICE` file.

## Contact

**Anshul Ojha**  
Email: anshulojha2018@gmail.com  
GitHub: [@anshulojha613](https://github.com/anshulojha613)

---

**December 2025**

*This project spanned over two qtrs in 2025 with most of the final build and testing in Oct, Nov, Dec 2025. It represents if you put your mind and passion, you can build something amazing. It's not perfect but its my own which I am proud of. Would love to get your comments when you try out.*
