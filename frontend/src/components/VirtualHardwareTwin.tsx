"use client";

import React, { useState } from "react";
import { Activity, Bell, Cpu, ExternalLink, Radio, Volume2, Zap } from "lucide-react";

interface VirtualHardwareTwinProps {
  currentRed?: boolean;
  currentYellow?: boolean;
  currentGreen?: boolean;
  distanceCm?: number;
  onPressEmergencyBtn?: () => void;
}

export const VirtualHardwareTwin: React.FC<VirtualHardwareTwinProps> = ({
  currentRed = true,
  currentYellow = false,
  currentGreen = false,
  distanceCm = 24.5,
  onPressEmergencyBtn,
}) => {
  const [btnPressed, setBtnPressed] = useState(false);
  const [buzzerActive, setBuzzerActive] = useState(false);

  const handleButtonPress = () => {
    setBtnPressed(true);
    setBuzzerActive(true);
    if (onPressEmergencyBtn) {
      onPressEmergencyBtn();
    }
    setTimeout(() => {
      setBtnPressed(false);
      setBuzzerActive(false);
    }, 1500);
  };

  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/90 p-6 shadow-2xl space-y-6">
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-3 border-b border-slate-800 pb-4">
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-600 flex items-center justify-center shadow-lg shadow-blue-500/20">
            <Cpu className="h-5 w-5 text-white" />
          </div>
          <div>
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              ESP32 DevKit V1 — Virtual Hardware Digital Twin
              <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800">
                Wokwi Compatible
              </span>
            </h3>
            <p className="text-xs text-slate-400">
              Interactive breadboard schematic, live GPIO pin telemetry & peripheral signals
            </p>
          </div>
        </div>

        <a
          href="https://wokwi.com"
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold border border-slate-700 transition"
        >
          <span>Open in Wokwi Simulator</span>
          <ExternalLink className="h-3.5 w-3.5 text-slate-400" />
        </a>
      </div>

      {/* Main Hardware Graphical Schematic */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 bg-slate-950/70 p-6 rounded-xl border border-slate-800/80">
        {/* Left: The ESP32 Microcontroller Board Visual */}
        <div className="lg:col-span-5 flex flex-col items-center justify-center p-4 bg-slate-900 rounded-xl border border-slate-700/80 relative shadow-xl">
          {/* Microcontroller PCB Plate */}
          <div className="w-56 bg-slate-800 rounded-lg p-3 border-2 border-slate-600 shadow-inner space-y-3 relative">
            {/* Board Header */}
            <div className="flex items-center justify-between text-[10px] font-mono text-slate-400 border-b border-slate-700 pb-1">
              <span>ESP32 DEVKIT V1</span>
              <span className="text-emerald-400">3.3V SYSTEM</span>
            </div>

            {/* Espressif Metal RF Shield */}
            <div className="w-full h-24 bg-gradient-to-b from-slate-400 to-slate-300 rounded p-2 text-slate-800 flex flex-col justify-between shadow-md border border-slate-200">
              <div className="font-bold text-[10px] tracking-wider font-mono">ESP-WROOM-32</div>
              <div className="text-[9px] font-mono opacity-70">FCC ID: 2AC7Z-ESPWROOM32</div>
              <div className="flex items-center justify-between text-[8px] font-mono">
                <span>Wi-Fi + BLE</span>
                <span className="font-bold text-slate-900">240 MHz DUAL CORE</span>
              </div>
            </div>

            {/* Micro-USB Port at bottom */}
            <div className="w-16 h-3 bg-slate-600 mx-auto rounded-t border border-slate-500" />

            {/* Onboard Status LEDs */}
            <div className="flex items-center justify-between px-2 pt-1">
              <div className="flex items-center gap-1">
                <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse shadow-sm shadow-red-500" />
                <span className="text-[9px] font-mono text-slate-400">PWR</span>
              </div>
              <div className="flex items-center gap-1">
                <span className="w-2 h-2 rounded-full bg-blue-400 animate-pulse shadow-sm shadow-blue-400" />
                <span className="text-[9px] font-mono text-slate-400">WIFI/MQTT</span>
              </div>
            </div>
          </div>

          <span className="text-[11px] font-mono text-slate-400 mt-3">Node: esp32_j1_controller</span>
        </div>

        {/* Right: Connected Peripherals Visuals (LEDs, HC-SR04, Button, Buzzer) */}
        <div className="lg:col-span-7 grid grid-cols-1 sm:grid-cols-2 gap-4">
          {/* Peripheral 1: 3-Aspect Traffic Signal Post */}
          <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800 flex flex-col justify-between">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-bold text-white">Traffic Signal LEDs</span>
              <span className="text-[10px] font-mono text-slate-400">GPIO 18, 19, 21</span>
            </div>

            <div className="flex items-center justify-center gap-4 py-3 bg-slate-950 rounded-lg border border-slate-800/80">
              {/* RED */}
              <div className="flex flex-col items-center gap-1">
                <div
                  className={`w-7 h-7 rounded-full border transition-all duration-300 ${
                    currentRed
                      ? "bg-red-500 border-red-300 shadow-lg shadow-red-500/80 ring-4 ring-red-500/30"
                      : "bg-red-950/40 border-red-900/50 opacity-40"
                  }`}
                />
                <span className="text-[9px] font-mono text-slate-400">D18 (220Ω)</span>
              </div>

              {/* YELLOW */}
              <div className="flex flex-col items-center gap-1">
                <div
                  className={`w-7 h-7 rounded-full border transition-all duration-300 ${
                    currentYellow
                      ? "bg-yellow-400 border-yellow-200 shadow-lg shadow-yellow-400/80 ring-4 ring-yellow-400/30"
                      : "bg-yellow-950/40 border-yellow-900/50 opacity-40"
                  }`}
                />
                <span className="text-[9px] font-mono text-slate-400">D19 (220Ω)</span>
              </div>

              {/* GREEN */}
              <div className="flex flex-col items-center gap-1">
                <div
                  className={`w-7 h-7 rounded-full border transition-all duration-300 ${
                    currentGreen
                      ? "bg-emerald-400 border-emerald-200 shadow-lg shadow-emerald-400/80 ring-4 ring-emerald-400/30"
                      : "bg-emerald-950/40 border-emerald-900/50 opacity-40"
                  }`}
                />
                <span className="text-[9px] font-mono text-slate-400">D21 (220Ω)</span>
              </div>
            </div>

            <p className="text-[10px] text-slate-400 mt-2">
              Driven by 3.3V logic with current-limiting resistors.
            </p>
          </div>

          {/* Peripheral 2: HC-SR04 Ultrasonic Distance Sensor */}
          <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800 flex flex-col justify-between">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-bold text-white">HC-SR04 Ultrasonic</span>
              <span className="text-[10px] font-mono text-slate-400">TRIG: D25 | ECHO: D26</span>
            </div>

            <div className="p-3 bg-blue-950/30 rounded-lg border border-blue-900/40 flex items-center justify-between">
              {/* Dual Transducer Graphic */}
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-full bg-slate-300 border-2 border-slate-500 flex items-center justify-center font-mono text-[9px] text-slate-800 font-bold shadow-inner">
                  T
                </div>
                <div className="w-8 h-8 rounded-full bg-slate-300 border-2 border-slate-500 flex items-center justify-center font-mono text-[9px] text-slate-800 font-bold shadow-inner">
                  R
                </div>
              </div>

              {/* Live Distance Output */}
              <div className="text-right">
                <div className="text-lg font-bold font-mono text-cyan-400">
                  {distanceCm.toFixed(1)} <span className="text-xs text-slate-400">cm</span>
                </div>
                <span className="text-[10px] font-semibold text-emerald-400 uppercase">
                  {distanceCm < 50 ? "● Vehicle at Stopline" : "○ Approach Clear"}
                </span>
              </div>
            </div>

            <p className="text-[10px] text-slate-400 mt-2">
              Echo stepped down: 5V → 3.3V via 1kΩ / 2kΩ voltage divider.
            </p>
          </div>

          {/* Peripheral 3: Tactile Emergency Push Button */}
          <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800 flex flex-col justify-between">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-bold text-white">Emergency Push Button</span>
              <span className="text-[10px] font-mono text-slate-400">GPIO 27 (10kΩ Pulldown)</span>
            </div>

            <div className="flex items-center justify-center py-2">
              <button
                onClick={handleButtonPress}
                className={`w-28 py-3 rounded-full font-bold text-xs uppercase tracking-wider transition-all duration-150 shadow-lg flex items-center justify-center gap-2 ${
                  btnPressed
                    ? "bg-red-700 text-white scale-95 shadow-red-700/80 ring-4 ring-red-400"
                    : "bg-red-600 hover:bg-red-500 text-white shadow-red-600/40 hover:scale-105 active:scale-95"
                }`}
              >
                <Zap className="h-4 w-4" />
                {btnPressed ? "PRESSED!" : "PRESS BTN"}
              </button>
            </div>

            <p className="text-[10px] text-slate-400 mt-2 text-center">
              Click to simulate physical emergency corridor button.
            </p>
          </div>

          {/* Peripheral 4: Alert Piezo Buzzer */}
          <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800 flex flex-col justify-between">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-bold text-white">Piezo Buzzer (Chime)</span>
              <span className="text-[10px] font-mono text-slate-400">GPIO 14</span>
            </div>

            <div className="flex items-center justify-center gap-3 py-3 bg-slate-950 rounded-lg border border-slate-800/80">
              <div
                className={`w-10 h-10 rounded-full border-2 flex items-center justify-center transition-all ${
                  buzzerActive
                    ? "bg-amber-500/20 border-amber-400 text-amber-300 animate-bounce shadow-lg shadow-amber-500/50"
                    : "bg-slate-800 border-slate-700 text-slate-500"
                }`}
              >
                <Volume2 className="h-5 w-5" />
              </div>
              <div>
                <span className="text-xs font-mono font-bold text-white">
                  {buzzerActive ? "1500 Hz ALERT" : "SILENT"}
                </span>
                <p className="text-[10px] text-slate-400">Audible preemption feedback</p>
              </div>
            </div>

            <p className="text-[10px] text-slate-400 mt-2">
              Chirps when an emergency priority corridor is activated.
            </p>
          </div>
        </div>
      </div>

      {/* Live Logic Pin Voltage Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-xs text-left font-mono text-slate-300">
          <thead className="bg-slate-950 text-slate-400 text-[10px] uppercase">
            <tr>
              <th className="py-2 px-3">Pin</th>
              <th className="py-2 px-3">Peripheral</th>
              <th className="py-2 px-3">Direction</th>
              <th className="py-2 px-3">Voltage</th>
              <th className="py-2 px-3">Logic State</th>
              <th className="py-2 px-3">Electrical Protection</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60 text-slate-200">
            <tr>
              <td className="py-2 px-3 font-bold text-cyan-400">GPIO 18</td>
              <td className="py-2 px-3 font-sans">Red LED</td>
              <td className="py-2 px-3 text-slate-400">OUTPUT</td>
              <td className="py-2 px-3 text-white">{currentRed ? "3.3V" : "0.0V"}</td>
              <td className="py-2 px-3">
                <span className={currentRed ? "text-red-400 font-bold" : "text-slate-500"}>
                  {currentRed ? "HIGH" : "LOW"}
                </span>
              </td>
              <td className="py-2 px-3 font-sans text-slate-400">220Ω Current-limiting resistor</td>
            </tr>
            <tr>
              <td className="py-2 px-3 font-bold text-cyan-400">GPIO 19</td>
              <td className="py-2 px-3 font-sans">Yellow LED</td>
              <td className="py-2 px-3 text-slate-400">OUTPUT</td>
              <td className="py-2 px-3 text-white">{currentYellow ? "3.3V" : "0.0V"}</td>
              <td className="py-2 px-3">
                <span className={currentYellow ? "text-yellow-400 font-bold" : "text-slate-500"}>
                  {currentYellow ? "HIGH" : "LOW"}
                </span>
              </td>
              <td className="py-2 px-3 font-sans text-slate-400">220Ω Current-limiting resistor</td>
            </tr>
            <tr>
              <td className="py-2 px-3 font-bold text-cyan-400">GPIO 21</td>
              <td className="py-2 px-3 font-sans">Green LED</td>
              <td className="py-2 px-3 text-slate-400">OUTPUT</td>
              <td className="py-2 px-3 text-white">{currentGreen ? "3.3V" : "0.0V"}</td>
              <td className="py-2 px-3">
                <span className={currentGreen ? "text-emerald-400 font-bold" : "text-slate-500"}>
                  {currentGreen ? "HIGH" : "LOW"}
                </span>
              </td>
              <td className="py-2 px-3 font-sans text-slate-400">220Ω Current-limiting resistor</td>
            </tr>
            <tr>
              <td className="py-2 px-3 font-bold text-cyan-400">GPIO 25</td>
              <td className="py-2 px-3 font-sans">Ultrasonic Trigger</td>
              <td className="py-2 px-3 text-slate-400">OUTPUT</td>
              <td className="py-2 px-3 text-white">3.3V Pulse</td>
              <td className="py-2 px-3 text-cyan-400">10µs PULSE</td>
              <td className="py-2 px-3 font-sans text-slate-400">Direct GPIO Trigger</td>
            </tr>
            <tr>
              <td className="py-2 px-3 font-bold text-cyan-400">GPIO 26</td>
              <td className="py-2 px-3 font-sans">Ultrasonic Echo</td>
              <td className="py-2 px-3 text-slate-400">INPUT</td>
              <td className="py-2 px-3 text-white">3.33V Safe</td>
              <td className="py-2 px-3 text-emerald-400">PULSE IN</td>
              <td className="py-2 px-3 font-sans text-emerald-400">1kΩ + 2kΩ Voltage Divider (5V → 3.3V)</td>
            </tr>
            <tr>
              <td className="py-2 px-3 font-bold text-cyan-400">GPIO 27</td>
              <td className="py-2 px-3 font-sans">Emergency Button</td>
              <td className="py-2 px-3 text-slate-400">INPUT</td>
              <td className="py-2 px-3 text-white">{btnPressed ? "3.3V" : "0.0V"}</td>
              <td className="py-2 px-3">
                <span className={btnPressed ? "text-red-400 font-bold" : "text-slate-500"}>
                  {btnPressed ? "HIGH" : "LOW"}
                </span>
              </td>
              <td className="py-2 px-3 font-sans text-slate-400">10kΩ External Pull-down Resistor</td>
            </tr>
            <tr>
              <td className="py-2 px-3 font-bold text-cyan-400">GPIO 14</td>
              <td className="py-2 px-3 font-sans">Piezo Buzzer</td>
              <td className="py-2 px-3 text-slate-400">OUTPUT</td>
              <td className="py-2 px-3 text-white">{buzzerActive ? "3.3V" : "0.0V"}</td>
              <td className="py-2 px-3">
                <span className={buzzerActive ? "text-amber-400 font-bold" : "text-slate-500"}>
                  {buzzerActive ? "ACTIVE" : "IDLE"}
                </span>
              </td>
              <td className="py-2 px-3 font-sans text-slate-400">Direct PWM tone control</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
};
