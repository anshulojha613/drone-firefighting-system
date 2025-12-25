"""
Ground Station Network Client
Sends commands to drones and receives telemetry/alerts
"""

import requests
import json
from typing import Dict, Optional, List
from datetime import datetime
import time
import threading

from network.protocol import (
    Message, MessageType, 
    MissionAssignMessage, StatusReportMessage,
    RTLCommandMessage, HeartbeatMessage
)


class GroundStationClient:
    """
    Ground station network client for communicating with drones
    """
    
    def __init__(self, config: Dict):
        self.config = config
        self.network_config = config['network']
        self.timeout = self.network_config['timeout_sec']
        
        # Drone connections
        self.drones = {}  # drone_id -> {'ip': str, 'port': int, 'last_seen': datetime}
        
        # Heartbeat monitoring
        self.heartbeat_thread = None
        self.running = False
        
        print("[COMM] Ground Station Client initialized")
    
    def register_drone(self, drone_id: str, ip: str, port: int = 5000):
        """
        Register a drone for communication
        """
        self.drones[drone_id] = {
            'ip': ip,
            'port': port,
            'last_seen': datetime.now(),
            'connected': False
        }
        print(f"[OK] Registered drone {drone_id} at {ip}:{port}")
    
    def _get_drone_url(self, drone_id: str) -> str:
        """Get base URL for drone"""
        if drone_id not in self.drones:
            raise ValueError(f"Drone {drone_id} not registered")
        
        drone = self.drones[drone_id]
        return f"http://{drone['ip']}:{drone['port']}"
    
    def assign_mission(self, drone_id: str, task_id: str, mission_config: Dict) -> bool:
        """
        Assign mission to drone
        """
        try:
            url = f"{self._get_drone_url(drone_id)}/api/mission/assign"
            
            data = {
                'task_id': task_id,
                'mission_config': mission_config
            }
            
            print(f" Assigning mission {task_id} to {drone_id}...")
            
            response = requests.post(url, json=data, timeout=self.timeout)
            
            if response.status_code == 200:
                result = response.json()
                print(f"[OK] Mission assigned: {result['message']}")
                return True
            else:
                print(f"[ERROR] Failed to assign mission: {response.status_code}")
                return False
        
        except requests.exceptions.Timeout:
            print(f"[ERROR] Timeout connecting to {drone_id}")
            return False
        except requests.exceptions.ConnectionError:
            print(f"[ERROR] Connection error to {drone_id}")
            return False
        except Exception as e:
            print(f"[ERROR] Error assigning mission: {e}")
            return False
    
    def start_mission(self, drone_id: str) -> bool:
        """
        Start mission execution on drone
        """
        try:
            url = f"{self._get_drone_url(drone_id)}/api/mission/start"
            
            print(f" Starting mission on {drone_id}...")
            
            response = requests.post(url, timeout=self.timeout)
            
            if response.status_code == 200:
                result = response.json()
                print(f"[OK] Mission started: {result['message']}")
                return True
            else:
                print(f"[ERROR] Failed to start mission: {response.status_code}")
                return False
        
        except Exception as e:
            print(f"[ERROR] Error starting mission: {e}")
            return False
    
    def abort_mission(self, drone_id: str) -> bool:
        """
        Abort current mission on drone
        """
        try:
            url = f"{self._get_drone_url(drone_id)}/api/mission/abort"
            
            print(f"[WARN]  Aborting mission on {drone_id}...")
            
            response = requests.post(url, timeout=self.timeout)
            
            if response.status_code == 200:
                result = response.json()
                print(f"[OK] Mission aborted: {result['message']}")
                return True
            else:
                print(f"[ERROR] Failed to abort mission: {response.status_code}")
                return False
        
        except Exception as e:
            print(f"[ERROR] Error aborting mission: {e}")
            return False
    
    def send_rtl_command(self, drone_id: str, reason: str = "Manual RTL") -> bool:
        """
        Send return to launch command
        """
        try:
            url = f"{self._get_drone_url(drone_id)}/api/rtl"
            
            data = {'reason': reason}
            
            print(f"[HOME] Sending RTL command to {drone_id}...")
            
            response = requests.post(url, json=data, timeout=self.timeout)
            
            if response.status_code == 200:
                result = response.json()
                print(f"[OK] RTL initiated: {result['message']}")
                return True
            else:
                print(f"[ERROR] Failed to send RTL: {response.status_code}")
                return False
        
        except Exception as e:
            print(f"[ERROR] Error sending RTL: {e}")
            return False
    
    def get_drone_status(self, drone_id: str) -> Optional[Dict]:
        """
        Get current status from drone
        """
        try:
            url = f"{self._get_drone_url(drone_id)}/api/status"
            
            response = requests.get(url, timeout=self.timeout)
            
            if response.status_code == 200:
                status = response.json()
                self.drones[drone_id]['last_seen'] = datetime.now()
                self.drones[drone_id]['connected'] = True
                return status
            else:
                return None
        
        except Exception as e:
            self.drones[drone_id]['connected'] = False
            return None
    
    def send_heartbeat(self, drone_id: str) -> bool:
        """
        Send heartbeat to drone
        """
        try:
            url = f"{self._get_drone_url(drone_id)}/api/heartbeat"
            
            data = {'timestamp': datetime.now().isoformat()}
            
            response = requests.post(url, json=data, timeout=5)
            
            if response.status_code == 200:
                self.drones[drone_id]['last_seen'] = datetime.now()
                self.drones[drone_id]['connected'] = True
                return True
            else:
                self.drones[drone_id]['connected'] = False
                return False
        
        except:
            self.drones[drone_id]['connected'] = False
            return False
    
    def start_heartbeat_monitoring(self, interval_sec: float = 5.0):
        """
        Start heartbeat monitoring for all registered drones
        """
        def heartbeat_loop():
            while self.running:
                for drone_id in list(self.drones.keys()):
                    self.send_heartbeat(drone_id)
                time.sleep(interval_sec)
        
        self.running = True
        self.heartbeat_thread = threading.Thread(target=heartbeat_loop, daemon=True)
        self.heartbeat_thread.start()
        print(f"[OK] Heartbeat monitoring started (interval: {interval_sec}s)")
    
    def stop_heartbeat_monitoring(self):
        """Stop heartbeat monitoring"""
        self.running = False
        if self.heartbeat_thread:
            self.heartbeat_thread.join(timeout=2)
        print("[OK] Heartbeat monitoring stopped")
    
    def get_connected_drones(self) -> List[str]:
        """
        Get list of currently connected drones
        """
        return [drone_id for drone_id, info in self.drones.items() if info['connected']]
    
    def get_all_statuses(self) -> Dict[str, Dict]:
        """
        Get status from all registered drones
        """
        statuses = {}
        for drone_id in self.drones.keys():
            status = self.get_drone_status(drone_id)
            if status:
                statuses[drone_id] = status
        return statuses
    
    def test_connection(self, drone_id: str) -> bool:
        """
        Test connection to drone
        """
        print(f"\n[SCAN] Testing connection to {drone_id}...")
        
        # Try to get status
        status = self.get_drone_status(drone_id)
        
        if status:
            print(f"[OK] Connection successful!")
            print(f"   State: {status['state']}")
            print(f"   Mode: {status['mode']}")
            print(f"   Battery: {status['battery']:.1f}%")
            return True
        else:
            print(f"[ERROR] Connection failed")
            return False


def main():
    """Test the ground station client"""
    import yaml
    
    # Load config
    with open('config/dfs_config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    # Create client
    client = GroundStationClient(config)
    
    # Register a test drone (adjust IP as needed)
    client.register_drone('SD-001', '10.10.8.100', 5000)
    
    # Test connection
    client.test_connection('SD-001')
    
    # Start heartbeat monitoring
    client.start_heartbeat_monitoring(interval_sec=5.0)
    
    try:
        # Keep running
        print("\nPress Ctrl+C to stop...")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping...")
        client.stop_heartbeat_monitoring()


if __name__ == '__main__':
    main()
