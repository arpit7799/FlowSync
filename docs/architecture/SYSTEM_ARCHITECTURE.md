# FlowSync System Architecture

## 1. Project Overview

FlowSync is an IoT-based adaptive traffic signal and emergency
vehicle priority system using edge AI and traffic simulation.

The system simulates four connected intersections and uses
intelligent traffic control to reduce congestion and emergency
vehicle delays.

The project is developed entirely using software simulation.
No physical traffic signals, Raspberry Pi, ESP32 or sensors
are required.

## 2. System Components

### 2.1 Traffic Simulation
Technology: SUMO, TraCI, Python

Responsibilities:
- Simulate four interconnected intersections.
- Generate different vehicle types and traffic demand.
- Simulate emergency vehicles.
- Expose vehicle positions and traffic light states.
- Measure queue lengths and waiting times.
- Execute traffic signal commands.

### 2.2 Edge AI
Technology: Python, OpenCV, YOLO, ONNX Runtime

Responsibilities:
- Process simulated camera frames.
- Detect and classify vehicles.
- Estimate lane-wise vehicle density.
- Identify emergency vehicles using a validated model.
- Export and benchmark optimized ONNX models.

Important:
YOLO inference must operate on actual image frames.
SUMO vehicle counts must not be presented as YOLO detections.

### 2.3 Traffic Intelligence
Technology: Python

Responsibilities:
- Calculate traffic demand.
- Adapt traffic signal green duration.
- Prevent starvation of low-demand lanes.
- Apply minimum and maximum green constraints.
- Handle yellow and all-red transitions.
- Process emergency priority requests.
- Coordinate emergency green corridors.
- Recover safely to normal adaptive operation.

### 2.4 IoT Communication
Technology: MQTT, Mosquitto, Wokwi, ESP32 simulation

Responsibilities:
- Exchange intersection state messages.
- Publish traffic signal commands.
- Communicate emergency priority events.
- Report node health and connectivity.
- Simulate ESP32 traffic signal controllers.

### 2.5 Backend
Technology: FastAPI, PostgreSQL, SQLAlchemy, WebSockets

Responsibilities:
- Receive simulation and AI telemetry.
- Manage intersection and signal states.
- Store events and historical measurements.
- Expose REST APIs.
- Publish real-time dashboard updates.
- Manage emergency requests and analytics.

### 2.6 Frontend
Technology: Next.js, React, TypeScript, Tailwind CSS

Responsibilities:
- Display four connected intersections.
- Visualize traffic signal states.
- Display vehicle detection information.
- Show lane density and queue information.
- Visualize emergency routes.
- Display MQTT node health.
- Present traffic analytics and comparisons.

## 3. Data Flow

1. SUMO generates simulated traffic.
2. TraCI extracts simulation state.
3. Camera frames are processed independently by OpenCV and YOLO.
4. Traffic intelligence combines validated traffic measurements.
5. The controller generates safe signal decisions.
6. MQTT distributes intersection commands and telemetry.
7. FastAPI receives events and stores relevant records.
8. WebSockets deliver live updates to the dashboard.
9. The dashboard visualizes the system state.

## 4. Emergency Priority Workflow

1. Detect or receive an emergency vehicle request.
2. Identify its current and target route.
3. Calculate the intersections requiring priority.
4. Check conflicting traffic movements.
5. Safely transition signals using yellow and all-red phases.
6. Coordinate the green corridor across consecutive intersections.
7. Track emergency vehicle progress.
8. Release priority and restore adaptive control.

Manual emergency activation is retained as a repeatable testing
fallback if automatic recognition is unavailable or uncertain.

## 5. Simulation and Evaluation

FlowSync will compare:
- Fixed-time signal control.
- Adaptive signal control.
- Adaptive control with emergency priority.

Metrics:
- Average waiting time.
- Average queue length.
- Total vehicle delay.
- Vehicle throughput.
- Emergency vehicle delay.
- Signal utilization.

All metrics must be obtained from actual simulation runs.

## 6. Software-only Deployment

The project targets development on an Apple Silicon Mac.

Raspberry Pi compatibility will be evaluated through software
compatibility and resource benchmarks, not claimed as physical
hardware deployment.

Wokwi will be used for ESP32 simulation. MQTT integration must
be tested before claiming successful communication.

## 7. Reliability and Safety

- Validate incoming MQTT messages.
- Enforce safe signal transitions.
- Apply bounded green durations.
- Prevent conflicting emergency routes from receiving
  incompatible priority commands.
- Provide fallback control when AI or communication fails.
- Record important control decisions and failures.

## 8. Architectural Principle

SUMO is the source of simulated traffic ground truth.
YOLO is responsible for visual inference on image frames.
The two data sources must remain distinguishable.

The backend must not replace the traffic intelligence engine.
The dashboard must display actual backend data rather than
fabricated demonstration values.
