echo "[INFO] Starting quick demo..."
python tests.py --clean
python main.py --demo
python batch_mission.py --config config/batch_mission_areas_sequential.yaml --mode sequential --mission-delay 2
python batch_mission.py --config config/batch_mission_areas_parallel.yaml --mode parallel --workers 2 --mission-delay 1
echo "[INFO] Demo completed!"
