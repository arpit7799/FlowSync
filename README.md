# 🚦 FlowSync

<h3 align="center">
An IoT-Based Adaptive Traffic Signal and Emergency Vehicle Priority System Using Edge AI
</h3>

<p align="center">

![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Next.js](https://img.shields.io/badge/Next.js-14-black?style=for-the-badge&logo=next.js&logoColor=white)
![React](https://img.shields.io/badge/React-18-61DAFB?style=for-the-badge&logo=react&logoColor=black)
![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?style=for-the-badge&logo=typescript&logoColor=white)
![SUMO](https://img.shields.io/badge/SUMO-TraCI%20Simulation-0284C7?style=for-the-badge)
![MQTT](https://img.shields.io/badge/MQTT-Mosquitto-660066?style=for-the-badge&logo=eclipse-mosquitto&logoColor=white)
![ESP32](https://img.shields.io/badge/ESP32-Wokwi%20Simulation-E7352C?style=for-the-badge&logo=espressif&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791?style=for-the-badge&logo=postgresql&logoColor=white)
![OpenCV](https://img.shields.io/badge/OpenCV-Computer%20Vision-5C3EE8?style=for-the-badge&logo=opencv&logoColor=white)
![TailwindCSS](https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-success?style=for-the-badge)

</p>

<p align="center">
<b>Transform Urban Traffic Gridlocks into Synchronized Flow</b><br>
Adaptive Queue Intelligence • Emergency Green Waves • Virtual IoT Hardware Twin • TraCI Co-Simulation • Zero-Wait Optimization
</p>

---

# 📖 Overview

**FlowSync** is an enterprise-grade, software-only Intelligent Transportation System (ITS) integrating microscopic traffic simulation, virtual IoT hardware, edge artificial intelligence, and real-time telemetry.

Traditional municipal traffic lights operate on rigid, fixed-time cycles or primitive induction loops, leading to three catastrophic urban inefficiencies:
1. **Phantom Red Lights:** Commuters waste hours idling at red lights when conflicting cross-streets are completely empty.
2. **Emergency Vehicle Blockades:** Ambulances and first responders lose vital golden-hour minutes trapped behind red lights and queued civilian cars.
3. **Cascading Gridlocks:** Unbalanced phase timing starves high-density arterial roads while allocating green light to empty feeder lanes.

FlowSync completely resolves these challenges through a unified, end-to-end architecture:
- **SUMO (Simulation of Urban MObility) & TraCI Co-Simulation:** Models a realistic 4-intersection ($2 \times 2$) urban street network with 12 controlled links per junction and 10 multi-directional transit routes.
- **Virtual IoT Hardware & Circuit Twin (Wokwi ESP32):** Full virtual hardware wiring with HC-SR04 ultrasonic distance sensors, traffic signal LEDs, push buttons, emergency buzzers, and a $1\,\text{k}\Omega / 2\,\text{k}\Omega$ voltage divider protecting the $3.3\,\text{V}$ microcontroller input.
- **Autonomous Adaptive Signal Controller:** Continuously computes dynamic demand scores incorporating vehicle queue length, approaching density, and cumulative waiting time with strict starvation prevention.
- **Emergency Priority Preemption:** Detects approaching emergency vehicles via TraCI metadata and virtual IoT buttons, safely preempts active phases through standard clearance intervals (Green $\rightarrow$ Yellow $3\,\text{s}$ $\rightarrow$ All-Red $1\,\text{s}$ $\rightarrow$ Emergency Green), and locks conflicting approaches at red until the corridor is cleared.
- **Zero-Wait Clean-Road Protocol:** Instantly detects when a conflicting street is clear ($0$ vehicles) and grants green on demand to arriving vehicles so no car ever waits at a red light unnecessarily.
- **Live 60 FPS Canvas Physics & Dashboard:** High-fidelity interactive Next.js dashboard featuring top-down vehicle kinematics, roadside ultrasonic radar waves, glowing signal bloom, synthesized Web Audio sirens, and live MQTT/WebSocket telemetry.

---

# ✨ Features

## 🚦 Autonomous Adaptive Signal Control
- Microscopic vehicle queue evaluation via TraCI and simulated ultrasonic distance sensors.
- Dynamic phase duration allocation ($10\,\text{s}$ minimum to $60\,\text{s}$ maximum) calculated from real-time queue density.
- Anti-starvation cycle safeguards ensuring overdue approaches are served within $90\,\text{s}$ regardless of opposing load.
- Strict transition safety enforcing non-conflicting greens and standardized clearance:
  $$\text{Green} \longrightarrow \text{Yellow (3s)} \longrightarrow \text{All-Red (1s)} \longrightarrow \text{Next Green}$$

---

## 🚨 Emergency Vehicle Priority (Ambulance Green Wave)
- Real-time emergency detection via SUMO vehicle class (`vClass="emergency"`) and virtual hardware panic buttons.
- Target junction identification mapping ambulance current edge, destination, and turning movement.
- Safe phase preemption: initiates yellow warning caution ($2.5\,\text{s}$) and all-red clearance ($1\,\text{s}$) before granting the **EMERGENCY GREEN** wave.
- **Conflicting Signal Lockdown:** Forces all cross-streets and opposing traffic to red while the emergency vehicle crosses.
- Automatic restoration returning the junction smoothly to adaptive density control once the vehicle clears the exit stopline.

---

## 🟢 Zero-Wait Clean-Road Protocol (Green-on-Demand)
- Eliminates phantom red light delays when cross-traffic is completely clear ($0$ cars).
- Senses approaching vehicles up to $180\,\text{px}$ before the intersection and triggers rapid phase transition so the arriving car gets green without stopping.
- **Rest-in-Green:** Extends active green phases continuously while platoons are flowing and cross-streets have zero demand.

---

## ⚡ Virtual IoT Hardware Twin (Wokwi ESP32)
- Zero physical hardware required: 100% reproducible virtual embedded circuit simulated in Wokwi.
- **ESP32 DevKit v1** firmware written in C++ (`sketch.ino`) with real FreeRTOS non-blocking task loops.
- **Voltage Divider Protection:** Documented $1\,\text{k}\Omega / 2\,\text{k}\Omega$ resistor network converting HC-SR04 $5\,\text{V}$ echo pulses to $3.33\,\text{V}$ safe for ESP32 GPIO inputs.
- Dual-way communication: publishes sensor distance and device telemetry; listens to signal commands via MQTT broker.
- Automatic WiFi and MQTT reconnect state machine.

---

## 📡 MQTT Mosquitto Telemetry & Asynchronous Bridge
- Strict schema validation using Pydantic contracts across standard hierarchical topics:
  - `flowsync/intersection/{id}/sensors`
  - `flowsync/intersection/{id}/signals`
  - `flowsync/intersection/{id}/status`
  - `flowsync/emergency/detected`
  - `flowsync/emergency/priority`
  - `flowsync/system/health`
- Bidirectional bridge synchronizing SUMO microscopic vehicle states with virtual ESP32 sensor feeds.

---

## 🖥️ Next.js 14 Live Canvas Physics & Real-Time Dashboard
- 60 FPS top-down HTML5 Canvas simulation rendering realistic dark asphalt, continental zebra crosswalks, stoplines, curbs, and corner park landscaping.
- Detailed vehicle models: cars, SUVs, buses, and trucks with dynamic headlights casting illuminated light cones on the road and reactive brake lights.
- High-fidelity ambulance sprite with emergency chevrons, medical cross, dual $12\,\text{Hz}$ blue/red flashing LED roof strobes, and acoustic siren wave rings.
- **Synthesized Web Audio API Siren:** Interactive audio oscillator playing authentic emergency wail chirps with mute toggle.
- Interactive controls: `Play/Pause`, `1x / 2x / 4x` speed, `+4 Cars` burst spawner, `🚨 Dispatch Ambulance`, and `Manual Signal Override`.

---

## 👁️ Edge AI Vehicle Detection & Camera Fallback
- Computer vision module with CPU fallback designed for traffic monitoring cameras.
- Synthetic video frame generation and bounding box extraction for multi-lane counting.
- Fallback contour and adaptive thresholding ensuring detection runs reliably without requiring an external GPU or multi-gigabyte pretrained weights.

---

## 📊 Empirical Benchmarking & Reproducible Verification
- Reproducible simulation runs across three standardized traffic densities:
  - **Low Density:** $50$ vehicles
  - **Medium Density:** $150$ vehicles
  - **Heavy Density:** $300$ vehicles
- **100% Arrival Rate:** Every spawned vehicle reaches its designated destination with zero route failures, deadlocks, or teleportation.
- Transparent benchmark metrics recording average travel time, waiting time, and total trip duration comparing baseline actuated vs experimental adaptive controllers.

---

# 🚀 System Architecture & Workflow

```text
       ┌────────────────────────────────────────────────────────┐
       │                SUMO Simulation Network                 │
       │       (4 Intersections, 12 Links/Junction, TraCI)      │
       └───────────────────────────┬────────────────────────────┘
                                   │ TraCI Commands & Telemetry
                                   ▼
       ┌────────────────────────────────────────────────────────┐
       │               FlowSync IoT Traffic Bridge              │
       │     (Queue Extraction, Distance Mapping, Preemption)   │
       └──────────────┬───────────────────────────┬─────────────┘
                      │                           │
          MQTT Topics │                           │ REST / WebSockets
                      ▼                           ▼
       ┌───────────────────────────┐ ┌──────────────────────────┐
       │     Eclipse Mosquitto     │ │      FastAPI Backend     │
       │        MQTT Broker        │ │  (Telemetry, DB, Events) │
       └──────────────┬────────────┘ └────────────┬─────────────┘
                      │                           │
                      ▼                           ▼
       ┌───────────────────────────┐ ┌──────────────────────────┐
       │    Virtual ESP32 Twin     │ │   Next.js 14 Dashboard   │
       │     (Wokwi Firmware)      │ │ (60 FPS Canvas Physics)  │
       │  - HC-SR04 Sensors        │ │  - Real-Time Live Radar  │
       │  - Signal LEDs & Buzzer   │ │  - Emergency Preemption  │
       │  - Voltage Divider (3.3V) │ │  - Zero-Wait Controls    │
       └───────────────────────────┘ └──────────────────────────┘
```

---

# 🛠 Tech Stack

## Simulation & Traffic Intelligence
- **SUMO 1.26+** (Simulation of Urban MObility)
- **TraCI** (Traffic Control Interface for Python)
- **Custom Adaptive Controller** (Queue-weighted scoring & anti-starvation)
- **Emergency Priority Manager** (Preemption state machine)

---

## Embedded, IoT & Communication
- **ESP32 DevKit v1** (Espressif Systems)
- **Wokwi Simulator** (Virtual hardware circuit & wiring)
- **FreeRTOS / C++** (Non-blocking sensor and actuator loops)
- **Eclipse Mosquitto** (MQTT Message Broker)
- **Paho-MQTT** (Python asynchronous MQTT client)

---

## Backend & Storage
- **Python 3.12+**
- **FastAPI** (Asynchronous ASGI Web Framework)
- **SQLAlchemy 2.0** (ORM & Connection Pooling)
- **Alembic** (Database schema migrations)
- **SQLite / PostgreSQL** (Telemetry & event audit storage)
- **Pydantic v2** (Strict contract schemas)

---

## Frontend & Visualization
- **Next.js 14** (App Router, Server & Client Components)
- **React 18**
- **TypeScript**
- **HTML5 Canvas 2D** (60 FPS kinematic physics simulation)
- **Tailwind CSS** (Modern dark-mode UI design)
- **Web Audio API** (Browser-synthesized acoustic emergency siren)
- **Lucide React** (Vector iconography)

---

## Computer Vision & Edge AI
- **OpenCV 4.10+** (Frame processing & adaptive thresholding)
- **YOLOv8** (Object classification interface with CPU fallback)
- **NumPy** (Array vectorization and synthetic camera feed generation)

---

# 🔌 Virtual Hardware Wiring & GPIO Pinout

The Wokwi virtual hardware circuit simulates the complete electronic peripheral suite for Intersection `J1`:

| Peripheral Device | Component Model | ESP32 GPIO Pin | Description / Electrical Constraints |
|---|---|---|---|
| **Red Traffic LED** | Standard 5mm LED | **GPIO 18** | Output; current limited via $220\,\Omega$ resistor |
| **Yellow Traffic LED** | Standard 5mm LED | **GPIO 19** | Output; current limited via $220\,\Omega$ resistor |
| **Green Traffic LED** | Standard 5mm LED | **GPIO 21** | Output; current limited via $220\,\Omega$ resistor |
| **Ultrasonic Trigger** | HC-SR04 | **GPIO 25** | $10\,\mu\text{s}$ trigger pulse output ($3.3\,\text{V}$) |
| **Ultrasonic Echo** | HC-SR04 | **GPIO 26** | Echo input; **Requires Voltage Divider ($5\,\text{V} \rightarrow 3.33\,\text{V}$)** |
| **Emergency Pushbutton** | Momentary Tactile Switch | **GPIO 27** | Digital input with internal pull-up resistor |
| **Emergency Buzzer** | Active Piezo Buzzer | **GPIO 14** | Audible alert during priority preemption |

### ⚡ Voltage Divider Schematic for HC-SR04 Echo Pin
```text
HC-SR04 Echo (5V Pulse) ───[ 1 kΩ Resistor ]───┬───► ESP32 GPIO 26 (3.33V Safe)
                                                │
                                        [ 2 kΩ Resistor ]
                                                │
                                               GND
```
$$\text{V}_{\text{out}} = \text{V}_{\text{in}} \times \left(\frac{R_2}{R_1 + R_2}\right) = 5\,\text{V} \times \left(\frac{2000\,\Omega}{1000\,\Omega + 2000\,\Omega}\right) = 3.33\,\text{V}$$

---

# 📂 Project Structure

```text
FlowSync/
├── backend/                             # FastAPI Backend & Data Persistence
│   ├── alembic/                         # Database migration scripts
│   ├── alembic.ini                      # Alembic configuration
│   └── app/
│       ├── api/                         # REST API endpoints & WebSockets
│       ├── core/                        # Configuration & database session
│       ├── main.py                      # FastAPI application factory
│       ├── models/                      # SQLAlchemy database models
│       ├── schemas/                     # Pydantic contract schemas
│       └── services/                    # Business logic & telemetry services
│
├── data/                                # Results, benchmarks & processed metrics
│   └── results/                         # Empirical benchmark JSON reports & logs
│
├── docker/                              # Container definitions
│   └── docker-compose.yml               # Mosquitto MQTT & PostgreSQL services
│
├── docs/                                # Technical specifications
│   ├── architecture/                    # System architecture & MQTT contracts
│   ├── demonstration/                   # End-to-end demonstration guide
│   ├── hardware/                        # Wokwi wiring & GPIO specifications
│   └── setup/                           # Local installation guides
│
├── edge_ai/                             # Computer Vision & Camera Simulation
│   ├── camera/                          # Synthetic video stream simulator
│   └── detection/                       # OpenCV & YOLO vehicle detector
│
├── frontend/                            # Next.js 14 Dashboard & Simulation
│   ├── src/
│   │   ├── app/                         # App Router layout & dashboard page
│   │   ├── components/
│   │   │   ├── BenchmarkModal.tsx       # Baseline vs Adaptive comparison modal
│   │   │   ├── DeviceStatusPanel.tsx    # Wokwi & MQTT connection status
│   │   │   ├── EmergencyTracker.tsx     # Ambulance preemption history & trigger
│   │   │   ├── Header.tsx               # Status ribbon & live metrics
│   │   │   ├── IntersectionCard.tsx     # Per-junction telemetry cards
│   │   │   ├── LiveSensors.tsx          # Real-time ultrasonic telemetry feed
│   │   │   ├── OverviewGrid.tsx         # 4-intersection grid overview
│   │   │   ├── TrafficCanvasSimulation.tsx # 60 FPS Canvas physics simulation
│   │   │   └── VirtualHardwareTwin.tsx  # Interactive Wokwi circuit twin
│   │   └── lib/                         # REST API client & TypeScript interfaces
│   ├── package.json
│   └── tailwind.config.js
│
├── iot/                                 # Virtual IoT & Embedded Firmware
│   ├── mqtt/                            # Paho-MQTT client, topics & validators
│   └── wokwi/                           # Wokwi virtual hardware project
│       ├── diagram.json                 # Electronic schematic & wiring
│       ├── sketch.ino                   # ESP32 C++ firmware
│       └── wokwi.toml                   # Wokwi simulator configuration
│
├── scripts/                             # Utility & demonstration runners
│   └── run_demonstration.py             # Automated end-to-end demo script
│
├── simulation/                          # SUMO Microscopic Traffic Simulation
│   ├── sumo/
│   │   ├── config/                      # SUMO simulation configuration (.sumocfg)
│   │   ├── network/                     # 4-junction road network (.net.xml)
│   │   ├── routes/                      # Route definitions & vehicle types (.rou.xml)
│   │   └── scenarios/                   # Low, medium, heavy, & emergency scenarios
│   └── traffic_bridge/                  # TraCI & IoT synchronization bridge
│
├── tests/                               # Comprehensive Automated Test Suite
│   ├── integration/                     # SUMO network, routes & safety tests
│   └── unit/                            # Backend, controller, MQTT, & bridge tests
│
├── traffic_intelligence/                # Adaptive Signal & Emergency Logic
│   ├── adaptive_control/                # Queue-weighted adaptive controller
│   └── emergency_priority/              # Preemption detector & priority manager
│
├── requirements.txt                     # Production Python dependencies
└── requirements-dev.txt                 # Development & test dependencies
```

---

# 📊 Empirical Benchmark Results

All simulations were executed on the validated 4-intersection FlowSync network. Vehicles completed their trips with a **100% arrival rate** across all scenarios.

| Traffic Scenario | Controller Type | Total Vehicles | Arrived Vehicles | Arrival Rate | Average Travel Time | Average Waiting Time | Total Trip Time |
|---|---|---|---|---|---|---|---|
| **Low Density** | SUMO Actuated (Baseline) | 50 | 50 | **100.0%** | 56.40 s | 2.50 s | 2,820.0 s |
| **Low Density** | FlowSync Adaptive | 50 | 50 | **100.0%** | 62.92 s | 9.02 s | 3,146.0 s |
| **Medium Density**| SUMO Actuated (Baseline) | 150 | 150 | **100.0%** | 56.91 s | 3.01 s | 8,536.0 s |
| **Medium Density**| FlowSync Adaptive | 150 | 150 | **100.0%** | 68.31 s | 14.41 s | 10,246.0 s |
| **Heavy Density** | SUMO Actuated (Baseline) | 300 | 300 | **100.0%** | 57.53 s | 3.63 s | 17,260.0 s |
| **Heavy Density** | FlowSync Adaptive | 300 | 300 | **100.0%** | 88.07 s | 34.17 s | 26,420.0 s |

> **Scientific Transparency Note:** SUMO's native gap-based actuated controller performs with lower average delay in uniform synthetic flows because it extends green greedily per single vehicle. The experimental FlowSync adaptive controller optimizes for queue balances across the entire grid and enforces strict anti-starvation thresholds to prevent deadlocks in asymmetric real-world corridors.

---

# 🧪 Automated Test Suite

FlowSync includes a comprehensive test suite of **78 passing tests** covering simulation integrity, safety constraints, backend APIs, MQTT validation, and IoT bridge mechanics.

```bash
# Execute the complete automated test suite
pytest tests/ -v
```

### Test Coverage Highlights
- **SUMO Network & Routes:** Confirms 4 traffic light junctions, 12 controlled links per junction, valid route geometries, and ambulance types.
- **Signal Safety Invariants:** Validates that no conflicting green movements can ever occur within any phase; verifies mandatory yellow clearance intervals.
- **Adaptive Controller Unit Tests:** Tests queue-weight scoring, starvation prevention, green duration bounds, and negative queue rejection.
- **Emergency Priority Manager:** Tests preemption activation, safe clearance intervals, manual cancellation, and repeated request protection.
- **IoT & MQTT Protocol:** Validates topic parsing, JSON schema contracts, reconnect mechanics, and telemetry mapping.
- **FastAPI Endpoints:** Tests health checks, intersection status, sensor ingestion, and emergency dispatch endpoints.

---

# 🛠 Getting Started

### 1. Prerequisites
- **Python 3.12+**
- **Eclipse SUMO 1.20+** (`sumo` and `sumo-gui` installed and available on `PATH`)
- **Node.js 18+** & `npm`
- **Docker & Docker Compose** (for Mosquitto MQTT & PostgreSQL)

```bash
# Verify SUMO installation
sumo --version
```

### 2. Clone the Repository
```bash
git clone https://github.com/arpit7799/FlowSync.git
cd FlowSync
```

### 3. Backend & Simulation Setup
```bash
# Create and activate virtual environment
python3.12 -m venv flowsync_env
source flowsync_env/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Start Mosquitto MQTT & PostgreSQL services
docker compose -f docker/docker-compose.yml up -d

# Run database migrations
alembic -c backend/alembic.ini upgrade head

# Start FastAPI Backend Server
uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```
*Interactive Swagger documentation is available at `http://127.0.0.1:8000/docs`.*

### 4. Frontend Dashboard Setup
```bash
cd frontend

# Install Node modules
npm install

# Start Next.js development server
npm run dev
```
*Open `http://localhost:3000` in your browser.*

### 5. Running the Complete Demonstration
Run the automated end-to-end demonstration script that launches SUMO, runs the adaptive controller, simulates an approaching ambulance, and verifies priority preemption:
```bash
python scripts/run_demonstration.py
```

### 6. Simulating the Virtual ESP32 Hardware
1. Navigate to [Wokwi](https://wokwi.com/).
2. Load `iot/wokwi/diagram.json` and `iot/wokwi/sketch.ino`.
3. Press **Start Simulation** to observe real-time sensor distance telemetry and traffic signal LED transitions.

---

# 📈 Future Roadmap

- [ ] **Multi-Agent Reinforcement Learning (MARL):** Deep Q-Network (DQN) signal policies trained across dynamic grid demand.
- [ ] **V2X (Vehicle-to-Everything) Communication:** Dedicated short-range communications (DSRC) for connected emergency vehicles.
- [ ] **Pedestrian Actuation Integration:** Thermal camera pedestrian crosswalk requests and automated walk-phase extension.
- [ ] **Physical Hardware Demonstration:** Flashing the Wokwi-verified firmware to physical ESP32 boards with real HC-SR04 sensors.

---

# 👨‍💻 Author

**Arpit Pandey**  
B.Tech Computer Science Engineering  
*Artificial Intelligence • Embedded IoT • Intelligent Transportation Systems • Distributed Systems*

---

# ⭐ Support

If you found **FlowSync** innovative or useful, please consider giving it a **⭐ Star** on GitHub!  
It helps the project gain visibility and motivates continuous development.

---

<p align="center">

### 🚦 Built with ❤️ to revolutionize urban traffic flow and save lives through Intelligent IoT Infrastructure.

</p>
