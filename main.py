"""
Drone Firefighting System - Main Entry Point

This is where everything starts. Initializes database, mission control,
network, and fire detection. Can run in demo mode or launch the dashboard.

Author: Anshul Ojha
"""

import yaml
import argparse
import time
from datetime import datetime
from database import DatabaseManager
from mission_control.orchestrator import MissionOrchestrator
from scouter_drone.executor import ScouterDroneSimulator
from firefighter_drone.executor import FirefighterDroneSimulator
from ml_training.fire_detector import FireDetector
from network.communication import NetworkCommunication
from network.ground_station_client import GroundStationClient
from utils.logger import get_logger, setup_logging

logger = get_logger()


def initialize_system(config_path='config/dfs_config.yaml'):
    """
    Boot up the whole system

    Loads config, sets up database, mission control, network, and fire detection.
    Takes about 2-3 seconds on Pi 4. Longer on Pi 3 (don't use Pi 3).
    """
    logger.info("\n" + "="*70)
    logger.info("[DRONE] DRONE FIREFIGHTING SYSTEM - INITIALIZATION")
    logger.info("="*70)
    
    # Load config file
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    logger.info(f"\n System: {config['system']['name']} v{config['system']['version']}")
    logger.info(f"   Ground Station: {config['system']['ground_station_id']}")
    
    # Database setup - SQLite for simplicity
    logger.info("\n[SAVE] Initializing database...")
    db_manager = DatabaseManager(config_path)
    db_manager.init_drone_pool(config_path)  # Creates drones if first run
    
    # Mission control - the brain of the operation
    logger.info("\n[TARGET] Initializing mission control...")
    orchestrator = MissionOrchestrator(config_path)
    
    # Network setup - WiFi for ground station communication
    logger.info("\n[COMM] Initializing network communication...")
    network = NetworkCommunication(config)
    logger.info(f"   Primary Network: {config['network']['primary']['ssid']} ({config['network']['primary']['ip']})")
    logger.info(f"   Backup Network: {config['network']['backup']['ssid']} ({config['network']['backup']['ip']})")
    # TODO: Add automatic failover between networks
    
    # Fire detection - thermal + ML confirmation
    logger.info("\n[FIRE] Initializing fire detection module...")
    fire_detector = FireDetector(
        hotspot_threshold_c=config['fire_detection']['thermal']['hotspot_threshold_c'],
        min_pixels=config['fire_detection']['thermal']['min_hotspot_pixels']
    )
    # Using 50°C threshold - tuned from field tests
    
    logger.info("\n[PASS] System init complete!")
    
    return orchestrator, network, fire_detector, config


