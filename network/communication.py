"""
Network Communication Layer
Handles communication between DFS Ground Control and Drones
"""
import requests
import json
from typing import Dict, Optional
from datetime import datetime


class NetworkCommunication:
    def __init__(self, config: Dict):
        self.config = config
        self.primary_network = config['network']['primary']
        self.backup_network = config['network']['backup']
        self.protocol = config['network']['protocol']
        self.timeout = config['network']['timeout_sec']
        
        # Use primary network by default
        self.active_network = self.primary_network
        self.base_url = f"{self.protocol}://{self.active_network['ip']}:{self.active_network['port']}"
    
    def send_task_to_drone(self, drone_id: str, task_data: Dict) -> bool:
        """Send task assignment to drone"""
        try:
            endpoint = f"{self.base_url}/api/drone/{drone_id}/task"
            response = requests.post(
                endpoint,
                json=task_data,
                timeout=self.timeout
            )
            return response.status_code == 200
        except Exception as e:
            print(f"Error sending task to {drone_id}: {e}")
            return False
    
    def receive_hotspot_alert(self, drone_id: str, hotspot_data: Dict) -> bool:
        """Receive hotspot alert from drone"""
        try:
            # In simulation, this is called directly
            # In real system, this would be an API endpoint
            print(f"[FIRE] Hotspot alert from {drone_id}:")
            print(f"   Location: ({hotspot_data['latitude']:.6f}, {hotspot_data['longitude']:.6f})")
            print(f"   Temperature: {hotspot_data['temperature_c']:.1f}°C")
            return True
        except Exception as e:
            print(f"Error receiving hotspot alert: {e}")
            return False
    
    def get_drone_status(self, drone_id: str) -> Optional[Dict]:
        """Get current status from drone"""
        try:
            endpoint = f"{self.base_url}/api/drone/{drone_id}/status"
            response = requests.get(endpoint, timeout=self.timeout)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"Error getting status from {drone_id}: {e}")
            return None
    
    def upload_mission_data(self, drone_id: str, data_path: str) -> bool:
        """Upload mission data from drone to DFS"""
        try:
            # In simulation, data is already local
            # In real system, this would transfer files
            print(f"[COMM] Uploading mission data from {drone_id}")
            print(f"   Data path: {data_path}")
            return True
        except Exception as e:
            print(f"Error uploading data: {e}")
            return False
    
    def send_heartbeat(self, drone_id: str) -> bool:
        """Send heartbeat to check drone connectivity"""
        try:
            endpoint = f"{self.base_url}/api/drone/{drone_id}/heartbeat"
            response = requests.post(
                endpoint,
                json={'timestamp': datetime.now().isoformat()},
                timeout=5
            )
            return response.status_code == 200
        except:
            return False
    
    def switch_to_backup_network(self):
        """Switch to backup network if primary fails"""
        print("[WARN]  Switching to backup network...")
        self.active_network = self.backup_network
        self.base_url = f"{self.protocol}://{self.active_network['ip']}:{self.active_network['port']}"
        print(f"[OK] Now using {self.active_network['ssid']} ({self.active_network['ip']})")
