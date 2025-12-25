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
from scouter_drone.simulator import ScouterDroneSimulator
from firefighter_drone.simulator import FirefighterDroneSimulator
from ml_training.fire_detector import FireDetector
from network.communication import NetworkCommunication
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


def run_demo_mission(orchestrator, fire_detector, config):
    """
    Demo mission for testing without hardware

    Creates a scout task, assigns drone, simulates flight, detects fires.
    Uses real GPS coordinates from my test field in Prosper, TX.
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
    
    sd_simulator = ScouterDroneSimulator(task_config, drone_id)
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
        run_demo_mission(orchestrator, fire_detector, config)
    
    else:
        print("\n[TIP] Usage:")
        print("   python main.py --demo          # Run demonstration mission")
        print("   python main.py --dashboard     # Launch dashboard")
        print("\n   For full operation, run both in separate terminals")


if __name__ == '__main__':
    main()
