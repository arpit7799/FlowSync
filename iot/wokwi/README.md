# FlowSync Virtual IoT Hardware (Wokwi Simulation)

This directory contains the virtual ESP32-based IoT edge controller for intersection **J1** (North-West junction).

## Circuit Components

| Component | Description | Connection / Pin |
|---|---|---|
| **ESP32 DevKit V1** | 30-pin microcontroller | Main IoT controller |
| **Red LED** | Traffic Signal Red indicator | GPIO 18 (via 220Ω current-limiting resistor) |
| **Yellow LED** | Traffic Signal Yellow indicator | GPIO 19 (via 220Ω current-limiting resistor) |
| **Green LED** | Traffic Signal Green indicator | GPIO 21 (via 220Ω current-limiting resistor) |
| **HC-SR04** | Ultrasonic sensor for vehicle presence | VCC to 5V, GND to GND, TRIG to GPIO 25 |
| **Voltage Divider** | Echo 5V -> 3.3V safe step-down | R1 = 1kΩ, R2 = 2kΩ between Echo and GPIO 26 |
| **Push Button** | Emergency Priority Request button | GPIO 27 (with 10kΩ pull-down resistor to GND) |
| **Buzzer** | Emergency Alert Audio Chime | GPIO 14 (positive lead), negative lead to GND |

## Voltage Divider Explanation for HC-SR04 Echo

The HC-SR04 ultrasonic sensor requires a 5V power supply ($V_{CC} = 5\text{V}$) to transmit high-intensity 40 kHz ultrasound bursts. Consequently, its `ECHO` output pin outputs a 5V TTL pulse when an echo is received.

The ESP32 microcontroller's GPIO pins are rated for **3.3V maximum input voltage**. Connecting the 5V Echo pin directly to the ESP32 can degrade or permanently damage the input protection diodes.

To ensure safety and reliability, a resistive voltage divider is placed on the Echo line:
$$V_{out} = V_{in} \times \frac{R_2}{R_1 + R_2} = 5\text{V} \times \frac{2000\,\Omega}{1000\,\Omega + 2000\,\Omega} = 3.33\text{V}$$

This safely conditions the signal to the ESP32 logic level while maintaining pulse timing fidelity.

## GPIO Mapping Table

```
+----------------------------------------------------+
| ESP32 GPIO | Peripheral            | Role          |
+----------------------------------------------------+
| GPIO 18    | Red LED               | Signal Phase  |
| GPIO 19    | Yellow LED            | Signal Phase  |
| GPIO 21    | Green LED             | Signal Phase  |
| GPIO 25    | HC-SR04 TRIG          | Sensor Output |
| GPIO 26    | HC-SR04 ECHO (divided)| Sensor Input  |
| GPIO 27    | Push Button           | Emergency In  |
| GPIO 14    | Piezo Buzzer          | Audio Alert   |
+----------------------------------------------------+
```

## MQTT Topic Mapping

- **Subscribe:** `flowsync/intersection/J1/signals` (Listens for incoming red/yellow/green commands)
- **Publish:** `flowsync/intersection/J1/sensors` (Publishes distance & vehicle detected flag every 500ms)
- **Publish:** `flowsync/intersection/J1/status` (Publishes device uptime, WiFi RSSI, and IP every 10s with retain=True)
- **Publish:** `flowsync/emergency/detected` (Published when emergency push button is triggered)

## How to Run in Wokwi Web Simulator

1. Go to [https://wokwi.com](https://wokwi.com) and start a new **ESP32** project.
2. Replace `diagram.json` with the contents of `iot/wokwi/diagram.json`.
3. Replace `sketch.ino` with the contents of `iot/wokwi/sketch.ino`.
4. Add `PubSubClient` and `ArduinoJson` in the **Library Manager** tab.
5. Click **Start Simulation** (Play button).
6. Click the HC-SR04 sensor in the preview to slide the target distance (distances < 50cm simulate a queue of vehicles waiting).
7. Click the red **EMG_REQ** push button to trigger an emergency priority event.
8. Watch the Serial Monitor for MQTT publish logs and LED state changes.

## Simulation Limitations

- In the public Wokwi web simulator without the Wokwi IoT Gateway plugin, WiFi connects to the simulated `Wokwi-GUEST` network, but direct socket connections to `localhost:1883` on your host machine require either Wokwi IoT Gateway or a publicly reachable broker (e.g. HiveMQ / EMQX test broker).
- The FlowSync software bridge (Phase 4) provides a native Python simulation adapter that communicates directly between SUMO and the Mosquitto MQTT broker without requiring browser simulator hosting.
