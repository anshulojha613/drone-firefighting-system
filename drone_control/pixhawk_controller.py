"""
Pixhawk Drone Controller
Real hardware controller using MAVLink/DroneKit for Pixhawk flight controllers
"""

from .base_controller import DroneControllerBase, FlightMode
from typing import List, Dict, Tuple
import os
import glob
import time

# Try to import dronekit - it's optional for demo mode
try:
    from dronekit import connect, VehicleMode, LocationGlobalRelative, Command
    from pymavlink import mavutil
    DRONEKIT_AVAILABLE = True
except ImportError:
    DRONEKIT_AVAILABLE = False
    print("WARNING: dronekit not installed. Hardware mode unavailable.")
    print("Install with: pip install dronekit pymavlink")


class PixhawkController(DroneControllerBase):
    """Real Pixhawk flight controller via MAVLink"""
    
    def __init__(self, drone_id: str, connection_string: str = '/dev/ttyACM0', baud: int = 57600):
        """
        Initialize Pixhawk controller
        """
        if not DRONEKIT_AVAILABLE:
            raise ImportError("dronekit is required for hardware mode. Install: pip install dronekit pymavlink")
        
        self.drone_id = drone_id
        self.connection_string = connection_string
        self.baud = baud
        self.vehicle = None
        
    def connect(self) -> bool:
        """Connect to Pixhawk via MAVLink"""
        try:
            print(f"[HARDWARE] {self.drone_id}: Connecting to Pixhawk at {self.connection_string}...")

            if (
                isinstance(self.connection_string, str)
                and self.connection_string.startswith("/dev/")
                and not os.path.exists(self.connection_string)
            ):
                candidates = []
                for pattern in (
                    "/dev/serial*",
                    "/dev/ttyAMA*",
                    "/dev/ttyACM*",
                    "/dev/ttyUSB*",
                ):
                    candidates.extend(sorted(glob.glob(pattern)))

                print(
                    f"[HARDWARE] {self.drone_id}: Connection failed: device does not exist: {self.connection_string}"
                )
                if candidates:
                    print(f"[HARDWARE] {self.drone_id}: Available serial candidates:")
                    for c in candidates:
                        print(f"[HARDWARE]   - {c}")
                else:
                    print(
                        f"[HARDWARE] {self.drone_id}: No serial devices found under /dev/serial*, /dev/ttyAMA*, /dev/ttyACM*, /dev/ttyUSB*"
                    )
                return False

            self.vehicle = connect(self.connection_string, baud=self.baud, wait_ready=True, timeout=30)
            
            print(f"[HARDWARE] {self.drone_id}: Connected to Pixhawk")
            print(f"[HARDWARE] Autopilot: {self.vehicle.version}")
            print(f"[HARDWARE] GPS: {self.vehicle.gps_0}")
            print(f"[HARDWARE] Battery: {self.vehicle.battery}")
            
            return True
        except Exception as e:
            print(f"[HARDWARE] {self.drone_id}: Connection failed: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from Pixhawk"""
        if self.vehicle:
            print(f"[HARDWARE] {self.drone_id}: Disconnecting from Pixhawk")
            self.vehicle.close()
            self.vehicle = None
    
    def arm(self) -> bool:
        """Arm the drone motors"""
        if not self.vehicle:
            print(f"[HARDWARE] {self.drone_id}: Cannot arm - not connected")
            return False
        
        print(f"[HARDWARE] {self.drone_id}: Arming motors...")
        self.vehicle.mode = VehicleMode("GUIDED")
        self.vehicle.armed = True
        
        # Wait for arming
        timeout = 10
        start = time.time()
        while not self.vehicle.armed and (time.time() - start) < timeout:
            print(f"[HARDWARE] {self.drone_id}: Waiting for arming...")
            time.sleep(1)
        
        if self.vehicle.armed:
            print(f"[HARDWARE] {self.drone_id}: Motors armed")
            return True
        else:
            print(f"[HARDWARE] {self.drone_id}: Arming failed")
            return False
    
    def disarm(self) -> bool:
        """Disarm the drone motors"""
        if not self.vehicle:
            return False
        
        print(f"[HARDWARE] {self.drone_id}: Disarming motors...")
        self.vehicle.armed = False
        time.sleep(1)
        return not self.vehicle.armed
    
    def takeoff(self, altitude_m: float) -> bool:
        """Takeoff to specified altitude"""
        if not self.vehicle or not self.vehicle.armed:
            print(f"[HARDWARE] {self.drone_id}: Cannot takeoff - not armed")
            return False
        
        print(f"[HARDWARE] {self.drone_id}: Taking off to {altitude_m}m...")
        self.vehicle.simple_takeoff(altitude_m)
        
        # Wait for altitude
        while True:
            current_alt = self.vehicle.location.global_relative_frame.alt
            print(f"[HARDWARE] {self.drone_id}: Altitude: {current_alt:.1f}m")
            
            if current_alt >= altitude_m * 0.95:
                print(f"[HARDWARE] {self.drone_id}: Reached target altitude")
                break
            time.sleep(1)
        
        return True
    
    def land(self) -> bool:
        """Land the drone"""
        if not self.vehicle:
            return False
        
        print(f"[HARDWARE] {self.drone_id}: Landing...")
        self.vehicle.mode = VehicleMode("LAND")
        return True
    
    def upload_mission(self, waypoints: List[Dict]) -> bool:
        """Upload waypoint mission to Pixhawk"""
        if not self.vehicle:
            print(f"[HARDWARE] {self.drone_id}: Cannot upload mission - not connected")
            return False
        
        print(f"[HARDWARE] {self.drone_id}: Uploading {len(waypoints)} waypoints...")
        
        # Clear existing mission
        cmds = self.vehicle.commands
        cmds.clear()
        
        # Add waypoints
        for i, wp in enumerate(waypoints):
            cmd = Command(
                0, 0, 0,
                mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT,
                mavutil.mavlink.MAV_CMD_NAV_WAYPOINT,
                0, 0, 0, 0, 0, 0,
                wp['lat'], wp['lon'], wp.get('alt', 50.0)
            )
            cmds.add(cmd)
            
        # Upload
        cmds.upload()
        print(f"[HARDWARE] {self.drone_id}: Mission uploaded OK")
        return True
    
    def start_mission(self) -> bool:
        """Start executing uploaded mission"""
        if not self.vehicle:
            return False
        
        print(f"[HARDWARE] {self.drone_id}: Starting mission...")
        self.vehicle.mode = VehicleMode("AUTO")
        return True
    
    def goto_waypoint(self, lat: float, lon: float, alt: float) -> bool:
        """Go to specific waypoint in GUIDED mode"""
        if not self.vehicle:
            return False
        
        print(f"[HARDWARE] {self.drone_id}: Going to ({lat:.6f}, {lon:.6f}, {alt}m)")
        location = LocationGlobalRelative(lat, lon, alt)
        self.vehicle.simple_goto(location)
        return True
    
    def get_position(self) -> Tuple[float, float, float]:
        """Get current GPS position"""
        if not self.vehicle:
            return (0.0, 0.0, 0.0)
        
        loc = self.vehicle.location.global_relative_frame
        return (loc.lat, loc.lon, loc.alt)
    
    def get_battery(self) -> float:
        """Get battery percentage"""
        if not self.vehicle or not self.vehicle.battery:
            return 0.0
        
        return self.vehicle.battery.level if self.vehicle.battery.level else 0.0
    
    def get_mode(self) -> FlightMode:
        """Get current flight mode"""
        if not self.vehicle:
            return FlightMode.IDLE
        
        mode_map = {
            "STABILIZE": FlightMode.IDLE,
            "GUIDED": FlightMode.GUIDED,
            "AUTO": FlightMode.AUTO,
            "RTL": FlightMode.RTL,
            "LAND": FlightMode.LAND
        }
        return mode_map.get(self.vehicle.mode.name, FlightMode.IDLE)
    
    def set_mode(self, mode: FlightMode) -> bool:
        """Set flight mode"""
        if not self.vehicle:
            return False
        
        mode_map = {
            FlightMode.GUIDED: "GUIDED",
            FlightMode.AUTO: "AUTO",
            FlightMode.RTL: "RTL",
            FlightMode.LAND: "LAND"
        }
        
        mavlink_mode = mode_map.get(mode)
        if mavlink_mode:
            print(f"[HARDWARE] {self.drone_id}: Setting mode to {mavlink_mode}")
            self.vehicle.mode = VehicleMode(mavlink_mode)
            return True
        return False
    
    def is_armed(self) -> bool:
        """Check if drone is armed"""
        return self.vehicle.armed if self.vehicle else False
    
    def is_connected(self) -> bool:
        """Check if drone is connected"""
        return self.vehicle is not None
    
    def get_speed(self) -> float:
        """Get current ground speed"""
        if not self.vehicle:
            return 0.0
        return self.vehicle.groundspeed if self.vehicle.groundspeed else 0.0
    
    def get_heading(self) -> float:
        """Get current heading"""
        if not self.vehicle:
            return 0.0
        return self.vehicle.heading if self.vehicle.heading else 0.0
    
    def emergency_stop(self):
        """Emergency stop - RTL"""
        if self.vehicle:
            print(f"[HARDWARE] {self.drone_id}: EMERGENCY - Returning to launch")
            self.vehicle.mode = VehicleMode("RTL")
    
    def wait_for_altitude(self, target_altitude: float, timeout: float = 30.0) -> bool:
        """Wait until drone reaches target altitude"""
        if not self.vehicle:
            return False
        
        start_time = time.time()
        while (time.time() - start_time) < timeout:
            current_alt = self.vehicle.location.global_relative_frame.alt
            if abs(current_alt - target_altitude) < 0.5:
                return True
            time.sleep(0.5)
        
        return False
    
    def wait_for_waypoint(self, timeout: float = 60.0) -> bool:
        """Wait until current waypoint is reached"""
        if not self.vehicle:
            return False
        
        start_time = time.time()
        while (time.time() - start_time) < timeout:
            # Check if waypoint reached (distance < 1m)
            nextwaypoint = self.vehicle.commands.next
            if nextwaypoint == 0:
                return True
            time.sleep(0.5)
        
        return False
