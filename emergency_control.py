#!/usr/bin/env python3
"""
Emergency Control Script for Drone Operations
Run this in a separate terminal while mission is executing to send emergency commands
"""

import requests
import argparse
import sys
from typing import Optional

class EmergencyControl:
    """Send emergency commands to drone during mission execution"""
    
    def __init__(self, drone_ip: str, drone_port: int = 5000):
        self.base_url = f"http://{drone_ip}:{drone_port}"
        self.drone_ip = drone_ip
        self.drone_port = drone_port
    
    def get_status(self) -> Optional[dict]:
        """Get current drone status"""
        try:
            response = requests.get(f"{self.base_url}/api/status", timeout=5)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"[ERROR] Failed to get status: {e}")
            return None
    
    def abort_mission(self) -> bool:
        """Abort current mission and RTL"""
        try:
            print("\n[WARN] Sending ABORT command...")
            response = requests.post(f"{self.base_url}/api/mission/abort", timeout=5)
            if response.status_code == 200:
                result = response.json()
                print(f"[OK] {result.get('message', 'Mission aborted')}")
                return True
            else:
                print(f"[ERROR] Abort failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"[ERROR] Failed to abort: {e}")
            return False
    
    def return_to_launch(self) -> bool:
        """Return to launch position (safe return home)"""
        try:
            print("\n[HOME] Sending RTL command...")
            response = requests.post(f"{self.base_url}/api/rtl", timeout=5)
            if response.status_code == 200:
                result = response.json()
                print(f"[OK] {result.get('message', 'RTL initiated')}")
                return True
            else:
                print(f"[ERROR] RTL failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"[ERROR] Failed to RTL: {e}")
            return False
    
    def land(self) -> bool:
        """Emergency land at current position"""
        try:
            print("\n[LAND] Sending LAND command...")
            response = requests.post(f"{self.base_url}/api/land", timeout=5)
            if response.status_code == 200:
                result = response.json()
                print(f"[OK] {result.get('message', 'Landing initiated')}")
                return True
            else:
                print(f"[ERROR] Land failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"[ERROR] Failed to land: {e}")
            return False
    
    def kill(self) -> bool:
        """KILL SWITCH - Immediate motor stop (DANGEROUS!)"""
        try:
            print("\n[KILL] WARNING: KILL SWITCH - MOTORS WILL STOP IMMEDIATELY!")
            print("[KILL] WARNING: DRONE WILL FALL IF AIRBORNE!")
            confirm = input("[KILL] Type 'KILL' to confirm: ")
            
            if confirm != "KILL":
                print("[KILL] Cancelled")
                return False
            
            response = requests.post(f"{self.base_url}/api/kill", timeout=5)
            if response.status_code == 200:
                result = response.json()
                print(f"[KILL] {result.get('message', 'Motors stopped')}")
                return True
            else:
                print(f"[ERROR] Kill failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"[ERROR] Failed to kill: {e}")
            return False


def interactive_mode(controller: EmergencyControl):
    """Interactive menu for emergency control"""
    print("\n" + "="*70)
    print("  EMERGENCY CONTROL - DRONE OPERATIONS")
    print("="*70)
    print(f"  Drone: {controller.drone_ip}:{controller.drone_port}")
    print("="*70)
    
    # Check connection
    status = controller.get_status()
    if status:
        print(f"\n[OK] Connected to drone")
        print(f"   State: {status.get('state', 'UNKNOWN')}")
        print(f"   Mode: {status.get('mode', 'UNKNOWN')}")
        print(f"   Task: {status.get('current_task', 'None')}")
    else:
        print("\n[WARN] Cannot connect to drone - commands may fail")
    
    while True:
        print("\n" + "-"*70)
        print("Emergency Commands:")
        print("  1. ABORT    - Abort mission and return to launch")
        print("  2. RTL      - Return to launch (safe return home)")
        print("  3. LAND     - Emergency land at current position")
        print("  4. KILL     - Kill switch (immediate motor stop - DANGEROUS!)")
        print("  5. STATUS   - Check drone status")
        print("  6. EXIT     - Exit emergency control")
        print("-"*70)
        
        choice = input("\nEnter command (1-6): ").strip()
        
        if choice == '1':
            controller.abort_mission()
        elif choice == '2':
            controller.return_to_launch()
        elif choice == '3':
            controller.land()
        elif choice == '4':
            controller.kill()
        elif choice == '5':
            status = controller.get_status()
            if status:
                print(f"\n[STATUS] Drone Status:")
                for key, value in status.items():
                    print(f"   {key}: {value}")
            else:
                print("\n[ERROR] Cannot get status")
        elif choice == '6':
            print("\n[EXIT] Exiting emergency control")
            break
        else:
            print("\n[ERROR] Invalid choice")


def main():
    parser = argparse.ArgumentParser(
        description='Emergency Control for Drone Operations',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode (recommended)
  python emergency_control.py --ip 10.10.8.1
  
  # Quick commands
  python emergency_control.py --ip 10.10.8.1 --abort
  python emergency_control.py --ip 10.10.8.1 --rtl
  python emergency_control.py --ip 10.10.8.1 --land
  python emergency_control.py --ip 10.10.8.1 --kill
  python emergency_control.py --ip 10.10.8.1 --status

Safety Notes:
  - ABORT: Safest option - stops mission and returns home
  - RTL: Returns to launch position safely
  - LAND: Lands at current position
  - KILL: DANGEROUS - Stops motors immediately, drone will fall!
        """
    )
    parser.add_argument('--ip', required=True, help='Drone IP address (e.g., 10.10.8.1)')
    parser.add_argument('--port', type=int, default=5000, help='Drone port (default: 5000)')
    parser.add_argument('--abort', action='store_true', help='Abort mission')
    parser.add_argument('--rtl', action='store_true', help='Return to launch')
    parser.add_argument('--land', action='store_true', help='Emergency land')
    parser.add_argument('--kill', action='store_true', help='Kill switch (DANGEROUS!)')
    parser.add_argument('--status', action='store_true', help='Get drone status')
    
    args = parser.parse_args()
    
    controller = EmergencyControl(args.ip, args.port)
    
    # Check if any command flag is set
    if args.abort:
        controller.abort_mission()
    elif args.rtl:
        controller.return_to_launch()
    elif args.land:
        controller.land()
    elif args.kill:
        controller.kill()
    elif args.status:
        status = controller.get_status()
        if status:
            print("\n[STATUS] Drone Status:")
            for key, value in status.items():
                print(f"   {key}: {value}")
        else:
            print("\n[ERROR] Cannot get status")
    else:
        # No command flag - enter interactive mode
        interactive_mode(controller)


if __name__ == '__main__':
    main()
