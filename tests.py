#!/usr/bin/env python3
"""
Consolidated Test Suite for Drone Firefighting System
Run: python tests.py [--simulation] [--network] [--hardware]
"""

import os
import sys
import yaml
import argparse
import tempfile
from datetime import datetime

# Project directory
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(PROJECT_DIR, 'data', 'test_output')


def test_imports():
    """Test all module imports"""
    print("\n[TEST] Module Imports")
    print("-" * 40)
    
    modules = [
        ("database", "DatabaseManager, Drone, Task, FireDetection"),
        ("mission_control.orchestrator", "MissionOrchestrator"),
        ("scouter_drone.simulator", "ScouterDroneSimulator"),
        ("firefighter_drone.simulator", "FirefighterDroneSimulator"),
        ("ml_training.fire_detector", "FireDetector"),
        ("network.communication", "NetworkCommunication"),
        ("dashboard.app", "DFSDashboard"),
        ("modules.camera_module", "CameraModule"),
        ("modules.fire_detector", "FireDetector"),
        ("drone_control", "ControllerFactory"),
    ]
    
    passed = 0
    for module, items in modules:
        try:
            exec(f"from {module} import {items}")
            print(f"  [OK] {module}")
            passed += 1
        except Exception as e:
            print(f"  [FAIL] {module}: {e}")
    
    return passed == len(modules)


def test_config():
    """Test config loading"""
    print("\n[TEST] Configuration")
    print("-" * 40)
    
    try:
        with open('config/dfs_config.yaml', 'r') as f:
            config = yaml.safe_load(f)
        
        print(f"  [OK] Config loaded")
        print(f"       System: {config['system']['name']}")
        print(f"       SD Drones: {config['drone_pool']['scouter_drones']['count']}")
        print(f"       FD Drones: {config['drone_pool']['firefighter_drones']['count']}")
        print(f"       Mode: {config['drone_control']['mode']}")
        return True
    except Exception as e:
        print(f"  [FAIL] {e}")
        return False


def test_database():
    """Test database operations"""
    print("\n[TEST] Database")
    print("-" * 40)
    
    try:
        from database import DatabaseManager, Drone
        db = DatabaseManager()
        session = db.get_session()
        
        drone_count = session.query(Drone).count()
        db.close_session(session)
        
        print(f"  [OK] Database connected ({drone_count} drones)")
        return True
    except Exception as e:
        print(f"  [FAIL] {e}")
        return False


def test_controller():
    """Test drone controller abstraction"""
    print("\n[TEST] Drone Controller")
    print("-" * 40)
    
    try:
        from drone_control import ControllerFactory, FlightMode
        from drone_control.demo_controller import DemoController
        
        # Check available modes
        modes = ControllerFactory.get_available_modes()
        print(f"  [OK] Available modes: {modes}")
        
        # Create demo controller directly (bypass config)
        controller = DemoController("TEST-001")
        print(f"  [OK] Controller created: {type(controller).__name__}")
        
        # Test basic operations
        controller.connect()
        controller.arm()
        controller.takeoff(15.0)
        controller.goto_waypoint(33.226, -96.826, 15.0)
        controller.land()
        controller.disarm()
        controller.disconnect()
        
        print(f"  [OK] Basic flight operations work")
        return True
    except Exception as e:
        print(f"  [FAIL] {e}")
        return False


