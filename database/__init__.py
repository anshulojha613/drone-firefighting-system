"""
Database module for Drone Firefighting System
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from .models import Base, Drone, Task, FireDetection, Telemetry, SystemLog
from .models import DroneType, DroneState, TaskState
import yaml
import os

class DatabaseManager:
    def __init__(self, config_path='config/dfs_config.yaml'):
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        db_config = config['database']
        db_path = db_config['path']
        
        # Create database directory if it doesn't exist
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # Create engine
        self.engine = create_engine(
            f"sqlite:///{db_path}",
            echo=db_config.get('echo', False),
            pool_size=db_config.get('pool_size', 10)
        )
        
        # Create session factory
        session_factory = sessionmaker(bind=self.engine)
        self.Session = scoped_session(session_factory)
        
        # Create tables
        Base.metadata.create_all(self.engine)
    
    def get_session(self):
        return self.Session()
    
    def close_session(self, session):
        session.close()
    
    def init_drone_pool(self, config_path='config/dfs_config.yaml'):
        """Initialize drone pool from config"""
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        session = self.get_session()
        
        try:
            # Check if drones already exist
            existing_count = session.query(Drone).count()
            if existing_count > 0:
                print(f"Drone pool already initialized with {existing_count} drones")
                return
            
            # Create Scouter Drones
            sd_config = config['drone_pool']['scouter_drones']
            for i in range(1, sd_config['count'] + 1):
                drone = Drone(
                    drone_id=f"{sd_config['prefix']}-{i:03d}",
                    drone_type=DroneType.SCOUTER,
                    state=DroneState.IDLE,
                    battery_percent=100.0,
                    battery_capacity_mah=sd_config['battery_capacity_mah'],
                    max_flight_time_min=sd_config['max_flight_time_min'],
                    cruise_speed_ms=sd_config['cruise_speed_ms'],
                    cruise_altitude_m=sd_config['cruise_altitude_m'],
                    current_latitude=33.2271901,
                    current_longitude=-96.8252657,
                    current_altitude=0.0
                )
                session.add(drone)
            
            # Create Firefighter Drones
            fd_config = config['drone_pool']['firefighter_drones']
            for i in range(1, fd_config['count'] + 1):
                drone = Drone(
                    drone_id=f"{fd_config['prefix']}-{i:03d}",
                    drone_type=DroneType.FIREFIGHTER,
                    state=DroneState.IDLE,
                    battery_percent=100.0,
                    battery_capacity_mah=fd_config['battery_capacity_mah'],
                    max_flight_time_min=fd_config['max_flight_time_min'],
                    cruise_speed_ms=fd_config['cruise_speed_ms'],
                    cruise_altitude_m=fd_config['cruise_altitude_m'],
                    payload_capacity_kg=fd_config['payload_capacity_kg'],
                    payload_remaining_kg=fd_config['payload_capacity_kg'],
                    current_latitude=33.2271901,
                    current_longitude=-96.8252657,
                    current_altitude=0.0
                )
                session.add(drone)
            
            session.commit()
            print(f"Initialized {sd_config['count']} Scouter Drones and {fd_config['count']} Firefighter Drones")
            
        except Exception as e:
            session.rollback()
            print(f"Error initializing drone pool: {e}")
            raise
        finally:
            self.close_session(session)

__all__ = [
    'DatabaseManager',
    'Base',
    'Drone',
    'Task',
    'FireDetection',
    'Telemetry',
    'SystemLog',
    'DroneType',
    'DroneState',
    'TaskState'
]
