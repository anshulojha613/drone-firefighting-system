# Logging Guide

## Overview

The DFS uses a centralized logging utility that provides consistent logging across all modules with configurable log levels.

## Log Levels

The system supports five log levels (in order of severity):

1. **DEBUG** - Detailed diagnostic information
2. **INFO** - General informational messages (default)
3. **WARNING** - Warning messages for potentially problematic situations
4. **ERROR** - Error messages for failures
5. **CRITICAL** - Critical errors that may cause system failure

## Usage

### Command-Line Configuration

Set the log level when starting the system:

```bash
# Default (INFO level)
python main.py --demo

# Debug level for detailed diagnostics
python main.py --demo --log-level DEBUG

# Warning level to see only warnings and errors
python main.py --demo --log-level WARNING

# Save logs to file
python main.py --demo --log-file logs/dfs_session.log

# Combined: DEBUG level with file logging
python main.py --demo --log-level DEBUG --log-file logs/debug.log
```

### Batch Mission Logging

```bash
# Default INFO level
python batch_mission.py

# Debug mode for troubleshooting
python batch_mission.py --log-level DEBUG

# Quiet mode (WARNING and above only)
python batch_mission.py --log-level WARNING

# Save batch execution logs
python batch_mission.py --log-file logs/batch_mission.log
```

### Dashboard Logging

```bash
# Normal dashboard with INFO logging
python main.py --dashboard

# Debug mode for dashboard troubleshooting
python main.py --dashboard --log-level DEBUG

# Quiet mode (suppress most output)
python main.py --dashboard --log-level ERROR --quiet
```

## Using Logger in Code

### Import the Logger

```python
from utils.logger import get_logger

logger = get_logger()
```

### Log Messages

```python
# Debug messages (only shown when log level is DEBUG)
logger.debug("[DEBUG] Detailed diagnostic information")

# Info messages (default level)
logger.info("[OK] Operation completed successfully")
logger.info("[LOAD] Loading configuration...")

# Warning messages
logger.warning("[WARN] Battery level below 30%")

# Error messages
logger.error("[FAIL] Failed to connect to drone")

# Critical messages
logger.critical("[CRITICAL] System shutdown required")
```

### Setup Logging Programmatically

```python
from utils.logger import setup_logging

# Setup with custom level
setup_logging(level='DEBUG')

# Setup with file logging
setup_logging(level='INFO', log_file='logs/custom.log')
```

## Log Message Format

### Console Output
```
[OK] Task TASK-20251223-0001 created
[WARN] No GPS file found for TASK-20251223-0002
[FAIL] Error loading GPS data: File not found
```

### File Output
```
2025-12-23 16:51:23 - DFS - INFO - [OK] Task TASK-20251223-0001 created
2025-12-23 16:51:24 - DFS - WARNING - [WARN] No GPS file found for TASK-20251223-0002
2025-12-23 16:51:25 - DFS - ERROR - [FAIL] Error loading GPS data: File not found
```

## Configuration File

The logging configuration in `config/dfs_config.yaml`:

```yaml
logging:
  level: INFO
  file: logs/dfs.log
  format: '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
  max_bytes: 10485760  # 10MB
  backup_count: 5
```

## Best Practices

### Use Appropriate Log Levels

- **DEBUG**: Variable values, function entry/exit, detailed state
- **INFO**: Normal operations, task creation, mission completion
- **WARNING**: Recoverable issues, fallback actions, deprecated usage
- **ERROR**: Failed operations, exceptions, data errors
- **CRITICAL**: System failures, unrecoverable errors

### Message Prefixes

Use consistent prefixes for clarity:

```python
logger.info("[OK] Success message")
logger.info("[LOAD] Loading resource")
logger.info("[SAVE] Saving data")
logger.warning("[WARN] Warning message")
logger.error("[FAIL] Error message")
logger.info("[DRONE] Drone-related message")
logger.info("[FIRE] Fire detection message")
logger.info("[COMM] Communication message")
```

### Avoid Sensitive Data

Never log sensitive information:
- API keys
- Passwords
- Personal identification
- GPS coordinates of private locations (use general area instead)

## Examples

### Module Initialization

```python
from utils.logger import get_logger

logger = get_logger()

class MyModule:
    def __init__(self):
        logger.info("[INIT] Initializing MyModule")
        try:
            self.setup()
            logger.info("[OK] MyModule initialized successfully")
        except Exception as e:
            logger.error(f"[FAIL] MyModule initialization failed: {e}")
            raise
```

### Task Execution

```python
logger.info(f"[START] Executing task {task_id}")
try:
    result = execute_mission()
    logger.info(f"[OK] Task {task_id} completed - {result['hotspots']} hotspots detected")
except Exception as e:
    logger.error(f"[FAIL] Task {task_id} failed: {e}")
```

### Debugging

```python
logger.debug(f"[DEBUG] Processing waypoint {i}/{total}")
logger.debug(f"[DEBUG] GPS coordinates: lat={lat}, lon={lon}")
logger.debug(f"[DEBUG] Battery level: {battery}%")
```

## Troubleshooting

### No Log Output

Check that the log level allows your messages:
```bash
# If using WARNING level, INFO messages won't show
python main.py --demo --log-level WARNING  # Won't show INFO
python main.py --demo --log-level INFO     # Will show INFO
```

### Log File Not Created

Ensure the logs directory exists:
```bash
mkdir -p logs
python main.py --demo --log-file logs/dfs.log
```

### Too Much Output

Increase the log level:
```bash
# Only show warnings and errors
python main.py --demo --log-level WARNING
```

### Need More Detail

Decrease the log level:
```bash
# Show all debug information
python main.py --demo --log-level DEBUG
```