def test_simulation():
    """Test full simulation with camera and ML"""
    print("\n[TEST] Simulation (SD + FD)")
    print("-" * 40)
    
    # Ensure demo mode
    config_path = 'config/dfs_config.yaml'
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    original_mode = config['drone_control']['mode']
    config['drone_control']['mode'] = 'demo'
    with open(config_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False)
    
    try:
        from scouter_drone.simulator import ScouterDroneSimulator
        from firefighter_drone.simulator import FirefighterDroneSimulator
        
        # Test SD
        task_config = {
            'corner_a_lat': 33.2265, 'corner_a_lon': -96.8265,
            'corner_b_lat': 33.2270, 'corner_b_lon': -96.8260,
            'corner_c_lat': 33.2270, 'corner_c_lon': -96.8265,
            'corner_d_lat': 33.2265, 'corner_d_lon': -96.8260,
            'cruise_altitude_m': 15.0, 'cruise_speed_ms': 5.0,
            'overlap_percent': 20
        }
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_dir = os.path.join(OUTPUT_DIR, f'test_{timestamp}')
        os.makedirs(output_dir, exist_ok=True)
        
        sd_sim = ScouterDroneSimulator(task_config, 'SD-TEST', output_dir)
        print(f"  [OK] SD initialized (camera: {sd_sim.camera is not None})")
        
        hotspots, session_dir = sd_sim.execute_mission()
        print(f"  [OK] SD mission complete ({hotspots} hotspots)")
        sd_sim.cleanup()
        
        # Test FD
        fd_sim = FirefighterDroneSimulator({}, 'FD-TEST', output_dir)
        print(f"  [OK] FD initialized (camera: {fd_sim.camera is not None})")
        
        success, fd_dir = fd_sim.execute_suppression_mission(33.2267, -96.8262)
        print(f"  [OK] FD mission complete (success: {success})")
        fd_sim.cleanup()
        
        return True
    except Exception as e:
        print(f"  [FAIL] {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Restore config
        config['drone_control']['mode'] = original_mode
        with open(config_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)


def test_network(drone_ip=None):
    """Test network communication"""
    print("\n[TEST] Network Communication")
    print("-" * 40)
    
    if not drone_ip:
        print("  [SKIP] No drone IP provided (use --drone-ip)")
        return True
    
    try:
        from network.ground_station_client import GroundStationClient
        import yaml
        
        with open('config/dfs_config.yaml', 'r') as f:
            config = yaml.safe_load(f)
        
        client = GroundStationClient(config)
        client.register_drone('SD-001', drone_ip, 5001)
        
        # Test connection
        if client.test_connection('SD-001'):
            print(f"  [OK] Connected to {drone_ip}")
        else:
            print(f"  [FAIL] Cannot connect to {drone_ip}")
            return False
        
        # Get status
        status = client.get_drone_status('SD-001')
        print(f"  [OK] Status: {status.get('state', 'unknown')}")
        
        return True
    except Exception as e:
        print(f"  [FAIL] {e}")
        return False


def test_hardware():
    """Test hardware connection (Pixhawk)"""
    print("\n[TEST] Hardware (Pixhawk)")
    print("-" * 40)
    
    try:
        from drone_control import ControllerFactory
        
        if not ControllerFactory.is_hardware_available():
            print("  [SKIP] DroneKit not installed")
            return True
        
        # Use factory with mode_override to force hardware mode
        controller = ControllerFactory.create_controller("HW-TEST", mode_override='hardware')
        
        if controller.connect():
            battery = controller.get_battery()
            position = controller.get_position()
            print(f"  [OK] Connected")
            print(f"       Battery: {battery}%")
            print(f"       Position: {position}")
            controller.disconnect()
            return True
        else:
            print(f"  [FAIL] Cannot connect to Pixhawk")
            return False
    except Exception as e:
        print(f"  [FAIL] {e}")
        return False


def reset_drones():
    """Reset all drones to IDLE state"""
    print("\n[UTIL] Resetting Drones")
    print("-" * 40)
    
    try:
        from database import DatabaseManager, Drone, DroneState
        
        db = DatabaseManager()
        session = db.get_session()
        
        drones = session.query(Drone).all()
        for drone in drones:
            drone.state = DroneState.IDLE
            drone.battery_percent = 100.0
            drone.current_task_id = None
        
        session.commit()
        db.close_session(session)
        
        print(f"  [OK] Reset {len(drones)} drones to IDLE")
        return True
    except Exception as e:
        print(f"  [FAIL] {e}")
        return False


def clean_records():
    """Clean all task and fire detection records"""
    print("\n[UTIL] Cleaning Records")
    print("-" * 40)
    
    try:
        from database import DatabaseManager, Task, FireDetection, Drone, DroneState
        
        db = DatabaseManager()
        session = db.get_session()
        
        task_count = session.query(Task).count()
        fire_count = session.query(FireDetection).count()
        
        session.query(FireDetection).delete()
        session.query(Task).delete()
        
        drones = session.query(Drone).all()
        for drone in drones:
            drone.state = DroneState.IDLE
            drone.battery_percent = 100.0
            drone.current_task_id = None
        
        session.commit()
        db.close_session(session)
        
        print(f"  [OK] Deleted {task_count} tasks, {fire_count} detections")
        print(f"  [OK] Reset {len(drones)} drones")
        return True
    except Exception as e:
        print(f"  [FAIL] {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="DFS Test Suite")
    parser.add_argument('--simulation', action='store_true', help='Run simulation tests')
    parser.add_argument('--network', action='store_true', help='Run network tests')
    parser.add_argument('--hardware', action='store_true', help='Run hardware tests')
    parser.add_argument('--drone-ip', type=str, help='Drone IP for network tests')
    parser.add_argument('--reset', action='store_true', help='Reset drones to IDLE')
    parser.add_argument('--clean', action='store_true', help='Clean all records')
    parser.add_argument('--all', action='store_true', help='Run all tests')
    args = parser.parse_args()
    
    print("=" * 60)
    print("DRONE FIREFIGHTING SYSTEM - TEST SUITE")
    print("=" * 60)
    
    # Utility operations
    if args.reset:
        reset_drones()
        return 0
    
    if args.clean:
        clean_records()
        return 0
    
    results = {}
    
    # Always run basic tests
    results['imports'] = test_imports()
    results['config'] = test_config()
    results['database'] = test_database()
    results['controller'] = test_controller()
    
    # Optional tests
    if args.simulation or args.all:
        results['simulation'] = test_simulation()
    
    if args.network or args.all:
        results['network'] = test_network(args.drone_ip)
    
    if args.hardware or args.all:
        results['hardware'] = test_hardware()
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    all_passed = True
    for name, passed in results.items():
        status = "[PASS]" if passed else "[FAIL]"
        print(f"  {name:20s} {status}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("[SUCCESS] All tests passed!")
    else:
        print("[FAILED] Some tests failed")
    print("=" * 60)
    
    return 0 if all_passed else 1


if __name__ == '__main__':
    sys.exit(main())