def run_demo_mission(orchestrator, fire_detector, config, mode_override=None, use_network=False, target_drone_id=None):
    """
    Demo mission for testing without hardware

    Creates a scout task, assigns drone, simulates flight, detects fires.
    Uses real GPS coordinates from my test field in Prosper, TX.
    
    Args:
        mode_override: If provided, overrides drone_control.mode from config
        use_network: If True, sends mission to drone over network (ground station mode)
        target_drone_id: If provided, uses this specific drone instead of auto-assignment
    """
    logger.info("\n" + "="*70)
    logger.info(" RUNNING DEMONSTRATION MISSION")
    logger.info("="*70)
    
    # Create scout task - using real coordinates from my test field
    print("\n[LOC] Creating scouting task...")
    flight_area = {
        'corner_a': {'latitude': 33.2271901, 'longitude': -96.8252657},
        'corner_b': {'latitude': 33.2272414, 'longitude': -96.8279586},
        'corner_c': {'latitude': 33.2258722, 'longitude': -96.8279840},
        'corner_d': {'latitude': 33.2257764, 'longitude': -96.8252980}
    }
    # This is about 200m x 150m - takes ~3 minutes to scan at 50ft altitude
    
    task = orchestrator.create_scout_task(flight_area, priority='high')
    
    task_id = task['task_id']
    task_config = task
    
    # Find available drone
    if target_drone_id:
        # Use specified drone
        print(f"\n[SYNC] Using specified drone: {target_drone_id}...")
        drone_id = target_drone_id
        
        # Manually assign task to specified drone using session
        from database import Drone, Task, DroneState, TaskState
        session = orchestrator.db_manager.get_session()
        
        try:
            drone = session.query(Drone).filter_by(drone_id=drone_id).first()
            
            if not drone:
                all_drones = session.query(Drone).all()
                print(f"[ERROR] Drone {drone_id} not found in database")
                print(f"   Available drones: {[d.drone_id for d in all_drones]}")
                return
            
            if drone.state != DroneState.IDLE:
                print(f"[WARN] Drone {drone_id} is {drone.state.value}, forcing assignment anyway...")
            
            # Force assignment
            drone.state = DroneState.ASSIGNED
            task_obj = session.query(Task).filter_by(task_id=task_id).first()
            if task_obj:
                task_obj.state = TaskState.ASSIGNED
                task_obj.assigned_drone_id = drone_id
                task_obj.assigned_at = datetime.now()
            
            session.commit()
            print(f"[OK] Task {task_id} assigned to {drone_id}")
            
        except Exception as e:
            session.rollback()
            print(f"[ERROR] Failed to assign task: {e}")
            return
        finally:
            orchestrator.db_manager.close_session(session)
    else:
        # Auto-assign to available drone
        print("\n[SYNC] Assigning task to available drone...")
        drone = orchestrator.assign_task_to_drone(task_id)
        
        if not drone:
            print("[FAIL] No available drones!")
            return
        
        drone_id = drone['drone_id']
    
    # Start mission
    print(f"\n Starting mission execution with {drone_id}...")
    orchestrator.start_task_execution(task_id)
    
    # Run simulated mission (or real if hardware connected)
    print(f"\n{'='*70}")
    print(f"SCOUTER DRONE MISSION - {drone_id}")
    print(f"{'='*70}")
    
    if use_network:
        # Network mode: Send mission to drone over WiFi
        print(f"\n[COMM] Network mode: Sending mission to {drone_id} over WiFi...")
        
        # Create ground station client
        gs_client = GroundStationClient(config)
        
        # Register drone from config
        drone_registry = config.get('drone_pool', {}).get('drone_registry', {})
        if drone_id not in drone_registry:
            print(f"[ERROR] Drone {drone_id} not found in drone_registry config")
            print(f"   Available drones: {list(drone_registry.keys())}")
            return
        
        drone_info = drone_registry[drone_id]
        gs_client.register_drone(drone_id, drone_info['ip'], drone_info['port'])
        
        # Test connection
        if not gs_client.test_connection(drone_id):
            print(f"[ERROR] Cannot connect to {drone_id} at {drone_info['ip']}:{drone_info['port']}")
            print(f"   Make sure drone agent is running on the Pi")
            print(f"   Run on Pi: python -m network.drone_agent --drone-id {drone_id}")
            return
        
        # Assign mission
        if not gs_client.assign_mission(drone_id, task_id, task_config):
            print(f"[ERROR] Failed to assign mission to {drone_id}")
            return
        
        # Start mission execution
        if not gs_client.start_mission(drone_id):
            print(f"[ERROR] Failed to start mission on {drone_id}")
            return
        
        print(f"\n[OK] Mission sent to {drone_id} - executing on drone...")
        print(f"   Monitor status: http://{drone_info['ip']}:{drone_info['port']}/api/status")
        
        print("[WAIT] Waiting for mission completion...")
        print("[TIP] Press Ctrl+C to abort mission and RTL")
        
        try:
            while True:
                status = gs_client.get_drone_status(drone_id)
                if status and status.get('state') in ['IDLE', 'RTL', 'COMPLETED']:
                    print(f"\n[OK] Mission complete - State: {status.get('state')}")
                    break
                
                print(f"   Status: {status.get('state') if status else 'UNKNOWN'}")
                time.sleep(1)
        
        except KeyboardInterrupt:
            print("\n\n[WARN] Mission abort requested by user")
            print("[ABORT] Sending abort command to drone...")
            
            try:
                # Send abort command to drone
                import requests
                response = requests.post(
                    f"http://{drone_info['ip']}:{drone_info['port']}/api/mission/abort",
                    timeout=5
                )
                
                if response.status_code == 200:
                    print("[OK] Abort command sent - drone returning to launch")
                    print("[OK] Mission aborted safely")
                else:
                    print(f"[ERROR] Abort command failed: {response.status_code}")
            
            except Exception as e:
                print(f"[ERROR] Failed to send abort command: {e}")
                print("[WARN] Drone may still be executing mission!")
            
            return
        
        # For network mode, we don't have local data
        hotspots_detected = 0
        data_path = None
    else:
        # Local mode: Run simulator locally (demo or hardware)
        sd_simulator = ScouterDroneSimulator(task_config, drone_id, mode_override=mode_override)
        hotspots_detected, data_path = sd_simulator.execute_mission()
    
    # Process any fires found
    if hotspots_detected > 0:
        print(f"\n[FIRE] Processing {hotspots_detected} fire detections...")
        hotspots = sd_simulator.get_hotspots()
        
        for hotspot in hotspots[:3]:  # Just first 3 for demo speed
            detection = orchestrator.register_fire_detection(
                task_id=task_id,
                drone_id=drone_id,
                latitude=hotspot['latitude'],
                longitude=hotspot['longitude'],
                temperature_c=hotspot['temperature_c'],
                confidence=hotspot['confidence'],
                detection_method='thermal'
            )
            
            time.sleep(1)  # Simulate ML processing time
    
    # Mark task done
    print(f"\n[OK] Completing task...")
    orchestrator.complete_task(task_id, hotspots_detected, data_path)
    
    # Print status summary
    print(f"\n{'='*70}")
    print("SYSTEM STATUS")
    print(f"{'='*70}")
    status = orchestrator.get_system_status()
    
    print(f"\n[DRONE] Drones:")
    print(f"   Total: {status['drones']['total']}")
    print(f"   Idle: {status['drones']['idle']}")
    print(f"   Flying: {status['drones']['flying']}")
    print(f"   Scouters: {status['drones']['scouters']}")
    print(f"   Firefighters: {status['drones']['firefighters']}")
    
    print(f"\n Tasks:")
    print(f"   Total: {status['tasks']['total']}")
    print(f"   Completed: {status['tasks']['completed']}")
    print(f"   Executing: {status['tasks']['executing']}")
    
    print(f"\n[FIRE] Fire Detections:")
    print(f"   Total: {status['detections']['total']}")
    print(f"   Active: {status['detections']['detected']}")
    print(f"   Dispatched: {status['detections']['dispatched']}")
    print(f"   Suppressed: {status['detections']['suppressed']}")
    
    print(f"\n{'='*70}")
    print("[OK] DEMONSTRATION MISSION COMPLETE")
    print(f"{'='*70}")
    
    print(f"\n[STATS] Mission Data:")
    print(f"   Location: {data_path}")
    print(f"   Hotspots Detected: {hotspots_detected}")
    print(f"\n[TIP] Next Steps:")
    print(f"   1. View data in: {data_path}")
    print(f"   2. Run dashboard: python dashboard/app.py")
    print(f"   3. Check database: database/dfs.db")


