# FlowSync — Final Demonstration Sequence

This document describes the exact 12-step sequence used to evaluate and demonstrate FlowSync.

## Demonstration Architecture Flow

```
[SUMO Traffic Simulation] 
      │ (vehicle counts, queues, ambulances)
      ▼
[IoT Software Bridge] ──────► [Mosquitto MQTT] ──────► [FastAPI Backend]
      ▲                                                      │
      │ (traffic commands / preemption)                      ▼
[Virtual ESP32 (Wokwi)]                               [Next.js Dashboard]
 (LEDs, HC-SR04, Emergency Btn)                      (Real-time WebSockets)
```

---

## The 12-Step Live Demonstration

### Step 1: Start Infrastructure & Database
Start Mosquitto MQTT broker and PostgreSQL:
```bash
docker compose -f docker/docker-compose.yml up -d
```
Initialize database tables and seed default 4-intersection topology:
```bash
python -c "from backend.app.core.database import init_db; init_db()"
```

### Step 2: Start FastAPI Backend
Launch the backend server:
```bash
uvicorn backend.app.main:app --port 8000
```
Verify health:
```bash
curl http://localhost:8000/api/v1/health
```

### Step 3: Start the Next.js Dashboard
```bash
cd frontend && npm run dev
```
Open [http://localhost:3000](http://localhost:3000) to see the 4 intersections (J1, J2, J3, J4) connected via WebSocket.

### Step 4: Start the Virtual ESP32 Hardware Circuit
Open [Wokwi](https://wokwi.com), paste `iot/wokwi/diagram.json` and `iot/wokwi/sketch.ino`, and start simulation.
The ESP32 publishes sensor readings to `flowsync/intersection/J1/sensors` and device status to `flowsync/intersection/J1/status`.

### Step 5: Start SUMO Simulation
Execute the traffic bridge:
```bash
python scripts/run_demonstration.py
```
SUMO starts simulating the 2x2 grid with low/medium/heavy background traffic.

### Step 6: Verify Sensor Values Reaching IoT Layer
Virtual ultrasonic distance sensors measure vehicle presence:
- Clear lane: ~350 cm
- Vehicle present at stop line: 15–25 cm
Telemetry publishes to MQTT and streams live onto the dashboard.

### Step 7: Verify MQTT Messages Reaching Backend
FastAPI MQTT subscriber receives payloads on `flowsync/intersection/+/sensors` and persists records to the database.

### Step 8: View Real-time Traffic on Dashboard
The dashboard displays:
- Live Red, Yellow, Green LED visualizers for J1, J2, J3, J4
- Vehicle counts and queue lengths updating every second
- Signal states (e.g. `GGggrrrrGGGg`)

### Step 9: Introduce an Emergency Vehicle
An ambulance (`ambulance_01`) enters at edge `N_J1` on its route toward J1 and J2.

### Step 10: Show Emergency Priority Request
The emergency detector detects the ambulance within 250m of J1 and automatically submits an emergency preemption request.

### Step 11: Show Safe Signal Transition
The safety controller checks the current phase:
- If conflicting, initiates a 3-second Yellow clearance interval.
- Followed by a 1-second All-Red clearance interval.
- Transitions J1 safely to Green Corridor (Phase 0).
- The ambulance crosses safely without conflicting movements.

### Step 12: Restore Normal Operation & View Analytics
Once the ambulance passes J1:
- Emergency corridor is cleared.
- Signal transitions through Yellow -> All-Red back to normal adaptive control.
- Stored event response times and empirical benchmarks can be viewed on the dashboard by clicking "View Benchmark Report".
