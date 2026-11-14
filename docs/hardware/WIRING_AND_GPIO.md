# FlowSync — Virtual IoT Hardware & Wiring Documentation

This document specifies the virtual hardware layout, component specifications, circuit connections, and electrical protection calculations for the ESP32-based traffic signal edge controller.

## 1. Controller Hardware Overview

Each of the four intersections (J1, J2, J3, J4) is controlled by a virtual ESP32 DevKit V1 node. The design is fully simulated in **Wokwi** (`iot/wokwi/`) with zero physical hardware dependencies.

### Bill of Materials (Per Intersection)

| Component | Quantity | Specification / Rating | Role |
|---|---|---|---|
| ESP32 DevKit V1 | 1 | 30-pin, Dual Core 240MHz, 3.3V Logic | Main edge controller |
| Red LED | 1 | Standard 5mm Diffused (Forward: 2.0V, 15mA) | Red Signal Indicator |
| Yellow LED | 1 | Standard 5mm Diffused (Forward: 2.1V, 15mA) | Yellow Signal Indicator |
| Green LED | 1 | Standard 5mm Diffused (Forward: 3.0V, 15mA) | Green Signal Indicator |
| Current Limiting Resistors | 3 | 220Ω, 1/4W, 5% Tolerance | LED current regulation |
| HC-SR04 Ultrasonic Sensor | 1 | 5V Supply, 40kHz Ultrasound, 2cm–400cm | Vehicle presence & queue detection |
| Voltage Divider Resistor $R_1$ | 1 | 1kΩ, 1/4W, 1% Metal Film | Echo line high-side divider |
| Voltage Divider Resistor $R_2$ | 1 | 2kΩ, 1/4W, 1% Metal Film | Echo line low-side divider |
| Push Button | 1 | SPST Momentary Tactile Switch | Emergency Priority Request |
| Pull-down Resistor | 1 | 10kΩ, 1/4W | Button input ground reference |
| Piezo Buzzer | 1 | 3.3V–5V Electromagnetic Buzzer | Emergency Alert Audio Chime |

---

## 2. GPIO Pinout Mapping

```
+-----------------------------------------------------------------------+
| ESP32 Pin | Connected Device             | Signal Type | Logic Level  |
+-----------------------------------------------------------------------+
| GPIO 18   | Red LED (via 220Ω resistor)   | Digital Out | 3.3V Active-H|
| GPIO 19   | Yellow LED (via 220Ω resistor)| Digital Out | 3.3V Active-H|
| GPIO 21   | Green LED (via 220Ω resistor) | Digital Out | 3.3V Active-H|
| GPIO 25   | HC-SR04 Trigger               | Digital Out | 3.3V Pulse   |
| GPIO 26   | HC-SR04 Echo (divided)        | Digital In  | 3.3V Safe In |
| GPIO 27   | Emergency Request Button      | Digital In  | 3.3V Active-H|
| GPIO 14   | Piezo Buzzer (Alert Chime)    | PWM / Tone  | 3.3V Audio   |
| 5V (VIN)  | HC-SR04 VCC                   | Power       | 5.0V DC      |
| 3V3       | Button High Supply            | Power       | 3.3V DC      |
| GND       | Common System Ground          | Ground      | 0V Reference |
+-----------------------------------------------------------------------+
```

---

## 3. Electrical Protection & Voltage Divider Analysis

### The 5V HC-SR04 to 3.3V ESP32 Interfacing Constraint

The HC-SR04 ultrasonic sensor requires a 5V power supply ($V_{CC} = 5.0\text{V}$) to energize its ultrasonic transducers. Its output `ECHO` line produces a 5V TTL pulse proportional to obstacle distance.

However, the ESP32 GPIO inputs are **strictly 3.3V tolerant**. Applying 5V directly to GPIO 26 risks forward-biasing the internal clamping diodes, leading to thermal breakdown or pin latch-up.

### Voltage Divider Calculation

A resistive divider is placed between the `ECHO` output and the ESP32 `GPIO 26`:

$$V_{out} = V_{in} \times \left( \frac{R_2}{R_1 + R_2} \right)$$

With:
- $V_{in} = 5.0\text{V}$ (HC-SR04 Echo pulse)
- $R_1 = 1{,}000\,\Omega$
- $R_2 = 2{,}000\,\Omega$

$$V_{out} = 5.0\text{V} \times \left( \frac{2000}{1000 + 2000} \right) = 5.0 \times \frac{2}{3} \approx 3.33\text{V}$$

This safely levels the 5V pulse to **3.33V**, perfectly within the high-level input threshold ($V_{IH} \ge 0.75 \times V_{DD} = 2.475\text{V}$) and maximum rating ($3.6\text{V}$).

---

## 4. Current-Limiting Resistor Calculations for LEDs

For a 3.3V supply and 15mA forward current ($I_F = 0.015\text{A}$):

$$R = \frac{V_{DD} - V_F}{I_F}$$

- **Red LED** ($V_F \approx 2.0\text{V}$):
  $$R = \frac{3.3 - 2.0}{0.015} = \frac{1.3}{0.015} \approx 86.7\,\Omega \implies \text{Selected: } 220\,\Omega \text{ (safe ~6mA current)}$$
- **Yellow LED** ($V_F \approx 2.1\text{V}$):
  $$R = \frac{3.3 - 2.1}{0.015} = \frac{1.2}{0.015} \approx 80.0\,\Omega \implies \text{Selected: } 220\,\Omega$$
- **Green LED** ($V_F \approx 3.0\text{V}$):
  $$R = \frac{3.3 - 3.0}{0.015} = \frac{0.3}{0.015} \approx 20.0\,\Omega \implies \text{Selected: } 220\,\Omega$$

Selecting standard $220\,\Omega$ resistors ensures low power consumption and prevents driver overloading.
