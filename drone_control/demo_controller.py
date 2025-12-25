"""
Demo Drone Controller
Simulated drone controller for testing and demonstration without hardware
"""

from .base_controller import DroneControllerBase, FlightMode
from typing import List, Dict, Tuple
import time
import random
import math


class DemoController(DroneControllerBase):
    """Simulated drone controller for demo/testing"""
    
    def __init__(self, drone_id: str, config: Dict = None):
        """
        Initialize demo controller
        """
        self.drone_id = drone_id
        self.config = config or {}
        
        # Connection state
        self.connected = False
        self.armed = False
        self.mode = FlightMode.IDLE
        
        # Position state (lat, lon, alt)
        self.position = (0.0, 0.0, 0.0)
        self.speed = 0.0
        self.heading = 0.0
        
        # Battery state
        self.battery = 100.0
        self.battery_drain_rate = self.config.get('battery_drain_rate', 0.1)
        
        # Mission state
        self.mission_waypoints = []
        self.current_waypoint_index = 0
        
        # Simulation settings
        self.simulate_delays = self.config.get('simulate_delays', True)
        self.gps_noise = self.config.get('gps_noise_meters', 0.5)
        
    def connect(self) -> bool:
        """Connect to simulated drone"""
        print(f"[DEMO] {self.drone_id}: Simulating connection...")
        if self.simulate_delays:
            time.sleep(0.5)
        self.connected = True
        print(f"[DEMO] {self.drone_id}: Connected (simulated)")
        return True
    
    def disconnect(self):
        """Disconnect from simulated drone"""
        print(f"[DEMO] {self.drone_id}: Disconnecting (simulated)")
        self.connected = False
        self.armed = False
        self.mode = FlightMode.IDLE
    
    def arm(self) -> bool:
        """Arm simulated drone"""
        if not self.connected:
            print(f"[DEMO] {self.drone_id}: Cannot arm - not connected")
            return False
        
        print(f"[DEMO] {self.drone_id}: Arming motors (simulated)")
        if self.simulate_delays:
            time.sleep(0.5)
        self.armed = True
        print(f"[DEMO] {self.drone_id}: Motors armed")
        return True
    
    def disarm(self) -> bool:
        """Disarm simulated drone"""
        print(f"[DEMO] {self.drone_id}: Disarming motors (simulated)")
        self.armed = False
        return True
    
    def takeoff(self, altitude_m: float) -> bool:
        """Simulate takeoff"""
        if not self.armed:
            print(f"[DEMO] {self.drone_id}: Cannot takeoff - not armed")
            return False
        
        print(f"[DEMO] {self.drone_id}: Taking off to {altitude_m}m (simulated)")
        if self.simulate_delays:
            time.sleep(1.0)
        
        lat, lon, _ = self.position
        self.position = (lat, lon, altitude_m)
        self.mode = FlightMode.GUIDED
        self.battery -= 1.0  # Takeoff uses battery
        
        print(f"[DEMO] {self.drone_id}: Reached altitude {altitude_m}m")
        return True
    
    def land(self) -> bool:
        """Simulate landing"""
        print(f"[DEMO] {self.drone_id}: Landing (simulated)")
        if self.simulate_delays:
            time.sleep(1.0)
        
        lat, lon, _ = self.position
        self.position = (lat, lon, 0.0)
        self.mode = FlightMode.LAND
        self.speed = 0.0
        
        print(f"[DEMO] {self.drone_id}: Landed")
        return True
    
    def upload_mission(self, waypoints: List[Dict]) -> bool:
        """Upload simulated mission"""
        print(f"[DEMO] {self.drone_id}: Uploading {len(waypoints)} waypoints (simulated)")
        self.mission_waypoints = waypoints
        self.current_waypoint_index = 0
        print(f"[DEMO] {self.drone_id}: Mission uploaded")
        return True
    
    def start_mission(self) -> bool:
        """Start simulated mission"""
        if not self.mission_waypoints:
            print(f"[DEMO] {self.drone_id}: No mission to start")
            return False
        
        print(f"[DEMO] {self.drone_id}: Starting mission with {len(self.mission_waypoints)} waypoints (simulated)")
        self.mode = FlightMode.AUTO
        self.current_waypoint_index = 0
        return True
    
    def goto_waypoint(self, lat: float, lon: float, alt: float) -> bool:
        """Simulate going to waypoint"""
        if not self.armed:
            print(f"[DEMO] {self.drone_id}: Cannot goto waypoint - not armed")
            return False
        
        # Calculate distance for simulation
        current_lat, current_lon, current_alt = self.position
        distance = self._calculate_distance(current_lat, current_lon, lat, lon)
        
        # Simulate movement delay based on distance
        if self.simulate_delays and distance > 0:
            delay = min(distance / 10.0, 0.5)  # Max 0.5s delay
            time.sleep(delay)
        
        # Add GPS noise
        noise_lat = random.uniform(-self.gps_noise / 111000, self.gps_noise / 111000)
        noise_lon = random.uniform(-self.gps_noise / 111000, self.gps_noise / 111000)
        
        self.position = (lat + noise_lat, lon + noise_lon, alt)
        self.battery -= self.battery_drain_rate
        
        # Update speed and heading
        self.speed = 5.0  # Simulated cruise speed
        self.heading = self._calculate_heading(current_lat, current_lon, lat, lon)
        
        return True
    
    def get_position(self) -> Tuple[float, float, float]:
        """Get simulated position"""
        return self.position
    
    def get_battery(self) -> float:
        """Get simulated battery level"""
        return max(0.0, min(100.0, self.battery))
    
    def get_mode(self) -> FlightMode:
        """Get current flight mode"""
        return self.mode
    
    def set_mode(self, mode: FlightMode) -> bool:
        """Set flight mode"""
        print(f"[DEMO] {self.drone_id}: Setting mode to {mode.value} (simulated)")
        self.mode = mode
        return True
    
    def is_armed(self) -> bool:
        """Check if armed"""
        return self.armed
    
    def is_connected(self) -> bool:
        """Check if connected"""
        return self.connected
    
    def get_speed(self) -> float:
        """Get current speed"""
        return self.speed
    
    def get_heading(self) -> float:
        """Get current heading"""
        return self.heading
    
    def emergency_stop(self):
        """Simulate emergency stop"""
        print(f"[DEMO] {self.drone_id}: EMERGENCY STOP - RTL (simulated)")
        self.mode = FlightMode.RTL
        self.speed = 0.0
    
    def wait_for_altitude(self, target_altitude: float, timeout: float = 30.0) -> bool:
        """Simulate waiting for altitude"""
        _, _, current_alt = self.position
        if abs(current_alt - target_altitude) < 0.5:
            return True
        
        print(f"[DEMO] {self.drone_id}: Waiting for altitude {target_altitude}m (simulated)")
        if self.simulate_delays:
            time.sleep(0.5)
        return True
    
    def wait_for_waypoint(self, timeout: float = 60.0) -> bool:
        """Simulate waiting for waypoint"""
        if self.simulate_delays:
            time.sleep(0.1)
        return True
    
    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two GPS coordinates in meters"""
        # Haversine formula
        R = 6371000  # Earth radius in meters
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        
        a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return R * c
    
    def _calculate_heading(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate heading between two GPS coordinates in degrees"""
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        dlon = math.radians(lon2 - lon1)
        
        y = math.sin(dlon) * math.cos(lat2_rad)
        x = math.cos(lat1_rad) * math.sin(lat2_rad) - math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(dlon)
        
        heading = math.degrees(math.atan2(y, x))
        return (heading + 360) % 360
    
    def set_home_position(self, lat: float, lon: float, alt: float):
        """Set home position for simulated drone"""
        print(f"[DEMO] {self.drone_id}: Setting home position to ({lat:.6f}, {lon:.6f}, {alt}m)")
        self.position = (lat, lon, 0.0)  # Start on ground
    
    def get_mission_progress(self) -> Tuple[int, int]:
        """
        Get mission progress
        """
        return (self.current_waypoint_index, len(self.mission_waypoints))
