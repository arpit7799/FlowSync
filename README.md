# FlowSync

# FlowSync

### An IoT-Based Adaptive Traffic Signal and Emergency Vehicle Priority System Using Edge AI

FlowSync is a software-based intelligent traffic management system designed to reduce urban congestion and improve emergency vehicle response times using adaptive traffic control, edge AI, IoT communication and multi-intersection simulation.

## Project Objectives

- Simulate four interconnected traffic intersections.
- Estimate traffic density and congestion.
- Adapt traffic signal timings dynamically.
- Detect and prioritize emergency vehicles.
- Coordinate green corridors across intersections.
- Demonstrate IoT communication through MQTT and ESP32 simulation.
- Provide a real-time traffic management dashboard.
- Evaluate adaptive control against fixed-time traffic control.

## Core Technologies

| Layer | Technologies |
|---|---|
| Traffic simulation | SUMO, TraCI |
| Computer vision | Python, OpenCV, YOLO |
| Edge inference | ONNX Runtime |
| Traffic intelligence | Python |
| IoT communication | MQTT, Mosquitto, Wokwi |
| Backend | FastAPI, SQLAlchemy |
| Database | PostgreSQL |
| Frontend | Next.js, React, TypeScript |
| Visualization | Recharts, Leaflet |
| Testing | Pytest |

## Architecture

- [System Architecture](docs/architecture/SYSTEM_ARCHITECTURE.md)
- [Communication Contracts](docs/architecture/COMMUNICATION_CONTRACTS.md)
- [MQTT Specification](docs/architecture/MQTT_SPECIFICATION.md)

## Project Structure

- `simulation/`
- `edge_ai/`
- `traffic_intelligence/`
- `iot/`
- `backend/`
- `frontend/`
- `tests/`
- `docs/`
- `scripts/`
- `data/`

## Development Environment

- Platform: Apple Silicon macOS
- Python: 3.12
- Virtual environment: `flowsync_env`

Activate the environment:

```bash
source flowsync_env/bin/activate
```

All Python dependencies will be installed inside this environment. Frontend dependencies will be managed separately using npm.

## Software-Only Implementation

- SUMO simulates road networks, vehicles and traffic lights.
- Wokwi simulates ESP32-based IoT controllers.
- Raspberry Pi compatibility will be evaluated using software and resource benchmarks.
- No physical traffic hardware is required.

## Evaluation

The system will compare fixed-time and adaptive traffic control using actual simulation measurements:

- Average waiting time
- Average queue length
- Total vehicle delay
- Vehicle throughput
- Emergency vehicle delay
- Signal utilization

## Development Phases

1. Architecture and Project Foundation
2. Traffic Simulation and AI Intelligence
3. Adaptive Control, Emergency Priority and IoT
4. Backend, Database and Dashboard
5. Integration, Testing and Evaluation

## Project Integrity

SUMO simulation ground truth and YOLO visual detections are maintained as separate data sources.

Performance results must come from actual simulation runs. Unimplemented features must not be presented as completed.

## License

License to be selected before public release.
