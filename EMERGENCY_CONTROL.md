# Emergency Control Guide

## Overview

During mission execution, you have multiple ways to send emergency commands to your drone:

1. **Same Terminal (Ctrl+C)** - Quick abort from the mission terminal
2. **Separate Terminal** - Full emergency control while mission runs

## Safety Levels

### 🟢 ABORT (Safest)
- Stops mission execution
- Returns to launch position
- Safe for all situations

### 🟡 RTL (Return to Launch)
- Returns drone to home position
- Maintains altitude during return
- Safe controlled return

### 🟠 LAND (Emergency)
- Lands at current position
- Use if RTL path is blocked
- Controlled descent

### 🔴 KILL (DANGEROUS!)
- **Immediate motor stop**
- **Drone will fall from sky**
- Only use if fire/collision imminent
- Requires confirmation

---

## Method 1: Same Terminal (Ctrl+C)

While mission is running, press **Ctrl+C** to abort:

```bash
python main.py --demo --network --drone-id SD-001

# Press Ctrl+C during execution
^C
[WARN] ⚠️  Mission abort requested by user
[ABORT] Sending abort command to drone...
[OK] Abort command sent - drone returning to launch
```

**What happens:**
- Mission stops immediately
- Drone returns to launch
- Safe and quick

---

## Method 2: Separate Terminal (Full Control)

### Interactive Mode (Recommended)

Open a **new terminal** while mission is running:

```bash
python emergency_control.py --ip 10.10.8.1
```

You'll see an interactive menu:

```
======================================================================
  🚨 EMERGENCY CONTROL - DRONE OPERATIONS
======================================================================
  Drone: 10.10.8.1:5000
======================================================================

[OK] Connected to drone
   State: EXECUTING
   Mode: hardware
   Task: TASK-20251226-0003

----------------------------------------------------------------------
Emergency Commands:
  1. ABORT    - Abort mission and return to launch
  2. RTL      - Return to launch (safe return home)
  3. LAND     - Emergency land at current position
  4. KILL     - Kill switch (immediate motor stop - DANGEROUS!)
  5. STATUS   - Check drone status
  6. EXIT     - Exit emergency control
----------------------------------------------------------------------

Enter command (1-6):
```

### Quick Commands

For immediate action without menu:

```bash
# Abort mission
python emergency_control.py --ip 10.10.8.1 --abort

# Return to launch
python emergency_control.py --ip 10.10.8.1 --rtl

# Emergency land
python emergency_control.py --ip 10.10.8.1 --land

# Check status
python emergency_control.py --ip 10.10.8.1 --status

# Kill switch (requires confirmation)
python emergency_control.py --ip 10.10.8.1 --kill
```

---

## Complete Workflow Example

### Terminal 1: Start Mission
```bash
# On Mac (Ground Station)
python main.py --demo --network --drone-id SD-001

[COMM] Running in NETWORK mode (Ground Station -> WiFi -> Drone)
[TARGET] Target drone: SD-001
...
[WAIT] Waiting for mission completion...
[TIP] Press Ctrl+C to abort mission and RTL
   Status: EXECUTING
   Status: EXECUTING
```

### Terminal 2: Emergency Control (if needed)
```bash
# Open new terminal on Mac
python emergency_control.py --ip 10.10.8.1

# Select option:
# 1 - ABORT (safest)
# 2 - RTL
# 3 - LAND
# 4 - KILL (dangerous!)
```

---

## API Endpoints

The drone agent exposes these emergency endpoints:

| Endpoint | Method | Action | Safety |
|----------|--------|--------|--------|
| `/api/mission/abort` | POST | Abort mission + RTL | 🟢 Safe |
| `/api/rtl` | POST | Return to launch | 🟡 Safe |
| `/api/land` | POST | Emergency land | 🟠 Caution |
| `/api/kill` | POST | Kill motors | 🔴 Dangerous |
| `/api/status` | GET | Get drone status | ℹ️ Info |

### Manual API Calls

You can also use `curl` for emergency commands:

```bash
# Abort mission
curl -X POST http://10.10.8.1:5000/api/mission/abort

# Return to launch
curl -X POST http://10.10.8.1:5000/api/rtl

# Emergency land
curl -X POST http://10.10.8.1:5000/api/land

# Check status
curl http://10.10.8.1:5000/api/status

# Kill switch
curl -X POST http://10.10.8.1:5000/api/kill
```

---

## Testing Without Propellers

Since you're testing without propellers attached:

1. **Start mission normally:**
   ```bash
   python main.py --demo --network --drone-id SD-001
   ```

2. **In separate terminal, test emergency commands:**
   ```bash
   # Test abort
   python emergency_control.py --ip 10.10.8.1 --abort
   
   # Check if it worked
   python emergency_control.py --ip 10.10.8.1 --status
   ```

3. **Watch drone agent logs on Pi** to see commands received

---

## Troubleshooting

### "Cannot connect to drone"
- Check drone agent is running on Pi
- Verify IP address (10.10.8.1)
- Check WiFi connection

### "Abort command failed"
- Drone may have already completed mission
- Check status first: `--status`
- Try RTL or LAND instead

### Mission keeps running after abort
- Check drone agent logs on Pi
- Manually SSH to Pi and check process
- Use kill switch as last resort

---

## Safety Recommendations

1. **Always test without propellers first**
2. **Keep emergency control terminal ready**
3. **Know your abort options:**
   - First try: Ctrl+C in mission terminal
   - Second try: ABORT from emergency control
   - Third try: RTL or LAND
   - Last resort: KILL (only if necessary)

4. **Monitor drone agent logs** on Pi during testing
5. **Have physical access** to Pi for manual shutdown

---

## Next Steps

Deploy updated code to Pi:
```bash
./deploy_to_pi.sh
```

Then restart drone agent on Pi:
```bash
ssh anshul@10.10.8.1
cd ~/drone-firefighting-system
source venv/bin/activate
python -m network.drone_agent --drone-id SD-001
```

Now you have full emergency control! 🚁