def main():
    """
    Main entry point - parses args and runs appropriate mode
    """
    parser = argparse.ArgumentParser(description='Drone Firefighting System')
    parser.add_argument('--config', default='config/dfs_config.yaml', help='Configuration file path')
    parser.add_argument('--demo', action='store_true', help='Run demonstration mission')
    parser.add_argument('--network', action='store_true', help='Use network mode (ground station sends missions to drones over WiFi)')
    parser.add_argument('--drone-id', type=str, help='Specify drone ID to use (e.g., SD-001)')
    parser.add_argument('--dashboard', action='store_true', help='Launch dashboard only')
    parser.add_argument('--quiet', action='store_true', help='Suppress dashboard server logs')
    parser.add_argument('--log-level', default='INFO', 
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        help='Set logging level (default: INFO)')
    parser.add_argument('--log-file', help='Optional log file path')
    
    args = parser.parse_args()
    
    # Setup logging system
    setup_logging(level=args.log_level, log_file=args.log_file)
    
    # Suppress dashboard noise if --quiet flag set
    if args.quiet:
        import logging
        logging.getLogger('werkzeug').setLevel(logging.ERROR)
        logging.getLogger('dash').setLevel(logging.ERROR)
    
    # Boot up system
    orchestrator, network, fire_detector, config = initialize_system(args.config)
    
    if args.dashboard:
        # Launch web dashboard
        from dashboard.app import DFSDashboard
        dashboard = DFSDashboard(args.config)
        dashboard.run(debug=False if args.quiet else True)
    
    elif args.demo:
        # Run demo mission
        if args.network:
            # Network mode: Ground station sends mission to drone over WiFi
            print("\n[COMM] Running in NETWORK mode (Ground Station -> WiFi -> Drone)")
            if args.drone_id:
                print(f"[TARGET] Target drone: {args.drone_id}")
            run_demo_mission(orchestrator, fire_detector, config, mode_override=None, use_network=True, target_drone_id=args.drone_id)
        else:
            # Local mode: Force demo controller for local simulation
            print("\n[LOCAL] Running in LOCAL DEMO mode (simulated flight)")
            if args.drone_id:
                print(f"[TARGET] Target drone: {args.drone_id}")
            run_demo_mission(orchestrator, fire_detector, config, mode_override='demo', use_network=False, target_drone_id=args.drone_id)
    
    else:
        print("\n[TIP] Usage:")
        print("   python main.py --demo                           # Run local demo mission (simulated)")
        print("   python main.py --demo --network --drone-id SD-001  # Run network mission to specific drone")
        print("   python main.py --dashboard                      # Launch dashboard")
        print("\n   For network mode, first start drone agent on Pi:")
        print("   python -m network.drone_agent --drone-id SD-001")
        print("\n   For full operation, run both in separate terminals")


if __name__ == '__main__':
    main()
