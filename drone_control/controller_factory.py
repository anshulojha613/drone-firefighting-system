"""
Controller Factory
Creates appropriate drone controller based on config
"""

from .base_controller import DroneControllerBase
from .demo_controller import DemoController
from .pixhawk_controller import PixhawkController
import yaml
import os


class ControllerFactory:
    """Factory to create appropriate drone controller based on config"""
    
    @staticmethod
    def create_controller(drone_id: str, config_path: str = 'config/dfs_config.yaml', mode_override: str = None) -> DroneControllerBase:
        """
        Create drone controller based on config
        """
        
        # Load config
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Get drone control config
        drone_control_config = config.get('drone_control', {})
        mode = mode_override if mode_override else drone_control_config.get('mode', 'demo')
        
        # Create appropriate controller based on mode
        if mode in ['demo', 'simulation']:
            print(f"[FACTORY] Creating DEMO controller for {drone_id}")
            demo_config = drone_control_config.get('demo', {})
            return DemoController(drone_id, demo_config)
        
        elif mode == 'hardware':
            print(f"[FACTORY] Creating HARDWARE controller for {drone_id}")
            hardware_config = drone_control_config.get('hardware', {})
            connection_string = hardware_config.get('connection_string', '/dev/ttyAMA0')
            baud = hardware_config.get('baud', 57600)
            return PixhawkController(drone_id, connection_string, baud)
        
        else:
            raise ValueError(f"Unknown drone control mode: {mode}. Use 'demo', 'simulation', or 'hardware'")
    
    @staticmethod
    def get_available_modes() -> list:
        """
        Get list of available controller modes
        """
        return ['demo', 'simulation', 'hardware']
    
    @staticmethod
    def is_hardware_available() -> bool:
        """
        Check if hardware mode is available (dronekit installed)
        """
        try:
            import dronekit
            import pymavlink
            return True
        except ImportError:
            return False
