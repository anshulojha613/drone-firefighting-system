"""
Network Message Protocol
Defines standardized JSON messages for ground station <-> drone communication
"""

from enum import Enum
from typing import Dict, Any, Optional
from datetime import datetime
import json


class MessageType(Enum):
    """Message types for communication"""
    # Ground Station -> Drone
    MISSION_ASSIGN = "mission_assign"
    MISSION_START = "mission_start"
    MISSION_ABORT = "mission_abort"
    RTL_COMMAND = "rtl_command"
    STATUS_REQUEST = "status_request"
    HEARTBEAT = "heartbeat"
    
    # Drone -> Ground Station
    STATUS_REPORT = "status_report"
    TELEMETRY = "telemetry"
    HOTSPOT_ALERT = "hotspot_alert"
    MISSION_COMPLETE = "mission_complete"
    MISSION_FAILED = "mission_failed"
    HEARTBEAT_ACK = "heartbeat_ack"


class Message:
    """Base message class"""
    
    def __init__(self, msg_type: MessageType, sender_id: str, data: Dict[str, Any] = None):
        self.msg_type = msg_type
        self.sender_id = sender_id
        self.timestamp = datetime.now().isoformat()
        self.data = data or {}
    
    def to_dict(self) -> Dict:
        """Convert message to dictionary"""
        return {
            'type': self.msg_type.value,
            'sender_id': self.sender_id,
            'timestamp': self.timestamp,
            'data': self.data
        }
    
    def to_json(self) -> str:
        """Convert message to JSON string"""
        return json.dumps(self.to_dict())
    
    @staticmethod
    def from_dict(msg_dict: Dict) -> 'Message':
        """Create message from dictionary"""
        msg_type = MessageType(msg_dict['type'])
        sender_id = msg_dict['sender_id']
        data = msg_dict.get('data', {})
        
        msg = Message(msg_type, sender_id, data)
        msg.timestamp = msg_dict['timestamp']
        return msg
    
    @staticmethod
    def from_json(json_str: str) -> 'Message':
        """Create message from JSON string"""
        return Message.from_dict(json.loads(json_str))


class MissionAssignMessage(Message):
    """Mission assignment message from ground station to drone"""
    
    def __init__(self, sender_id: str, task_id: str, mission_config: Dict):
        data = {
            'task_id': task_id,
            'mission_config': mission_config
        }
        super().__init__(MessageType.MISSION_ASSIGN, sender_id, data)


class StatusReportMessage(Message):
    """Status report from drone to ground station"""
    
    def __init__(self, sender_id: str, status: Dict):
        """
        status should contain:
        - state: str (IDLE, FLYING, EXECUTING, etc.)
        - battery: float (0-100)
        - position: dict with lat, lon, alt
        - mode: str (DEMO, HARDWARE)
        - armed: bool
        - connected: bool
        """
        super().__init__(MessageType.STATUS_REPORT, sender_id, status)


class TelemetryMessage(Message):
    """Telemetry data from drone to ground station"""
    
    def __init__(self, sender_id: str, telemetry: Dict):
        """
        telemetry should contain:
        - position: dict with lat, lon, alt
        - speed: float
        - heading: float
        - battery: float
        - timestamp: str
        """
        super().__init__(MessageType.TELEMETRY, sender_id, telemetry)


class HotspotAlertMessage(Message):
    """Hotspot detection alert from drone to ground station"""
    
    def __init__(self, sender_id: str, hotspot: Dict):
        """
        hotspot should contain:
        - latitude: float
        - longitude: float
        - altitude: float
        - temperature_c: float
        - confidence: float
        - timestamp: str
        """
        super().__init__(MessageType.HOTSPOT_ALERT, sender_id, hotspot)


class MissionCompleteMessage(Message):
    """Mission completion notification from drone to ground station"""
    
    def __init__(self, sender_id: str, task_id: str, result: Dict):
        """
        result should contain:
        - hotspots_detected: int
        - data_path: str
        - duration_sec: float
        - success: bool
        """
        data = {
            'task_id': task_id,
            'result': result
        }
        super().__init__(MessageType.MISSION_COMPLETE, sender_id, data)


class RTLCommandMessage(Message):
    """Return to launch command from ground station to drone"""
    
    def __init__(self, sender_id: str, reason: str = "Manual RTL"):
        data = {'reason': reason}
        super().__init__(MessageType.RTL_COMMAND, sender_id, data)


class HeartbeatMessage(Message):
    """Heartbeat message for connectivity check"""
    
    def __init__(self, sender_id: str):
        super().__init__(MessageType.HEARTBEAT, sender_id, {})


class HeartbeatAckMessage(Message):
    """Heartbeat acknowledgment"""
    
    def __init__(self, sender_id: str):
        super().__init__(MessageType.HEARTBEAT_ACK, sender_id, {})


def create_message(msg_type: MessageType, sender_id: str, **kwargs) -> Message:
    """
    Factory function to create appropriate message type
    """
    if msg_type == MessageType.MISSION_ASSIGN:
        return MissionAssignMessage(sender_id, kwargs['task_id'], kwargs['mission_config'])
    
    elif msg_type == MessageType.STATUS_REPORT:
        return StatusReportMessage(sender_id, kwargs['status'])
    
    elif msg_type == MessageType.TELEMETRY:
        return TelemetryMessage(sender_id, kwargs['telemetry'])
    
    elif msg_type == MessageType.HOTSPOT_ALERT:
        return HotspotAlertMessage(sender_id, kwargs['hotspot'])
    
    elif msg_type == MessageType.MISSION_COMPLETE:
        return MissionCompleteMessage(sender_id, kwargs['task_id'], kwargs['result'])
    
    elif msg_type == MessageType.RTL_COMMAND:
        return RTLCommandMessage(sender_id, kwargs.get('reason', 'Manual RTL'))
    
    elif msg_type == MessageType.HEARTBEAT:
        return HeartbeatMessage(sender_id)
    
    elif msg_type == MessageType.HEARTBEAT_ACK:
        return HeartbeatAckMessage(sender_id)
    
    else:
        return Message(msg_type, sender_id, kwargs)
