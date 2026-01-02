"""
Batch Mission Planner for DFS
Reads flight areas from config file and executes missions automatically
"""
import yaml
import json
import sys
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from mission_control.orchestrator import MissionOrchestrator
from scouter_drone.executor import ScouterDroneSimulator
from firefighter_drone.executor import FirefighterDroneSimulator
from utils.logger import get_logger, setup_logging

logger = get_logger()

class BatchMissionPlanner:
    """
    Batch mission execution with parallel processing
    
    Handles multiple missions simultaneously using ThreadPoolExecutor.
    Added this after realizing sequential execution was too slow for
    testing large mission sets.
    
    TODO: Add progress bar for long-running batches
    TODO: Implement mission retry logic for failed tasks
    TODO: Add resource limits to prevent system overload
    """
    def __init__(self, config_file='config/mission_areas.yaml', simulate_fires=False):
        self.config_file = config_file
        self.orchestrator = MissionOrchestrator()
        self.print_lock = Lock()
        self.simulate_fires = simulate_fires
        self.load_mission_areas()
    
    def load_mission_areas(self):
        """Load mission areas from YAML or JSON file"""
        config_path = Path(self.config_file)
        
        if not config_path.exists():
            raise FileNotFoundError(f"Mission areas file not found: {self.config_file}")
        
        if config_path.suffix in ['.yaml', '.yml']:
            with open(config_path, 'r') as f:
                self.config = yaml.safe_load(f)
        elif config_path.suffix == '.json':
            with open(config_path, 'r') as f:
                self.config = json.load(f)
        else:
            raise ValueError(f"Unsupported file format: {config_path.suffix}. Use .yaml, .yml, or .json")
        
        self.mission_areas = self.config.get('mission_areas', [])
        
        default_settings = {
            'mode': 'sequential',
            'parallel_max_workers': 3,
            'task_dispatch_delay_sec': 0.5,
            'delay_between_missions_sec': 2,
            'stop_on_error': False,
            'auto_dispatch_firefighters': True
        }
        self.execution_settings = {**default_settings, **self.config.get('execution', {})}
        
        execution_config = self.orchestrator.config.get('mission_planning', {}).get('execution', {})
        if execution_config:
            self.execution_settings['mode'] = execution_config.get('mode', self.execution_settings['mode'])
            self.execution_settings['parallel_max_workers'] = execution_config.get('parallel_max_workers', self.execution_settings['parallel_max_workers'])
            self.execution_settings['task_dispatch_delay_sec'] = execution_config.get('task_dispatch_delay_sec', self.execution_settings['task_dispatch_delay_sec'])
            self.execution_settings['delay_between_missions_sec'] = execution_config.get('delay_between_missions_sec', self.execution_settings['delay_between_missions_sec'])
        
        print(f"[OK] Loaded {len(self.mission_areas)} mission area(s) from {self.config_file}")
    
    def validate_area(self, area):
        """Validate flight area coordinates"""
        required_fields = ['name', 'priority', 'corners']
        for field in required_fields:
            if field not in area:
                return False, f"Missing field: {field}"
        
        corners = area['corners']
        required_corners = ['corner_a', 'corner_b', 'corner_c', 'corner_d']
        
        for corner in required_corners:
            if corner not in corners:
                return False, f"Missing {corner}"
            if 'latitude' not in corners[corner] or 'longitude' not in corners[corner]:
                return False, f"{corner} missing latitude/longitude"
        
        return True, "Valid"
    
    def execute_all_missions(self):
        """Execute all missions from config"""
        print("\n" + "="*70)
        print("[BATCH] STARTING BATCH MISSION EXECUTION")
        print("="*70)
        print(f"   Total missions: {len(self.mission_areas)}")
        print(f"   Execution mode: {self.execution_settings['mode']}")
        
        if self.execution_settings['mode'] == 'parallel':
            print(f"   Max parallel workers: {self.execution_settings['parallel_max_workers']}")
            print(f"   Task dispatch delay: {self.execution_settings['task_dispatch_delay_sec']}s")
        else:
            print(f"   Delay between missions: {self.execution_settings['delay_between_missions_sec']}s")
        
        print(f"   Stop on error: {self.execution_settings['stop_on_error']}")
        
        if self.execution_settings['mode'] == 'parallel':
            results = self._execute_parallel()
        else:
            results = self._execute_sequential()
        
        self.print_summary(results)
        return results
    
    def _execute_sequential(self):
        """Execute missions sequentially"""
        results = []
        
        for i, area in enumerate(self.mission_areas):
            print(f"\n{'='*70}")
            print(f"[MISSION {i+1}/{len(self.mission_areas)}] {area.get('name', 'Unnamed')}")
            print(f"{'='*70}")
            
            valid, msg = self.validate_area(area)
            if not valid:
                print(f"[FAIL] Invalid area: {msg}")
                results.append({'name': area.get('name'), 'success': False, 'error': msg})
                if self.execution_settings['stop_on_error']:
                    break
                continue
            
            try:
                result = self.execute_single_mission(area, i+1)
                results.append(result)
            except Exception as e:
                print(f"[FAIL] Mission failed: {e}")
                results.append({'name': area.get('name'), 'success': False, 'error': str(e)})
                if self.execution_settings['stop_on_error']:
                    break
            
            if i < len(self.mission_areas) - 1:
                delay = self.execution_settings['delay_between_missions_sec']
                print(f"\n[WAIT] Waiting {delay}s before next mission...")
                time.sleep(delay)
        
        return results
    
    def _execute_parallel(self):
        """Execute missions in parallel using thread pool"""
        results = []
        max_workers = self.execution_settings['parallel_max_workers']
        dispatch_delay = self.execution_settings['task_dispatch_delay_sec']
        
        print(f"\n[PARALLEL] Dispatching tasks with {dispatch_delay}s delay between dispatches...")
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {}
            
            for i, area in enumerate(self.mission_areas):
                valid, msg = self.validate_area(area)
                if not valid:
                    with self.print_lock:
                        print(f"[FAIL] Invalid area {area.get('name')}: {msg}")
                    results.append({'name': area.get('name'), 'success': False, 'error': msg})
                    continue
                
                future = executor.submit(self._execute_mission_wrapper, area, i+1)
                futures[future] = area
                
                with self.print_lock:
                    print(f"[DISPATCH] Task {i+1}/{len(self.mission_areas)}: {area.get('name', 'Unnamed')}")
                
                if i < len(self.mission_areas) - 1:
                    time.sleep(dispatch_delay)
            
            print(f"\n[PARALLEL] All tasks dispatched. Waiting for completion...\n")
            
            for future in as_completed(futures):
                area = futures[future]
                try:
                    result = future.result()
                    results.append(result)
                    
                    with self.print_lock:
                        status = "[OK]" if result.get('success') else "[FAIL]"
                        print(f"{status} Mission '{result.get('name')}' completed")
                        if result.get('success'):
                            print(f"      Task: {result.get('task_id')}, Drone: {result.get('drone_id')}, Hotspots: {result.get('hotspots')}")
                        else:
                            print(f"      Error: {result.get('error')}")
                
                except Exception as e:
                    with self.print_lock:
                        print(f"[FAIL] Mission '{area.get('name')}' failed: {e}")
                    results.append({'name': area.get('name'), 'success': False, 'error': str(e)})
        
        return results
    
    def _execute_mission_wrapper(self, area, mission_num):
        """Wrapper for parallel execution with thread-safe printing"""
        try:
            with self.print_lock:
                print(f"\n[START] Mission {mission_num}: {area.get('name', 'Unnamed')}")
            
            result = self.execute_single_mission(area, mission_num)
            return result
        except Exception as e:
            return {'name': area.get('name'), 'success': False, 'error': str(e)}
    
    def execute_single_mission(self, area, mission_num=1, simulate_fire=False):
        """Execute a single mission"""
        corners = area['corners']
        flight_area = {
            'corner_a': {'latitude': corners['corner_a']['latitude'], 'longitude': corners['corner_a']['longitude']},
            'corner_b': {'latitude': corners['corner_b']['latitude'], 'longitude': corners['corner_b']['longitude']},
            'corner_c': {'latitude': corners['corner_c']['latitude'], 'longitude': corners['corner_c']['longitude']},
            'corner_d': {'latitude': corners['corner_d']['latitude'], 'longitude': corners['corner_d']['longitude']}
        }
        
        task = self.orchestrator.create_scout_task(
            flight_area=flight_area,
            priority=area.get('priority', 'medium')
        )
        
        task_id = task['task_id']
        drone = self.orchestrator.assign_task_to_drone(task_id)
        if not drone:
            raise Exception("No available drones")
        
        drone_id = drone['drone_id']
        
        # Set logging context for this mission
        logger.set_context(task_id=task_id, drone_id=drone_id, module='batch_mission')
        
        with self.print_lock:
            logger.info(f"[OK] Created and assigned task")
        
        self.orchestrator.start_task_execution(task_id)
        
        task_config = {
            'corner_a_lat': flight_area['corner_a']['latitude'],
            'corner_a_lon': flight_area['corner_a']['longitude'],
            'corner_b_lat': flight_area['corner_b']['latitude'],
            'corner_b_lon': flight_area['corner_b']['longitude'],
            'corner_c_lat': flight_area['corner_c']['latitude'],
            'corner_c_lon': flight_area['corner_c']['longitude'],
            'corner_d_lat': flight_area['corner_d']['latitude'],
            'corner_d_lon': flight_area['corner_d']['longitude'],
            'cruise_altitude_m': area.get('altitude_m', 15.24),
            'cruise_speed_ms': area.get('speed_ms', 5.0),
            'overlap_percent': area.get('overlap_percent', 20)
        }
        
        sd_simulator = ScouterDroneSimulator(task_config, drone_id)
        hotspots, data_path = sd_simulator.execute_mission()
        sd_simulator.cleanup()
        
        # Simulate fire detection if flag is set
        if self.simulate_fires and hotspots == 0:
            with self.print_lock:
                logger.info(f"[FIRE] Simulating fire detection")
            
            # Inject a simulated fire detection
            center_lat = (flight_area['corner_a']['latitude'] + flight_area['corner_c']['latitude']) / 2
            center_lon = (flight_area['corner_a']['longitude'] + flight_area['corner_c']['longitude']) / 2
            
            detection = self.orchestrator.register_fire_detection(
                task_id=task_id,
                drone_id=drone_id,
                latitude=center_lat,
                longitude=center_lon,
                temperature_c=65.5,
                confidence=0.92,
                detection_method='thermal_simulated'
            )
            
            with self.print_lock:
                logger.info(f"[FIRE] Fire registered at ({center_lat:.6f}, {center_lon:.6f})")
            
            hotspots = 1
            
            # Wait a bit for FD dispatch and then execute FD mission
            import time
            time.sleep(1)
            
            # Execute FD suppression mission if one was dispatched
            self._execute_fd_suppression_missions()
        
        # Clear context before completing
        logger.clear_context()
        self.orchestrator.complete_task(task_id, hotspots, data_path)
        
        return {
            'name': area.get('name'),
            'task_id': task_id,
            'drone_id': drone_id,
            'hotspots': hotspots,
            'data_path': data_path,
            'success': True
        }
    
    def _execute_fd_suppression_missions(self):
        """Execute any pending FD suppression missions"""
        from database import DatabaseManager, Task, Drone, TaskState, DroneState
        
        db_manager = DatabaseManager()
        session = db_manager.get_session()
        
        try:
            # Find all assigned suppression tasks
            fd_tasks = session.query(Task).filter(
                Task.task_type == 'suppress',
                Task.state == TaskState.ASSIGNED
            ).all()
            
            for task in fd_tasks:
                drone = session.query(Drone).get(task.drone_id)
                if not drone:
                    continue
                
                # Set logging context for FD mission
                logger.set_context(task_id=task.task_id, drone_id=drone.drone_id, module='FD_suppression')
                
                with self.print_lock:
                    logger.info(f"[FD] Starting suppression mission")
                
                # Start task execution
                self.orchestrator.start_task_execution(task.task_id)
                
                # Execute FD mission simulation
                target_lat = (task.corner_a_lat + task.corner_c_lat) / 2
                target_lon = (task.corner_a_lon + task.corner_c_lon) / 2
                
                task_config = {
                    'suppression_duration_sec': 30,
                    'approach_altitude_m': task.cruise_altitude_m or 12.0
                }
                
                fd_simulator = FirefighterDroneSimulator(task_config, drone.drone_id)
                success, data_path = fd_simulator.execute_suppression_mission(target_lat, target_lon)
                fd_simulator.cleanup()
                
                # Complete the suppression task
                if success:
                    self.orchestrator.complete_suppression_task(task.task_id, data_path)
                    with self.print_lock:
                        logger.info(f"[OK] Suppression completed")
                else:
                    with self.print_lock:
                        logger.error(f"[FAIL] Suppression failed")
                
                # Clear context
                logger.clear_context()
        
        except Exception as e:
            with self.print_lock:
                logger.error(f"[FAIL] Error executing FD missions: {e}")
        finally:
            db_manager.close_session(session)
    
    def print_summary(self, results):
        """Print execution summary"""
        print("\n" + "="*70)
        print("[STATS] BATCH MISSION SUMMARY")
        print("="*70)
        
        successful = [r for r in results if r.get('success')]
        failed = [r for r in results if not r.get('success')]
        
        print(f"   Total missions: {len(results)}")
        print(f"   Successful: {len(successful)}")
        print(f"   Failed: {len(failed)}")
        
        if successful:
            total_hotspots = sum(r.get('hotspots', 0) for r in successful)
            print(f"   Total hotspots: {total_hotspots}")
        
        if failed:
            print("\n[FAIL] Failed missions:")
            for r in failed:
                print(f"   - {r.get('name')}: {r.get('error')}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Batch Mission Planner for DFS")
    parser.add_argument('--config', default='config/mission_areas.yaml',
                        help='Path to mission areas config file (YAML or JSON)')
    parser.add_argument('--validate-only', action='store_true',
                        help='Only validate config, do not execute')
    parser.add_argument('--mode', choices=['sequential', 'parallel'],
                        help='Execution mode (overrides config)')
    parser.add_argument('--workers', type=int,
                        help='Max parallel workers (parallel mode only)')
    parser.add_argument('--dispatch-delay', type=float,
                        help='Delay between task dispatches in seconds (parallel mode)')
    parser.add_argument('--mission-delay', type=float,
                        help='Delay between missions in seconds (sequential mode)')
    parser.add_argument('--log-level', default='INFO',
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        help='Set logging level (default: INFO)')
    parser.add_argument('--log-file', help='Optional log file path')
    parser.add_argument('--simulate-fires', action='store_true',
                        help='Simulate fire detections to trigger FD drone dispatch')
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(level=args.log_level, log_file=args.log_file)
    
    try:
        planner = BatchMissionPlanner(args.config, simulate_fires=args.simulate_fires)
        
        if args.mode:
            planner.execution_settings['mode'] = args.mode
        if args.workers:
            planner.execution_settings['parallel_max_workers'] = args.workers
        if args.dispatch_delay is not None:
            planner.execution_settings['task_dispatch_delay_sec'] = args.dispatch_delay
        if args.mission_delay is not None:
            planner.execution_settings['delay_between_missions_sec'] = args.mission_delay
        
        if args.validate_only:
            print("\n[OK] Configuration validated OK")
            for i, area in enumerate(planner.mission_areas):
                valid, msg = planner.validate_area(area)
                status = "[OK]" if valid else "[FAIL]"
                print(f"   {status} Area {i+1}: {area.get('name', 'Unnamed')} - {msg}")
            return 0
        
        results = planner.execute_all_missions()
        
        failed = [r for r in results if not r.get('success')]
        return 1 if failed else 0
        
    except FileNotFoundError as e:
        print(f"[FAIL] {e}")
        print("\nCreate a mission areas file. Example config/mission_areas.yaml:")
        print("""
mission_areas:
  - name: "Test Area 1"
    priority: high
    corners:
      corner_a:
        latitude: 33.2271
        longitude: -96.8252
      corner_b:
        latitude: 33.2272
        longitude: -96.8279
      corner_c:
        latitude: 33.2258
        longitude: -96.8279
      corner_d:
        latitude: 33.2257
        longitude: -96.8252

execution:
  delay_between_missions_sec: 2
  stop_on_error: false
  auto_dispatch_firefighters: true
""")
        return 1
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
