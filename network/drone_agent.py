"""
Drone Agent - Network Server
Runs on Raspberry Pi, receives commands from ground station and executes missions
"""

from flask import Flask, request, jsonify
import threading
import time
import yaml
from typing import Dict, Optional
from datetime import datetime
import os
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from network.protocol import Message, MessageType, StatusReportMessage, TelemetryMessage
from drone_control import ControllerFactory
from scouter_drone.executor import ScouterDroneSimulator


class DroneAgent:
    """
    Drone-side agent that runs on Raspberry Pi
    Receives commands from ground station and executes missions
    """
    
    def __init__(self, drone_id: str, config_path: str = 'config/dfs_config.yaml'):
        self.drone_id = drone_id
        self.config_path = config_path
        
        # Load config
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        # Initialize controller
        self.controller = ControllerFactory.create_controller(self.drone_id, self.config_path)
        
        # State
        self.state = "IDLE"  # IDLE, EXECUTING, RTL
        self.current_task = None
        self.mission_thread = None
        
        # Flask app for receiving commands
        self.app = Flask(f'drone_agent_{drone_id}')
        self.setup_routes()
        
        # Telemetry thread
        self.telemetry_thread = None
        self.running = False
        
        print(f"[DRONE] Drone Agent initialized: {self.drone_id}")
        print(f"   Mode: {self.config['drone_control']['mode']}")
    
    def setup_routes(self):
        """Setup Flask routes for receiving commands"""
        
        @self.app.route('/api/status', methods=['GET'])
        def get_status():
            """Return current drone status"""
            status = self.get_status()
            return jsonify(status)
        
        @self.app.route('/api/mission/assign', methods=['POST'])
        def assign_mission():
            """Receive mission assignment"""
            try:
                data = request.json
                task_id = data['task_id']
                mission_config = data['mission_config']
                
                print(f"\n Received mission assignment: {task_id}")
                
                # Store task
                self.current_task = {
                    'task_id': task_id,
                    'config': mission_config,
                    'assigned_at': datetime.now().isoformat()
                }
                
                return jsonify({
                    'success': True,
                    'message': f'Mission {task_id} assigned',
                    'drone_id': self.drone_id
                })
            
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 400
        
        @self.app.route('/api/mission/start', methods=['POST'])
        def start_mission():
            """Start executing assigned mission"""
            try:
                if not self.current_task:
                    return jsonify({
                        'success': False,
                        'error': 'No mission assigned'
                    }), 400
                
                if self.state == "EXECUTING":
                    return jsonify({
                        'success': False,
                        'error': 'Mission already executing'
                    }), 400
                
                print(f"\n Starting mission: {self.current_task['task_id']}")
                
                # Start mission in separate thread
                self.mission_thread = threading.Thread(
                    target=self._execute_mission,
                    daemon=True
                )
                self.mission_thread.start()
                
                return jsonify({
                    'success': True,
                    'message': 'Mission started',
                    'task_id': self.current_task['task_id']
                })
            
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/mission/abort', methods=['POST'])
        def abort_mission():
            """Abort current mission"""
            try:
                print(f"\n[WARN]  Aborting mission: {self.current_task['task_id'] if self.current_task else 'None'}")
                
                # Set state to RTL
                self.state = "RTL"
                
                # Emergency stop controller
                if self.controller.is_connected():
                    self.controller.emergency_stop()
                
                return jsonify({
                    'success': True,
                    'message': 'Mission aborted, RTL initiated'
                })
            
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/rtl', methods=['POST'])
        def return_to_launch():
            """Return to launch (safe return home)"""
            try:
                print(f"\n[HOME] RTL command received - returning to launch")
                
                self.state = "RTL"
                
                if self.controller.is_connected():
                    # Use return_to_launch if available, otherwise emergency_stop
                    if hasattr(self.controller, 'return_to_launch'):
                        self.controller.return_to_launch()
                    else:
                        self.controller.emergency_stop()
                
                return jsonify({
                    'success': True,
                    'message': 'RTL initiated'
                })
            
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/land', methods=['POST'])
        def land():
            """Emergency land at current position"""
            try:
                print(f"\n[LAND] Emergency land command received")
                
                self.state = "LANDING"
                
                if self.controller.is_connected():
                    # Use land if available, otherwise emergency_stop
                    if hasattr(self.controller, 'land'):
                        self.controller.land()
                    else:
                        self.controller.emergency_stop()
                
                return jsonify({
                    'success': True,
                    'message': 'Emergency landing initiated'
                })
            
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/kill', methods=['POST'])
        def kill():
            """KILL SWITCH - Immediate motor stop (DANGEROUS - drone will fall!)"""
            try:
                print(f"\n[KILL] KILL SWITCH ACTIVATED - MOTORS STOPPING")
                
                self.state = "KILLED"
                
                if self.controller.is_connected():
                    # Disarm motors immediately
                    if hasattr(self.controller, 'disarm'):
                        self.controller.disarm()
                    else:
                        self.controller.emergency_stop()
                
                return jsonify({
                    'success': True,
                    'message': 'KILL SWITCH ACTIVATED - Motors stopped'
                })
            
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/heartbeat', methods=['POST'])
        def heartbeat():
            """Respond to heartbeat"""
            return jsonify({
                'success': True,
                'drone_id': self.drone_id,
                'timestamp': datetime.now().isoformat(),
                'state': self.state
            })
    
    def get_status(self) -> Dict:
        """Get current drone status"""
        status = {
            'drone_id': self.drone_id,
            'state': self.state,
            'timestamp': datetime.now().isoformat(),
            'mode': self.config['drone_control']['mode'],
            'current_task': self.current_task['task_id'] if self.current_task else None
        }
        
        # Add controller status if connected
        if self.controller.is_connected():
            status.update({
                'armed': self.controller.is_armed(),
                'battery': self.controller.get_battery(),
                'position': {
                    'lat': self.controller.get_position()[0],
                    'lon': self.controller.get_position()[1],
                    'alt': self.controller.get_position()[2]
                },
                'speed': self.controller.get_speed(),
                'heading': self.controller.get_heading(),
                'flight_mode': self.controller.get_mode().value
            })
        else:
            status.update({
                'armed': False,
                'battery': 100.0,
                'position': {'lat': 0.0, 'lon': 0.0, 'alt': 0.0},
                'speed': 0.0,
                'heading': 0.0,
                'flight_mode': 'IDLE'
            })
        
        return status
    
    def _execute_mission(self):
        """Execute mission (runs in separate thread)"""
        try:
            self.state = "EXECUTING"
            
            task_config = self.current_task['config']
            task_id = self.current_task['task_id']
            
            print(f"\n{'='*70}")
            print(f"EXECUTING MISSION: {task_id}")
            print(f"{'='*70}")
            
            # Create simulator with controller
            simulator = ScouterDroneSimulator(
                task_config=task_config,
                drone_id=self.drone_id,
                output_base_dir='data',
                config_path=self.config_path
            )
            
            # Execute mission
            hotspots_count, data_path = simulator.execute_mission()
            
            print(f"\n[PASS] Mission complete: {task_id}")
            print(f"   Hotspots: {hotspots_count}")
            print(f"   Data: {data_path}")
            
            # Update state
            self.state = "IDLE"
            
            # TODO: Send mission complete message to ground station
            
        except Exception as e:
            print(f"\n[ERROR] Mission failed: {e}")
            self.state = "IDLE"
            # TODO: Send mission failed message to ground station
    
    def start_telemetry_stream(self, interval_sec: float = 1.0):
        """Start streaming telemetry to ground station"""
        def telemetry_loop():
            while self.running:
                if self.controller.is_connected():
                    telemetry = {
                        'position': {
                            'lat': self.controller.get_position()[0],
                            'lon': self.controller.get_position()[1],
                            'alt': self.controller.get_position()[2]
                        },
                        'speed': self.controller.get_speed(),
                        'heading': self.controller.get_heading(),
                        'battery': self.controller.get_battery(),
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    # TODO: Send telemetry to ground station
                    # For now, just print
                    if self.state == "EXECUTING":
                        print(f"[COMM] Telemetry: {telemetry['position']}, Battery: {telemetry['battery']:.1f}%")
                
                time.sleep(interval_sec)
        
        self.running = True
        self.telemetry_thread = threading.Thread(target=telemetry_loop, daemon=True)
        self.telemetry_thread.start()
    
    def stop_telemetry_stream(self):
        """Stop telemetry stream"""
        self.running = False
        if self.telemetry_thread:
            self.telemetry_thread.join(timeout=2)
    
    def run(self, host: str = '0.0.0.0', port: int = 5000):
        """
        Start the drone agent server
        """
        print(f"\n{'='*70}")
        print(f"[DRONE] DRONE AGENT STARTING")
        print(f"{'='*70}")
        print(f"Drone ID: {self.drone_id}")
        print(f"Listening on: {host}:{port}")
        print(f"Mode: {self.config['drone_control']['mode']}")
        print(f"{'='*70}\n")
        
        # Start telemetry stream
        self.start_telemetry_stream()
        
        # Start Flask server
        self.app.run(host=host, port=port, debug=False)


def main():
    """Main entry point for drone agent"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Drone Agent - Network Server')
    parser.add_argument('--drone-id', type=str, required=True, help='Drone ID (e.g., SD-001)')
    parser.add_argument('--config', type=str, default='config/dfs_config.yaml', help='Config file path')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=5000, help='Port to listen on')
    
    args = parser.parse_args()
    
    # Create and run agent
    agent = DroneAgent(args.drone_id, args.config)
    agent.run(host=args.host, port=args.port)


if __name__ == '__main__':
    main()
