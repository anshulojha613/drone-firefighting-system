"""
Base Drone Controller Interface
Abstract base class defining the interface for all drone controllers
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Tuple, Optional
from enum import Enum


class FlightMode(Enum):
    """Flight modes supported by the drone"""
    IDLE = "IDLE"
    TAKEOFF = "TAKEOFF"
    GUIDED = "GUIDED"
    AUTO = "AUTO"
    RTL = "RTL"
    LAND = "LAND"
    EMERGENCY = "EMERGENCY"


class DroneControllerBase(ABC):
    """Abstract base class for drone control"""
    
    @abstractmethod
    def connect(self) -> bool:
        """
        Connect to drone
        """
        pass
    
    @abstractmethod
    def disconnect(self):
        """Disconnect from drone"""
        pass
    
    @abstractmethod
    def arm(self) -> bool:
        """
        Arm the drone motors
        """
        pass
    
    @abstractmethod
    def disarm(self) -> bool:
        """
        Disarm the drone motors
        """
        pass
    
    @abstractmethod
    def takeoff(self, altitude_m: float) -> bool:
        """
        Takeoff to specified altitude
        """
        pass
    
    @abstractmethod
    def land(self) -> bool:
        """
        Land the drone
        """
        pass
    
    @abstractmethod
    def upload_mission(self, waypoints: List[Dict]) -> bool:
        """
        Upload waypoint mission to drone
        """
        pass
    
    @abstractmethod
    def start_mission(self) -> bool:
        """
        Start executing uploaded mission
        """
        pass
    
    @abstractmethod
    def goto_waypoint(self, lat: float, lon: float, alt: float) -> bool:
        """
        Go to specific waypoint in GUIDED mode
        """
        pass
    
    @abstractmethod
    def get_position(self) -> Tuple[float, float, float]:
        """
        Get current GPS position
        """
        pass
    
    @abstractmethod
    def get_battery(self) -> float:
        """
        Get battery percentage
        """
        pass
    
    @abstractmethod
    def get_mode(self) -> FlightMode:
        """
        Get current flight mode
        """
        pass
    
    @abstractmethod
    def set_mode(self, mode: FlightMode) -> bool:
        """
        Set flight mode
        """
        pass
    
    @abstractmethod
    def is_armed(self) -> bool:
        """
        Check if drone is armed
        """
        pass
    
    @abstractmethod
    def is_connected(self) -> bool:
        """
        Check if drone is connected
        """
        pass
    
    @abstractmethod
    def get_speed(self) -> float:
        """
        Get current ground speed
        """
        pass
    
    @abstractmethod
    def get_heading(self) -> float:
        """
        Get current heading
        """
        pass
    
    @abstractmethod
    def emergency_stop(self):
        """Emergency stop - RTL or immediate landing"""
        pass
    
    @abstractmethod
    def wait_for_altitude(self, target_altitude: float, timeout: float = 30.0) -> bool:
        """
        Wait until drone reaches target altitude
        """
        pass
    
    @abstractmethod
    def wait_for_waypoint(self, timeout: float = 60.0) -> bool:
        """
        Wait until current waypoint is reached
        """
        pass
