"""
Mission Control Orchestrator - Core DFS logic
"""
import yaml
from datetime import datetime, timedelta
from typing import List, Optional, Dict
import random
from database import DatabaseManager, Drone, Task, FireDetection, DroneState, TaskState, DroneType


class MissionOrchestrator:
    """
    Mission control - the brain of the operation
    
    Handles task creation, drone assignment, fire detection registration.
    Uses round-robin for load balancing - simple but works well enough.
    
    TODO: Add battery-aware assignment (prefer drones with more charge)
    TODO: Implement proximity-based assignment for faster response
    TODO: Add mission priority queue instead of FIFO
    """
    def __init__(self, config_path='config/dfs_config.yaml'):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.db_manager = DatabaseManager(config_path)
        self._initialize_counters()
        self._load_round_robin_state()
    
    def _initialize_counters(self):
        """Load task/detection counters from DB to avoid ID conflicts"""
        # This was a pain to debug - counters were resetting on restart
        # causing duplicate task IDs. Now we check the DB for max counter.
        """Initialize task and detection counters from existing database records"""
        session = self.db_manager.get_session()
        try:
            # Get the highest task counter from today's tasks
            today = datetime.now().strftime('%Y%m%d')
            tasks_today = session.query(Task).filter(
                Task.task_id.like(f'TASK-{today}-%')
            ).all()
            
            if tasks_today:
                max_counter = max([int(t.task_id.split('-')[-1]) for t in tasks_today])
                self.task_counter = max_counter
            else:
                self.task_counter = 0
            
            # Get the highest detection counter from today's detections
            detections_today = session.query(FireDetection).filter(
                FireDetection.detection_id.like(f'FIRE-{today}-%')
            ).all()
            
            if detections_today:
                max_counter = max([int(d.detection_id.split('-')[-1]) for d in detections_today])
                self.detection_counter = max_counter
            else:
                self.detection_counter = 0
                
        finally:
            self.db_manager.close_session(session)
    
    def _load_round_robin_state(self):
        """Load round-robin state from DB to continue where we left off"""
        # Round-robin is simple but fair. Tried random assignment first
        # but some drones got way more tasks than others.
        """Load round-robin state from last assignments in database"""
        session = self.db_manager.get_session()
        try:
            # Find last assigned scouter drone
            last_scout_task = session.query(Task).filter(
                Task.task_type == 'scout',
                Task.drone_id.isnot(None)
            ).order_by(Task.assigned_at.desc()).first()
            
            if last_scout_task:
                last_drone = session.query(Drone).get(last_scout_task.drone_id)
                if last_drone:
                    # Get all scouter drones ordered by ID
                    all_scouters = session.query(Drone).filter(
                        Drone.drone_type == DroneType.SCOUTER
                    ).order_by(Drone.drone_id).all()
                    
                    # Find index of last assigned drone
                    for i, drone in enumerate(all_scouters):
                        if drone.drone_id == last_drone.drone_id:
                            self.last_assigned_scouter_index = i
                            break
                    else:
                        self.last_assigned_scouter_index = -1
                else:
                    self.last_assigned_scouter_index = -1
            else:
                self.last_assigned_scouter_index = -1
            
            # Find last assigned firefighter drone
            last_ff_task = session.query(Task).filter(
                Task.task_type == 'firefight',
                Task.drone_id.isnot(None)
            ).order_by(Task.assigned_at.desc()).first()
            
            if last_ff_task:
                last_drone = session.query(Drone).get(last_ff_task.drone_id)
                if last_drone:
                    # Get all firefighter drones ordered by ID
                    all_firefighters = session.query(Drone).filter(
                        Drone.drone_type == DroneType.FIREFIGHTER
                    ).order_by(Drone.drone_id).all()
                    
                    # Find index of last assigned drone
                    for i, drone in enumerate(all_firefighters):
                        if drone.drone_id == last_drone.drone_id:
                            self.last_assigned_firefighter_index = i
                            break
                    else:
                        self.last_assigned_firefighter_index = -1
                else:
                    self.last_assigned_firefighter_index = -1
            else:
                self.last_assigned_firefighter_index = -1
                
        finally:
            self.db_manager.close_session(session)
    
    def create_scout_task(self, flight_area: Dict, priority: str = 'medium') -> Dict:
        """Create a new scouting task with flight area coordinates"""
        session = self.db_manager.get_session()
        
        try:
            self.task_counter += 1
            task_id = f"TASK-{datetime.now().strftime('%Y%m%d')}-{self.task_counter:04d}"
            
            task = Task(
                task_id=task_id,
                task_type='scout',
                state=TaskState.CREATED,
                priority=priority,
                corner_a_lat=flight_area['corner_a']['latitude'],
                corner_a_lon=flight_area['corner_a']['longitude'],
                corner_b_lat=flight_area['corner_b']['latitude'],
                corner_b_lon=flight_area['corner_b']['longitude'],
                corner_c_lat=flight_area['corner_c']['latitude'],
                corner_c_lon=flight_area['corner_c']['longitude'],
                corner_d_lat=flight_area['corner_d']['latitude'],
                corner_d_lon=flight_area['corner_d']['longitude'],
                cruise_altitude_m=self.config['drone_pool']['scouter_drones']['cruise_altitude_m'],
                cruise_speed_ms=self.config['drone_pool']['scouter_drones']['cruise_speed_ms'],
                pattern='serpentine'
            )
            
            session.add(task)
            session.commit()
            
            # Return task data as dict to avoid session issues
            task_data = {
                'task_id': task.task_id,
                'corner_a_lat': task.corner_a_lat,
                'corner_a_lon': task.corner_a_lon,
                'corner_b_lat': task.corner_b_lat,
                'corner_b_lon': task.corner_b_lon,
                'corner_c_lat': task.corner_c_lat,
                'corner_c_lon': task.corner_c_lon,
                'corner_d_lat': task.corner_d_lat,
                'corner_d_lon': task.corner_d_lon,
                'cruise_altitude_m': task.cruise_altitude_m,
                'cruise_speed_ms': task.cruise_speed_ms,
                'pattern': task.pattern
            }
            
            print(f"[OK] Created task: {task_id}")
            return task_data
            
        except Exception as e:
            session.rollback()
            print(f"Error creating task: {e}")
            raise
        finally:
            self.db_manager.close_session(session)
    
    def assign_task_to_drone(self, task_id: str) -> Optional[Dict]:
        """Assign task to available drone using round-robin with battery/capability checks"""
        session = self.db_manager.get_session()
        
        try:
            task = session.query(Task).filter_by(task_id=task_id).first()
            if not task:
                print(f"Task {task_id} not found")
                return None
            
            # Get minimum battery requirement
            min_battery = self.config['mission_planning']['assignment']['min_battery_percent']
            
            # Determine drone type needed
            drone_type = DroneType.SCOUTER if task.task_type == 'scout' else DroneType.FIREFIGHTER
            
            # Find available drones that meet requirements
            available_drones = session.query(Drone).filter(
                Drone.drone_type == drone_type,
                Drone.state == DroneState.IDLE,
                Drone.battery_percent >= min_battery
            ).order_by(Drone.drone_id).all()  # Order by ID for consistent round-robin
            
            if not available_drones:
                print(f"No available {drone_type.value} drones")
                return None
            
            # Round-robin selection with battery check
            selected_drone = None
            num_drones = len(available_drones)
            
            # Get the appropriate round-robin index
            if drone_type == DroneType.SCOUTER:
                last_index = self.last_assigned_scouter_index
            else:
                last_index = self.last_assigned_firefighter_index
            
            # Try to find next drone in round-robin order
            for i in range(num_drones):
                next_index = (last_index + 1 + i) % num_drones
                candidate = available_drones[next_index]
                
                # Check if drone meets mission requirements
                if candidate.battery_percent >= min_battery:
                    selected_drone = candidate
                    
                    # Update round-robin index
                    if drone_type == DroneType.SCOUTER:
                        self.last_assigned_scouter_index = next_index
                    else:
                        self.last_assigned_firefighter_index = next_index
                    break
            
            # Fallback: if no drone found in round-robin, pick highest battery
            if not selected_drone:
                selected_drone = max(available_drones, key=lambda d: d.battery_percent)
                print(f"[WARN]  Round-robin failed, using highest battery drone")
            
            # Assign task
            task.drone_id = selected_drone.id
            task.state = TaskState.ASSIGNED
            task.assigned_at = datetime.utcnow()
            
            selected_drone.state = DroneState.ASSIGNED
            
            session.commit()
            
            # Return drone data as dict to avoid session issues
            drone_data = {
                'drone_id': selected_drone.drone_id,
                'drone_type': selected_drone.drone_type.value,
                'battery_percent': selected_drone.battery_percent
            }
            
            print(f"[OK] Assigned task {task_id} to drone {selected_drone.drone_id}")
            return drone_data
            
        except Exception as e:
            session.rollback()
            print(f"Error assigning task: {e}")
            raise
        finally:
            self.db_manager.close_session(session)
    
    def start_task_execution(self, task_id: str):
        """Mark task as executing"""
        session = self.db_manager.get_session()
        
        try:
            task = session.query(Task).filter_by(task_id=task_id).first()
            if task:
                task.state = TaskState.EXECUTING
                task.started_at = datetime.utcnow()
                
                drone = session.query(Drone).get(task.drone_id)
                if drone:
                    drone.state = DroneState.FLYING
                
                session.commit()
                print(f"[OK] Task {task_id} execution started")
        except Exception as e:
            session.rollback()
            print(f"Error starting task: {e}")
            raise
        finally:
            self.db_manager.close_session(session)
    
    def complete_task(self, task_id: str, hotspots_detected: int = 0, data_path: str = None):
        """Mark task as completed"""
        session = self.db_manager.get_session()
        
        try:
            task = session.query(Task).filter_by(task_id=task_id).first()
            if task:
                task.state = TaskState.COMPLETED
                task.completed_at = datetime.utcnow()
                task.hotspots_detected = hotspots_detected
                task.data_path = data_path
                
                drone = session.query(Drone).get(task.drone_id)
                if drone:
                    drone.state = DroneState.IDLE
                    drone.total_flights += 1
                    
                    # Calculate flight time
                    if task.started_at:
                        flight_time = (task.completed_at - task.started_at).total_seconds() / 60
                        drone.total_flight_time_min += flight_time
                        
                        # Estimate battery usage (rough estimate)
                        battery_used = (flight_time / drone.max_flight_time_min) * 100
                        drone.battery_percent = max(0, drone.battery_percent - battery_used)
                
                session.commit()
                print(f"[OK] Task {task_id} completed - {hotspots_detected} hotspots detected")
        except Exception as e:
            session.rollback()
            print(f"Error completing task: {e}")
            raise
        finally:
            self.db_manager.close_session(session)
    
    def complete_suppression_task(self, task_id: str, data_path: str = None):
        """Mark suppression task as completed and update fire status"""
        session = self.db_manager.get_session()
        
        try:
            task = session.query(Task).filter_by(task_id=task_id).first()
            if task:
                task.state = TaskState.COMPLETED
                task.completed_at = datetime.utcnow()
                task.fires_suppressed = 1
                task.data_path = data_path
                
                # Update drone state
                drone = session.query(Drone).get(task.drone_id)
                if drone:
                    drone.state = DroneState.IDLE
                    drone.total_flights += 1
                    
                    # Calculate flight time
                    if task.started_at:
                        flight_time = (task.completed_at - task.started_at).total_seconds() / 60
                        drone.total_flight_time_min += flight_time
                        battery_used = (flight_time / drone.max_flight_time_min) * 100
                        drone.battery_percent = max(0, drone.battery_percent - battery_used)
                
                # Update fire detection status to suppressed
                detections = session.query(FireDetection).filter_by(
                    dispatched_fd_id=task.drone_id,
                    status='dispatched'
                ).all()
                
                for detection in detections:
                    detection.status = 'suppressed'
                    detection.suppressed_at = datetime.utcnow()
                
                session.commit()
                print(f"[OK] Suppression task {task_id} completed - fire suppressed")
        except Exception as e:
            session.rollback()
            print(f"Error completing suppression task: {e}")
            raise
        finally:
            self.db_manager.close_session(session)
    
    def register_fire_detection(self, task_id: str, drone_id: str, 
                                latitude: float, longitude: float,
                                temperature_c: float, confidence: float,
                                detection_method: str = 'thermal') -> FireDetection:
        """Register a fire detection event"""
        session = self.db_manager.get_session()
        
        try:
            self.detection_counter += 1
            detection_id = f"FIRE-{datetime.now().strftime('%Y%m%d')}-{self.detection_counter:04d}"
            
            # Get task and drone
            task = session.query(Task).filter_by(task_id=task_id).first()
            drone = session.query(Drone).filter_by(drone_id=drone_id).first()
            
            detection = FireDetection(
                detection_id=detection_id,
                latitude=latitude,
                longitude=longitude,
                temperature_c=temperature_c,
                confidence=confidence,
                detection_method=detection_method,
                task_id=task.id if task else None,
                drone_id=drone.id if drone else None,
                status='detected'
            )
            
            session.add(detection)
            session.commit()
            
            print(f"[FIRE] Fire detected: {detection_id} at ({latitude:.6f}, {longitude:.6f}) - {temperature_c}°C")
            
            # Auto-dispatch FD if configured
            alerts_config = self.config.get('fire_detection', {}).get('alerts', {})
            immediate_dispatch = alerts_config.get('immediate_dispatch', True)
            min_confidence = alerts_config.get('min_confidence', 0.7)
            
            if immediate_dispatch and confidence >= min_confidence:
                self.dispatch_firefighter_drone(detection_id)
            
            return detection
            
        except Exception as e:
            session.rollback()
            print(f"Error registering detection: {e}")
            raise
        finally:
            self.db_manager.close_session(session)
    
    def dispatch_firefighter_drone(self, detection_id: str) -> Optional[str]:
        """Dispatch a firefighter drone to a fire location"""
        session = self.db_manager.get_session()
        
        try:
            detection = session.query(FireDetection).filter_by(detection_id=detection_id).first()
            if not detection:
                return None
            
            # Find available FD drone
            fd_drone = session.query(Drone).filter(
                Drone.drone_type == DroneType.FIREFIGHTER,
                Drone.state == DroneState.IDLE,
                Drone.battery_percent >= 30
            ).first()
            
            if not fd_drone:
                print("[WARN]  No available firefighter drones")
                return None
            
            # Create suppression task
            self.task_counter += 1
            task_id = f"TASK-{datetime.now().strftime('%Y%m%d')}-{self.task_counter:04d}"
            
            # Create small area around detection point
            offset = 0.0001  # ~10 meters
            task = Task(
                task_id=task_id,
                task_type='suppress',
                state=TaskState.ASSIGNED,
                priority='high',
                corner_a_lat=detection.latitude + offset,
                corner_a_lon=detection.longitude - offset,
                corner_b_lat=detection.latitude + offset,
                corner_b_lon=detection.longitude + offset,
                corner_c_lat=detection.latitude - offset,
                corner_c_lon=detection.longitude + offset,
                corner_d_lat=detection.latitude - offset,
                corner_d_lon=detection.longitude - offset,
                cruise_altitude_m=self.config['drone_pool']['firefighter_drones']['cruise_altitude_m'],
                cruise_speed_ms=self.config['drone_pool']['firefighter_drones']['cruise_speed_ms'],
                drone_id=fd_drone.id,
                assigned_at=datetime.utcnow()
            )
            
            session.add(task)
            
            # Update detection
            detection.status = 'dispatched'
            detection.dispatched_fd_id = fd_drone.id
            detection.dispatched_at = datetime.utcnow()
            
            # Update drone state
            fd_drone.state = DroneState.ASSIGNED
            
            session.commit()
            
            print(f"[DRONE] Dispatched {fd_drone.drone_id} to fire location (Task: {task_id})")
            return task_id
            
        except Exception as e:
            session.rollback()
            print(f"Error dispatching FD: {e}")
            raise
        finally:
            self.db_manager.close_session(session)
    
    def get_system_status(self) -> Dict:
        """Get current system status"""
        session = self.db_manager.get_session()
        
        try:
            drones = session.query(Drone).all()
            tasks = session.query(Task).all()
            detections = session.query(FireDetection).all()
            
            status = {
                'drones': {
                    'total': len(drones),
                    'idle': len([d for d in drones if d.state == DroneState.IDLE]),
                    'flying': len([d for d in drones if d.state == DroneState.FLYING]),
                    'charging': len([d for d in drones if d.state == DroneState.CHARGING]),
                    'scouters': len([d for d in drones if d.drone_type == DroneType.SCOUTER]),
                    'firefighters': len([d for d in drones if d.drone_type == DroneType.FIREFIGHTER])
                },
                'tasks': {
                    'total': len(tasks),
                    'created': len([t for t in tasks if t.state == TaskState.CREATED]),
                    'assigned': len([t for t in tasks if t.state == TaskState.ASSIGNED]),
                    'executing': len([t for t in tasks if t.state == TaskState.EXECUTING]),
                    'completed': len([t for t in tasks if t.state == TaskState.COMPLETED])
                },
                'detections': {
                    'total': len(detections),
                    'detected': len([d for d in detections if d.status == 'detected']),
                    'dispatched': len([d for d in detections if d.status == 'dispatched']),
                    'suppressed': len([d for d in detections if d.status == 'suppressed'])
                }
            }
            
            return status
            
        finally:
            self.db_manager.close_session(session)
    
    def cancel_task(self, task_id: str) -> bool:
        """Cancel a task and return drone to IDLE"""
        session = self.db_manager.get_session()
        
        try:
            task = session.query(Task).filter_by(task_id=task_id).first()
            if not task:
                return False
            
            # Update task state
            task.state = TaskState.CANCELLED
            task.completed_at = datetime.now()
            
            # Return drone to IDLE if assigned
            if task.drone_id:
                drone = session.query(Drone).get(task.drone_id)
                if drone:
                    drone.state = DroneState.IDLE
            
            session.commit()
            return True
            
        except Exception as e:
            session.rollback()
            print(f"Error cancelling task: {e}")
            return False
        finally:
            self.db_manager.close_session(session)
    
    def return_drone_to_station(self, drone_id: str) -> bool:
        """Send RTS (Return to Station) command to drone"""
        session = self.db_manager.get_session()
        
        try:
            drone = session.query(Drone).filter_by(drone_id=drone_id).first()
            if not drone:
                return False
            
            # Find any active task for this drone
            active_task = session.query(Task).filter(
                Task.drone_id == drone.id,
                Task.state.in_([TaskState.ASSIGNED, TaskState.EXECUTING])
            ).first()
            
            # Cancel active task if exists
            if active_task:
                active_task.state = TaskState.CANCELLED
                active_task.completed_at = datetime.now()
            
            # Return drone to IDLE
            drone.state = DroneState.IDLE
            
            session.commit()
            print(f"[OK] RTS command sent to {drone_id} - returning to station")
            return True
            
        except Exception as e:
            session.rollback()
            print(f"Error sending RTS to drone: {e}")
            return False
        finally:
            self.db_manager.close_session(session)
    
    def reset_stale_tasks(self, max_age_hours: int = 24) -> int:
        """Reset stale executing tasks to cancelled state"""
        session = self.db_manager.get_session()
        
        try:
            cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
            
            # Find stale executing tasks (with or without started_at timestamp)
            stale_tasks = session.query(Task).filter(
                Task.state == TaskState.EXECUTING,
                (Task.started_at < cutoff_time) | (Task.started_at == None)
            ).all()
            
            count = 0
            for task in stale_tasks:
                task.state = TaskState.CANCELLED
                task.completed_at = datetime.now()
                
                # Return drone to IDLE
                if task.drone_id:
                    drone = session.query(Drone).get(task.drone_id)
                    if drone:
                        drone.state = DroneState.IDLE
                
                count += 1
            
            session.commit()
            return count
            
        except Exception as e:
            session.rollback()
            print(f"Error resetting stale tasks: {e}")
            return 0
        finally:
            self.db_manager.close_session(session)
