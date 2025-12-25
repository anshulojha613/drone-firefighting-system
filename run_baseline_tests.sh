#!/bin/bash

echo "========================================"
echo "DFS BASELINE TEST SUITE"
echo "========================================"
echo ""

# Use venv Python
PYTHON="./venv/bin/python"

# Test 1: System Initialization
echo "Test 1: System Initialization"
$PYTHON main.py --help > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "[PASS]"
else
    echo "[FAIL]"
fi
echo ""

# Test 2: Clean database
echo "Test 2: Clean Database"
$PYTHON tests.py --clean
echo ""

# Test 3: Demo Mission
echo "Test 3: Demo Mission"
$PYTHON main.py --demo --quiet
if [ $? -eq 0 ]; then
    echo "[PASS]"
else
    echo "[FAIL]"
fi
echo ""

# Test 4: Batch Mission (validate only - needs config/mission_areas.yaml)
echo "Test 4: Batch Mission"
if [ -f "config/mission_areas.yaml" ]; then
    $PYTHON batch_mission.py --validate-only
    if [ $? -eq 0 ]; then
        echo "[PASS]"
    else
        echo "[FAIL]"
    fi
else
    echo "[SKIP] (no config/mission_areas.yaml)"
fi
echo ""

# Test 5: Database Check
echo "Test 5: Database Integrity"
TASK_COUNT=$(sqlite3 database/dfs.db "SELECT COUNT(*) FROM tasks;")
DRONE_COUNT=$(sqlite3 database/dfs.db "SELECT COUNT(*) FROM drones;")
echo "Tasks: $TASK_COUNT"
echo "Drones: $DRONE_COUNT"

if [ $DRONE_COUNT -eq 8 ] && [ $TASK_COUNT -gt 0 ]; then
    echo "[PASS]"
else
    echo "[FAIL]"
fi
echo ""

# Test 6: Data Validation
echo "Test 6: Data Files"
DATA_DIRS=$(ls -d data/SD-*_*/ 2>/dev/null | wc -l)
echo "Data directories: $DATA_DIRS"

if [ $DATA_DIRS -gt 0 ]; then
    echo "[PASS]"
else
    echo "[FAIL]"
fi
echo ""

echo "========================================"
echo "BASELINE TESTS COMPLETE"
echo "========================================"
echo ""
echo "Next: Review results and run dashboard test manually"
echo "Command: python main.py --dashboard --quiet"
