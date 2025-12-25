"""
Database Models for Drone Firefighting System
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Text, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

Base = declarative_base()


class DroneType(enum.Enum):
    SCOUTER = "SD"
    FIREFIGHTER = "FD"


class DroneState(enum.Enum):
    IDLE = "idle"
    CHARGING = "charging"
    ASSIGNED = "assigned"
    FLYING = "flying"
    RETURNING = "returning"
    MAINTENANCE = "maintenance"
    OFFLINE = "offline"


class TaskState(enum.Enum):
    CREATED = "created"
    ASSIGNED = "assigned"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    ARCHIVED = "archived"
    DELETED = "deleted"


class Drone(Base):
    """
    Drone model - tracks state, position, battery, capabilities
    
    TODO: Add maintenance schedule tracking
    TODO: Implement flight hour logging for maintenance
    TODO: Add last_seen timestamp for offline detection
    """
    __tablename__ = 'drones'
    
    id = Column(Integer, primary_key=True)
    drone_id = Column(String(50), unique=True, nullable=False)
    drone_type = Column(Enum(DroneType), nullable=False)
    state = Column(Enum(DroneState), default=DroneState.IDLE)
    
    # Battery info
    battery_percent = Column(Float, default=100.0)
    battery_capacity_mah = Column(Integer)
    
    # Flight capabilities
    max_flight_time_min = Column(Float)
    cruise_speed_ms = Column(Float)
    cruise_altitude_m = Column(Float)
    
    # Current position
    current_latitude = Column(Float)
    current_longitude = Column(Float)
    current_altitude = Column(Float)
    
    # Payload (for FD drones)
    payload_capacity_kg = Column(Float)
    payload_remaining_kg = Column(Float)
    
    # Operational stats
    total_flights = Column(Integer, default=0)
    total_flight_time_min = Column(Float, default=0.0)
    last_maintenance = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    tasks = relationship("Task", back_populates="drone")
    telemetry = relationship("Telemetry", back_populates="drone")


class Task(Base):
    """
    Mission task model
    
    TODO: Add estimated completion time
    TODO: Implement task dependencies (task B after task A)
    TODO: Add priority queue support
    """
    __tablename__ = 'tasks'
    
    id = Column(Integer, primary_key=True)
    task_id = Column(String(50), unique=True, nullable=False)
    task_type = Column(String(20))  # 'scout' or 'suppress'
    state = Column(Enum(TaskState), default=TaskState.CREATED)
    priority = Column(String(10), default='medium')
    
    # Flight area (rectangular A-B-C-D)
    corner_a_lat = Column(Float)
    corner_a_lon = Column(Float)
    corner_b_lat = Column(Float)
    corner_b_lon = Column(Float)
    corner_c_lat = Column(Float)
    corner_c_lon = Column(Float)
    corner_d_lat = Column(Float)
    corner_d_lon = Column(Float)
    
    # Flight params
    cruise_altitude_m = Column(Float)
    cruise_speed_ms = Column(Float)
    pattern = Column(String(20), default='serpentine')
    
    # Assignment
    drone_id = Column(Integer, ForeignKey('drones.id'))
    assigned_at = Column(DateTime)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    # Results
    hotspots_detected = Column(Integer, default=0)
    fires_suppressed = Column(Integer, default=0)
    data_path = Column(String(255))
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    notes = Column(Text)
    
    # Relationships
    drone = relationship("Drone", back_populates="tasks")
    detections = relationship("FireDetection", back_populates="task")


class FireDetection(Base):
    """
    Fire detection event model
    
    TODO: Add fire spread prediction
    TODO: Implement confidence decay over time
    TODO: Add weather data correlation
    """
    __tablename__ = 'fire_detections'
    
    id = Column(Integer, primary_key=True)
    detection_id = Column(String(50), unique=True, nullable=False)
    
    # Location
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    altitude = Column(Float)
    
    # Detection details
    temperature_c = Column(Float)
    confidence = Column(Float)
    detection_method = Column(String(20))  # 'thermal' or 'ml'
    
    # Associated task and drone
    task_id = Column(Integer, ForeignKey('tasks.id'))
    drone_id = Column(Integer, ForeignKey('drones.id'))
    
    # Status
    status = Column(String(20), default='detected')  # detected, dispatched, suppressed, false_alarm
    dispatched_fd_id = Column(Integer, ForeignKey('drones.id'))
    
    # Timestamps
    detected_at = Column(DateTime, default=datetime.utcnow)
    dispatched_at = Column(DateTime)
    suppressed_at = Column(DateTime)
    
    # Media
    thermal_image_path = Column(String(255))
    rgb_image_path = Column(String(255))
    
    # Relationships
    task = relationship("Task", back_populates="detections")


class Telemetry(Base):
    __tablename__ = 'telemetry'
    
    id = Column(Integer, primary_key=True)
    drone_id = Column(Integer, ForeignKey('drones.id'))
    task_id = Column(Integer, ForeignKey('tasks.id'))
    
    # GPS data
    timestamp = Column(DateTime, nullable=False)
    latitude = Column(Float)
    longitude = Column(Float)
    altitude = Column(Float)
    heading = Column(Float)
    
    # Status
    battery_percent = Column(Float)
    speed_ms = Column(Float)
    
    # Environment
    temperature_c = Column(Float)
    humidity_percent = Column(Float)
    pressure_hpa = Column(Float)
    
    # Relationships
    drone = relationship("Drone", back_populates="telemetry")


class SystemLog(Base):
    __tablename__ = 'system_logs'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    level = Column(String(10))  # INFO, WARNING, ERROR
    module = Column(String(50))
    message = Column(Text)
    details = Column(Text)
