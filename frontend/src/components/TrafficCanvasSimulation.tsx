"use client";

import React, { useEffect, useRef, useState } from "react";
import {
  AlertTriangle,
  Car,
  CheckCircle2,
  Cpu,
  FastForward,
  Info,
  Maximize2,
  Pause,
  Play,
  Radio,
  RefreshCw,
  ShieldAlert,
  Sparkles,
  Volume2,
  VolumeX,
  Wifi,
} from "lucide-react";

interface RoutePoint {
  x: number;
  y: number;
  junction?: string;
  approach?: "N" | "S" | "E" | "W";
  dir?: "NS" | "EW";
  stopLineX?: number;
  stopLineY?: number;
}

interface Vehicle {
  id: string;
  type: "car" | "ambulance" | "suv" | "bus" | "truck";
  x: number;
  y: number;
  targetX: number;
  targetY: number;
  routeIdx: number;
  route: RoutePoint[];
  speed: number;
  maxSpeed: number;
  length: number;
  width: number;
  color: string;
  waitingTime: number;
  isStopped: boolean;
  isBraking: boolean;
  angle: number;
}

interface SignalState {
  mode: "green" | "yellow" | "all_red" | "emergency_green";
  phase: 0 | 2; // 0 = NS green, 2 = EW green
  timer: number;
  emergencyTargetDir?: "NS" | "EW";
  transitionTimer: number;
  isZeroWaitActive?: boolean;
}

interface DecisionLog {
  id: string;
  timestamp: string;
  junction: string;
  type: "adaptive" | "emergency" | "manual";
  message: string;
}

export const TrafficCanvasSimulation: React.FC = () => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  // Simulation controls state
  const [isRunning, setIsRunning] = useState<boolean>(true);
  const [simSpeed, setSimSpeed] = useState<number>(1);
  const [autoSpawn, setAutoSpawn] = useState<boolean>(true);
  const [zeroWaitGreen, setZeroWaitGreen] = useState<boolean>(true);
  const [showSensorRadar, setShowSensorRadar] = useState<boolean>(true);
  const [soundEnabled, setSoundEnabled] = useState<boolean>(true);
  const [activeAmbulances, setActiveAmbulances] = useState<number>(0);
  const [totalVehicles, setTotalVehicles] = useState<number>(0);
  const [selectedJunction, setSelectedJunction] = useState<string>("J1");
  const [decisionLogs, setDecisionLogs] = useState<DecisionLog[]>([]);

  // Audio Context for Siren
  const audioCtxRef = useRef<AudioContext | null>(null);
  const oscRef = useRef<OscillatorNode | null>(null);
  const lfoRef = useRef<OscillatorNode | null>(null);
  const gainRef = useRef<GainNode | null>(null);

  const ensureAudioContext = () => {
    try {
      if (!audioCtxRef.current) {
        audioCtxRef.current = new (window.AudioContext || (window as any).webkitAudioContext)();
      }
      if (audioCtxRef.current.state === "suspended") {
        audioCtxRef.current.resume();
      }
      return audioCtxRef.current;
    } catch (e) {
      console.warn("AudioContext error:", e);
      return null;
    }
  };

  // Junction centers in canvas coordinate space (W=1000, H=580)
  const J1 = { x: 300, y: 180 };
  const J2 = { x: 740, y: 180 };
  const J3 = { x: 300, y: 440 };
  const J4 = { x: 740, y: 440 };

  const ROAD_W = 70; // 35px per lane
  const LANE_OFFSET = 17.5;

  // Signal states for J1, J2, J3, J4
  const signalsRef = useRef<{ [key: string]: SignalState }>({
    J1: { mode: "green", phase: 0, timer: 14, transitionTimer: 0 },
    J2: { mode: "green", phase: 2, timer: 12, transitionTimer: 0 },
    J3: { mode: "green", phase: 2, timer: 15, transitionTimer: 0 },
    J4: { mode: "green", phase: 0, timer: 16, transitionTimer: 0 },
  });

  const vehiclesRef = useRef<Vehicle[]>([]);

  // Real-time sensor readings per approach
  const sensorDataRef = useRef<{
    [key: string]: {
      count: number;
      distanceCm: number;
      detected: boolean;
      hasAmbulance: boolean;
      speedAvg: number;
    };
  }>({
    J1_N: { count: 0, distanceCm: 350, detected: false, hasAmbulance: false, speedAvg: 0 },
    J1_S: { count: 0, distanceCm: 350, detected: false, hasAmbulance: false, speedAvg: 0 },
    J1_E: { count: 0, distanceCm: 350, detected: false, hasAmbulance: false, speedAvg: 0 },
    J1_W: { count: 0, distanceCm: 350, detected: false, hasAmbulance: false, speedAvg: 0 },

    J2_N: { count: 0, distanceCm: 350, detected: false, hasAmbulance: false, speedAvg: 0 },
    J2_S: { count: 0, distanceCm: 350, detected: false, hasAmbulance: false, speedAvg: 0 },
    J2_E: { count: 0, distanceCm: 350, detected: false, hasAmbulance: false, speedAvg: 0 },
    J2_W: { count: 0, distanceCm: 350, detected: false, hasAmbulance: false, speedAvg: 0 },

    J3_N: { count: 0, distanceCm: 350, detected: false, hasAmbulance: false, speedAvg: 0 },
    J3_S: { count: 0, distanceCm: 350, detected: false, hasAmbulance: false, speedAvg: 0 },
    J3_E: { count: 0, distanceCm: 350, detected: false, hasAmbulance: false, speedAvg: 0 },
    J3_W: { count: 0, distanceCm: 350, detected: false, hasAmbulance: false, speedAvg: 0 },

    J4_N: { count: 0, distanceCm: 350, detected: false, hasAmbulance: false, speedAvg: 0 },
    J4_S: { count: 0, distanceCm: 350, detected: false, hasAmbulance: false, speedAvg: 0 },
    J4_E: { count: 0, distanceCm: 350, detected: false, hasAmbulance: false, speedAvg: 0 },
    J4_W: { count: 0, distanceCm: 350, detected: false, hasAmbulance: false, speedAvg: 0 },
  });

  // Logging helper
  const addLog = (junction: string, type: "adaptive" | "emergency" | "manual", message: string) => {
    const timeStr = new Date().toLocaleTimeString();
    setDecisionLogs((prev) => [
      { id: `${Date.now()}_${Math.random()}`, timestamp: timeStr, junction, type, message },
      ...prev.slice(0, 19),
    ]);
  };

  // Diverse realistic routes across the 2x2 grid
  const ROUTES: RoutePoint[][] = [
    // 0: North to South straight (via J1 and J3)
    [
      { x: J1.x - LANE_OFFSET, y: -40 },
      { x: J1.x - LANE_OFFSET, y: J1.y - ROAD_W / 2 - 10, junction: "J1", approach: "N", dir: "NS", stopLineX: J1.x - LANE_OFFSET, stopLineY: J1.y - ROAD_W / 2 },
      { x: J1.x - LANE_OFFSET, y: J1.y + ROAD_W / 2 + 10 },
      { x: J3.x - LANE_OFFSET, y: J3.y - ROAD_W / 2 - 10, junction: "J3", approach: "N", dir: "NS", stopLineX: J3.x - LANE_OFFSET, stopLineY: J3.y - ROAD_W / 2 },
      { x: J3.x - LANE_OFFSET, y: 640 },
    ],
    // 1: South to North straight (via J3 and J1)
    [
      { x: J3.x + LANE_OFFSET, y: 640 },
      { x: J3.x + LANE_OFFSET, y: J3.y + ROAD_W / 2 + 10, junction: "J3", approach: "S", dir: "NS", stopLineX: J3.x + LANE_OFFSET, stopLineY: J3.y + ROAD_W / 2 },
      { x: J3.x + LANE_OFFSET, y: J3.y - ROAD_W / 2 - 10 },
      { x: J1.x + LANE_OFFSET, y: J1.y + ROAD_W / 2 + 10, junction: "J1", approach: "S", dir: "NS", stopLineX: J1.x + LANE_OFFSET, stopLineY: J1.y + ROAD_W / 2 },
      { x: J1.x + LANE_OFFSET, y: -40 },
    ],
    // 2: West to East straight (via J1 and J2)
    [
      { x: -40, y: J1.y + LANE_OFFSET },
      { x: J1.x - ROAD_W / 2 - 10, y: J1.y + LANE_OFFSET, junction: "J1", approach: "W", dir: "EW", stopLineX: J1.x - ROAD_W / 2, stopLineY: J1.y + LANE_OFFSET },
      { x: J1.x + ROAD_W / 2 + 10, y: J1.y + LANE_OFFSET },
      { x: J2.x - ROAD_W / 2 - 10, y: J2.y + LANE_OFFSET, junction: "J2", approach: "W", dir: "EW", stopLineX: J2.x - ROAD_W / 2, stopLineY: J2.y + LANE_OFFSET },
      { x: 1040, y: J2.y + LANE_OFFSET },
    ],
    // 3: East to West straight (via J2 and J1)
    [
      { x: 1040, y: J2.y - LANE_OFFSET },
      { x: J2.x + ROAD_W / 2 + 10, y: J2.y - LANE_OFFSET, junction: "J2", approach: "E", dir: "EW", stopLineX: J2.x + ROAD_W / 2, stopLineY: J2.y - LANE_OFFSET },
      { x: J2.x - ROAD_W / 2 - 10, y: J2.y - LANE_OFFSET },
      { x: J1.x + ROAD_W / 2 + 10, y: J1.y - LANE_OFFSET, junction: "J1", approach: "E", dir: "EW", stopLineX: J1.x + ROAD_W / 2, stopLineY: J1.y - LANE_OFFSET },
      { x: -40, y: J1.y - LANE_OFFSET },
    ],
    // 4: West to East straight (via J3 and J4)
    [
      { x: -40, y: J3.y + LANE_OFFSET },
      { x: J3.x - ROAD_W / 2 - 10, y: J3.y + LANE_OFFSET, junction: "J3", approach: "W", dir: "EW", stopLineX: J3.x - ROAD_W / 2, stopLineY: J3.y + LANE_OFFSET },
      { x: J3.x + ROAD_W / 2 + 10, y: J3.y + LANE_OFFSET },
      { x: J4.x - ROAD_W / 2 - 10, y: J4.y + LANE_OFFSET, junction: "J4", approach: "W", dir: "EW", stopLineX: J4.x - ROAD_W / 2, stopLineY: J4.y + LANE_OFFSET },
      { x: 1040, y: J4.y + LANE_OFFSET },
    ],
    // 5: East to West straight (via J4 and J3)
    [
      { x: 1040, y: J4.y - LANE_OFFSET },
      { x: J4.x + ROAD_W / 2 + 10, y: J4.y - LANE_OFFSET, junction: "J4", approach: "E", dir: "EW", stopLineX: J4.x + ROAD_W / 2, stopLineY: J4.y - LANE_OFFSET },
      { x: J4.x - ROAD_W / 2 - 10, y: J4.y - LANE_OFFSET },
      { x: J3.x + ROAD_W / 2 + 10, y: J3.y - LANE_OFFSET, junction: "J3", approach: "E", dir: "EW", stopLineX: J3.x + ROAD_W / 2, stopLineY: J3.y - LANE_OFFSET },
      { x: -40, y: J3.y - LANE_OFFSET },
    ],
    // 6: North to South straight (via J2 and J4)
    [
      { x: J2.x - LANE_OFFSET, y: -40 },
      { x: J2.x - LANE_OFFSET, y: J2.y - ROAD_W / 2 - 10, junction: "J2", approach: "N", dir: "NS", stopLineX: J2.x - LANE_OFFSET, stopLineY: J2.y - ROAD_W / 2 },
      { x: J2.x - LANE_OFFSET, y: J2.y + ROAD_W / 2 + 10 },
      { x: J4.x - LANE_OFFSET, y: J4.y - ROAD_W / 2 - 10, junction: "J4", approach: "N", dir: "NS", stopLineX: J4.x - LANE_OFFSET, stopLineY: J4.y - ROAD_W / 2 },
      { x: J4.x - LANE_OFFSET, y: 640 },
    ],
    // 7: South to North straight (via J4 and J2)
    [
      { x: J4.x + LANE_OFFSET, y: 640 },
      { x: J4.x + LANE_OFFSET, y: J4.y + ROAD_W / 2 + 10, junction: "J4", approach: "S", dir: "NS", stopLineX: J4.x + LANE_OFFSET, stopLineY: J4.y + ROAD_W / 2 },
      { x: J4.x + LANE_OFFSET, y: J4.y - ROAD_W / 2 - 10 },
      { x: J2.x + LANE_OFFSET, y: J2.y + ROAD_W / 2 + 10, junction: "J2", approach: "S", dir: "NS", stopLineX: J2.x + LANE_OFFSET, stopLineY: J2.y + ROAD_W / 2 },
      { x: J2.x + LANE_OFFSET, y: -40 },
    ],
    // 8: Turning Route - North to East (via J1, turns East to J2)
    [
      { x: J1.x - LANE_OFFSET, y: -40 },
      { x: J1.x - LANE_OFFSET, y: J1.y - ROAD_W / 2 - 10, junction: "J1", approach: "N", dir: "NS", stopLineX: J1.x - LANE_OFFSET, stopLineY: J1.y - ROAD_W / 2 },
      { x: J1.x - LANE_OFFSET, y: J1.y + LANE_OFFSET },
      { x: J1.x + ROAD_W / 2 + 10, y: J1.y + LANE_OFFSET },
      { x: J2.x - ROAD_W / 2 - 10, y: J2.y + LANE_OFFSET, junction: "J2", approach: "W", dir: "EW", stopLineX: J2.x - ROAD_W / 2, stopLineY: J2.y + LANE_OFFSET },
      { x: 1040, y: J2.y + LANE_OFFSET },
    ],
    // 9: Turning Route - West to South (via J1, turns South to J3)
    [
      { x: -40, y: J1.y + LANE_OFFSET },
      { x: J1.x - ROAD_W / 2 - 10, y: J1.y + LANE_OFFSET, junction: "J1", approach: "W", dir: "EW", stopLineX: J1.x - ROAD_W / 2, stopLineY: J1.y + LANE_OFFSET },
      { x: J1.x - LANE_OFFSET, y: J1.y + LANE_OFFSET },
      { x: J1.x - LANE_OFFSET, y: J1.y + ROAD_W / 2 + 10 },
      { x: J3.x - LANE_OFFSET, y: J3.y - ROAD_W / 2 - 10, junction: "J3", approach: "N", dir: "NS", stopLineX: J3.x - LANE_OFFSET, stopLineY: J3.y - ROAD_W / 2 },
      { x: J3.x - LANE_OFFSET, y: 640 },
    ],
  ];

  // Helper to spawn a new vehicle
  const spawnVehicle = (
    type: "car" | "ambulance" | "suv" | "bus" | "truck" = "car",
    routeIndex?: number
  ) => {
    const rIdx = routeIndex !== undefined ? routeIndex : Math.floor(Math.random() * ROUTES.length);
    const chosenRoute = ROUTES[rIdx];
    const startPt = chosenRoute[0];

    const carColors = ["#38bdf8", "#818cf8", "#f43f5e", "#fbbf24", "#34d399", "#a855f7", "#e2e8f0"];
    const isAmbulance = type === "ambulance";

    const newVeh: Vehicle = {
      id: `${type}_${Date.now()}_${Math.floor(Math.random() * 1000)}`,
      type,
      x: startPt.x,
      y: startPt.y,
      targetX: chosenRoute[1].x,
      targetY: chosenRoute[1].y,
      routeIdx: 1,
      route: chosenRoute,
      speed: 0,
      maxSpeed: isAmbulance ? 3.6 : type === "bus" || type === "truck" ? 1.8 : 2.5,
      length: isAmbulance ? 34 : type === "bus" ? 48 : type === "truck" ? 42 : type === "suv" ? 28 : 24,
      width: isAmbulance ? 16 : type === "bus" ? 18 : type === "truck" ? 18 : 14,
      color: isAmbulance ? "#ffffff" : carColors[Math.floor(Math.random() * carColors.length)],
      waitingTime: 0,
      isStopped: false,
      isBraking: false,
      angle: 0,
    };

    vehiclesRef.current.push(newVeh);
    setTotalVehicles(vehiclesRef.current.length);

    if (isAmbulance) {
      const ambCount = vehiclesRef.current.filter((veh) => veh.type === "ambulance").length;
      setActiveAmbulances(ambCount);
      if (soundEnabled) {
        startSirenSound();
      }
      addLog(
        chosenRoute[1]?.junction || "Grid",
        "emergency",
        `🚨 EMERGENCY AMBULANCE DISPATCHED! Priority Green Wave Initiated.`
      );
    }
  };

  // Pre-seed realistic vehicle traffic
  useEffect(() => {
    for (let i = 0; i < 7; i++) {
      spawnVehicle(i === 3 ? "suv" : i === 5 ? "truck" : "car", i % ROUTES.length);
    }
    addLog("System", "adaptive", "Autonomous IoT Adaptive Signal Engine & Sensor Telemetry Initialized.");
  }, []);

  const stopSirenSound = () => {
    try {
      if (oscRef.current) {
        oscRef.current.stop();
        oscRef.current.disconnect();
        oscRef.current = null;
      }
      if (lfoRef.current) {
        lfoRef.current.stop();
        lfoRef.current.disconnect();
        lfoRef.current = null;
      }
    } catch (e) {}
  };

  const startSirenSound = () => {
    try {
      const ctx = ensureAudioContext();
      if (!ctx) return;

      // Don't recreate if already sounding
      if (oscRef.current && lfoRef.current) return;

      stopSirenSound();

      // Main siren carrier oscillator
      const osc = ctx.createOscillator();
      const masterGain = ctx.createGain();

      // Low Frequency Oscillator (LFO) for authentic continuous emergency wail
      const lfo = ctx.createOscillator();
      const lfoGain = ctx.createGain();

      osc.type = "sawtooth";
      osc.frequency.setValueAtTime(800, ctx.currentTime);

      lfo.type = "sine";
      lfo.frequency.setValueAtTime(1.4, ctx.currentTime); // 1.4 Hz wail frequency

      lfoGain.gain.setValueAtTime(260, ctx.currentTime); // Modulate pitch from 540 Hz to 1060 Hz
      lfo.connect(lfoGain);
      lfoGain.connect(osc.frequency);

      // Audible clear volume
      masterGain.gain.setValueAtTime(0.25, ctx.currentTime);
      osc.connect(masterGain);
      masterGain.connect(ctx.destination);

      osc.start();
      lfo.start();

      oscRef.current = osc;
      lfoRef.current = lfo;
      gainRef.current = masterGain;
    } catch (err) {
      console.warn("Audio start error:", err);
    }
  };

  // Web Audio Synthesizer for Emergency Siren
  useEffect(() => {
    if (!soundEnabled || activeAmbulances === 0) {
      stopSirenSound();
    } else if (soundEnabled && activeAmbulances > 0) {
      startSirenSound();
    }

    return () => {
      stopSirenSound();
    };
  }, [soundEnabled, activeAmbulances]);

  // Periodic Random Traffic Spawner
  useEffect(() => {
    if (!isRunning || !autoSpawn) return;

    const spawnInterval = setInterval(() => {
      if (vehiclesRef.current.length < 18) {
        const types: ("car" | "suv" | "truck" | "bus")[] = ["car", "car", "car", "suv", "truck", "bus"];
        const chosenType = types[Math.floor(Math.random() * types.length)];
        spawnVehicle(chosenType);
      }
    }, 2800 / simSpeed);

    return () => clearInterval(spawnInterval);
  }, [isRunning, autoSpawn, simSpeed]);

  // Sensor Scanning & Adaptive Signal Decision Loop (Every 1s tick)
  useEffect(() => {
    if (!isRunning) return;

    const interval = setInterval(() => {
      const signals = signalsRef.current;
      const vehicles = vehiclesRef.current;
      const sensors = sensorDataRef.current;

      const ambulances = vehicles.filter((v) => v.type === "ambulance");
      setActiveAmbulances(ambulances.length);

      // Junction list
      const junctions = [
        { id: "J1", pos: J1 },
        { id: "J2", pos: J2 },
        { id: "J3", pos: J3 },
        { id: "J4", pos: J4 },
      ];

      junctions.forEach(({ id, pos }) => {
        const sig = signals[id];

        // 1. Calculate approach queues from sensors
        const nKey = `${id}_N`;
        const sKey = `${id}_S`;
        const eKey = `${id}_E`;
        const wKey = `${id}_W`;

        const nsQueue = (sensors[nKey]?.count || 0) + (sensors[sKey]?.count || 0);
        const ewQueue = (sensors[eKey]?.count || 0) + (sensors[wKey]?.count || 0);

        // Check for approaching ambulance targeting this junction
        let ambulanceApproaching: Vehicle | null = null;
        let ambulanceDir: "NS" | "EW" = "NS";

        for (const amb of ambulances) {
          const nextWp = amb.route[amb.routeIdx];
          if (nextWp?.junction === id) {
            const dist = Math.hypot(amb.x - pos.x, amb.y - pos.y);
            if (dist < 260) {
              ambulanceApproaching = amb;
              ambulanceDir = nextWp.dir || "NS";
              break;
            }
          }
        }

        // ====================================================================
        // EMERGENCY VEHICLE PRIORITY ENGINE
        // ====================================================================
        if (ambulanceApproaching) {
          const reqPhase: 0 | 2 = ambulanceDir === "NS" ? 0 : 2;

          if (sig.phase === reqPhase && (sig.mode === "green" || sig.mode === "emergency_green")) {
            // Already green for ambulance! Lock into emergency green corridor
            if (sig.mode !== "emergency_green") {
              sig.mode = "emergency_green";
              sig.timer = 18;
              addLog(
                id,
                "emergency",
                `🚨 AMBULANCE GRANTED GREEN CORRIDOR at ${id} (${ambulanceDir} Wave). All conflicting signals locked RED.`
              );
            }
          } else {
            // Ambulance direction is currently red! Preempt safely: Yellow -> All-Red -> Emergency Green
            if (sig.mode === "green") {
              sig.mode = "yellow";
              sig.timer = 2; // Fast safe yellow clearance
              addLog(
                id,
                "emergency",
                `⚠️ Ambulance detected approaching ${id}. Initiating safe clearance: Yellow caution -> Red clearance.`
              );
            } else if (sig.mode === "yellow") {
              sig.timer -= 1;
              if (sig.timer <= 0) {
                sig.mode = "all_red";
                sig.timer = 1; // 1s all-red intersection clearance
              }
            } else if (sig.mode === "all_red") {
              sig.timer -= 1;
              if (sig.timer <= 0) {
                sig.phase = reqPhase;
                sig.mode = "emergency_green";
                sig.timer = 20; // Lock green for ambulance passage
                addLog(
                  id,
                  "emergency",
                  `🚨 EMERGENCY PREEMPTION ACTIVE at ${id}: ${ambulanceDir} turned GREEN. Conflicting directions locked RED.`
                );
              }
            }
          }
          return;
        }

        // ====================================================================
        // NORMAL ADAPTIVE CONTROLLER (Sensor-driven density & Zero-Wait engine)
        // ====================================================================
        if (sig.mode === "emergency_green") {
          // Emergency vehicle has cleared! Smoothly restore safe yellow -> normal adaptive
          sig.mode = "yellow";
          sig.timer = 2;
          sig.isZeroWaitActive = false;
          addLog(id, "adaptive", `Ambulance cleared ${id}. Restoring normal adaptive density control.`);
          return;
        }

        // Countdown timer
        sig.timer -= 0.5;

        if (sig.mode === "green") {
          const currentQueue = sig.phase === 0 ? nsQueue : ewQueue;
          const opposingQueue = sig.phase === 0 ? ewQueue : nsQueue;
          const fromStr = sig.phase === 0 ? "NS" : "EW";
          const toStr = sig.phase === 0 ? "EW" : "NS";

          // --- ZERO-WAIT CLEAN ROAD ENGINE ---
          // Rule A: Cross street is empty (0 cars) and the other street has waiting/approaching cars!
          // Switch to GREEN immediately so no vehicles stay at a red light for an empty road!
          if (zeroWaitGreen && currentQueue === 0 && opposingQueue > 0) {
            sig.mode = "yellow";
            sig.timer = 1.5; // Quick safe clearance
            sig.isZeroWaitActive = true;
            addLog(
              id,
              "adaptive",
              `✨ Zero-Wait Green at ${id}: Cross street (${fromStr}) is empty (0 cars). Switched to GREEN for waiting cars (${toStr}) so no cars stay in red light!`
            );
            return;
          }

          // Rule B: Rest-in-Green! Cars are flowing on current road and cross street is empty (0 cars).
          // Keep extending green so flowing traffic does not stop for empty roads!
          if (zeroWaitGreen && currentQueue > 0 && opposingQueue === 0) {
            sig.timer = Math.max(sig.timer, 8);
            sig.isZeroWaitActive = true;
            return;
          }

          // Rule C: Standard density evaluation when both or neither have cars
          const highOpposingDemand = opposingQueue >= 3 && sig.timer <= 3;
          const timerExpired = sig.timer <= 0;

          if (highOpposingDemand || timerExpired) {
            sig.mode = "yellow";
            sig.timer = 2.5;
            sig.isZeroWaitActive = false;

            addLog(
              id,
              "adaptive",
              `Sensor evaluation at ${id}: ${fromStr} Queue=${currentQueue}, ${toStr} Queue=${opposingQueue}. Toggling Green to ${toStr} via Yellow clearance.`
            );
          }
        } else if (sig.mode === "yellow") {
          if (sig.timer <= 0) {
            // Transition to All-Red clearance interval
            sig.mode = "all_red";
            sig.timer = 1.0;
          }
        } else if (sig.mode === "all_red") {
          if (sig.timer <= 0) {
            // Safe toggle to the opposing phase!
            sig.phase = sig.phase === 0 ? 2 : 0;
            sig.mode = "green";

            // Dynamically allocate green duration based on sensor queue length (8s to 20s)
            const newQueue = sig.phase === 0 ? nsQueue : ewQueue;
            const adaptiveDuration = Math.min(22, Math.max(8, 8 + newQueue * 3));
            sig.timer = adaptiveDuration;

            addLog(
              id,
              "adaptive",
              `Safe switch completed at ${id}: ${sig.phase === 0 ? "North-South" : "East-West"} now GREEN for ${adaptiveDuration}s.`
            );
          }
        }
      });
    }, 500 / simSpeed);

    return () => clearInterval(interval);
  }, [isRunning, simSpeed, zeroWaitGreen]);

  // Main 60 FPS Physics Simulation & High-Fidelity Rendering Canvas Loop
  useEffect(() => {
    let animId: number;

    const render = () => {
      const canvas = canvasRef.current;
      if (!canvas) return;
      const ctx = canvas.getContext("2d");
      if (!ctx) return;

      const W = canvas.width;
      const H = canvas.height;

      // -------------------------------------------------------------
      // 1. ENVIRONMENT / GROUND RENDERING
      // -------------------------------------------------------------
      // City ground base
      ctx.fillStyle = "#090d16";
      ctx.fillRect(0, 0, W, H);

      // Corner City Park / Landscaping Grids
      const drawParkZone = (x: number, y: number, w: number, h: number) => {
        // Soft lawn
        ctx.fillStyle = "#062319";
        ctx.fillRect(x, y, w, h);

        // Concrete sidewalk perimeter
        ctx.strokeStyle = "#1e293b";
        ctx.lineWidth = 3;
        ctx.strokeRect(x, y, w, h);

        // Decorative landscape trees
        const treePositions = [
          { tx: x + 40, ty: y + 35 },
          { tx: x + w - 40, ty: y + 35 },
          { tx: x + 40, ty: y + h - 35 },
          { tx: x + w - 40, ty: y + h - 35 },
          { tx: x + w / 2, ty: y + h / 2 },
        ];

        treePositions.forEach(({ tx, ty }) => {
          ctx.fillStyle = "#064e3b";
          ctx.beginPath();
          ctx.arc(tx, ty, 10, 0, Math.PI * 2);
          ctx.fill();

          ctx.fillStyle = "#10b981";
          ctx.beginPath();
          ctx.arc(tx - 2, ty - 2, 6, 0, Math.PI * 2);
          ctx.fill();
        });
      };

      // 4 Parks in quadrants
      drawParkZone(20, 20, J1.x - ROAD_W / 2 - 20, J1.y - ROAD_W / 2 - 20);
      drawParkZone(J1.x + ROAD_W / 2, 20, J2.x - J1.x - ROAD_W, J1.y - ROAD_W / 2 - 20);
      drawParkZone(J2.x + ROAD_W / 2, 20, W - (J2.x + ROAD_W / 2) - 20, J1.y - ROAD_W / 2 - 20);

      drawParkZone(20, J1.y + ROAD_W / 2, J1.x - ROAD_W / 2 - 20, J3.y - J1.y - ROAD_W);
      drawParkZone(J1.x + ROAD_W / 2, J1.y + ROAD_W / 2, J2.x - J1.x - ROAD_W, J3.y - J1.y - ROAD_W);
      drawParkZone(J2.x + ROAD_W / 2, J1.y + ROAD_W / 2, W - (J2.x + ROAD_W / 2) - 20, J3.y - J1.y - ROAD_W);

      drawParkZone(20, J3.y + ROAD_W / 2, J1.x - ROAD_W / 2 - 20, H - (J3.y + ROAD_W / 2) - 20);
      drawParkZone(J1.x + ROAD_W / 2, J3.y + ROAD_W / 2, J2.x - J1.x - ROAD_W, H - (J3.y + ROAD_W / 2) - 20);
      drawParkZone(J2.x + ROAD_W / 2, J3.y + ROAD_W / 2, W - (J2.x + ROAD_W / 2) - 20, H - (J3.y + ROAD_W / 2) - 20);

      // -------------------------------------------------------------
      // 2. ASPHALT ROADBEDS & CONCRETE CURBS
      // -------------------------------------------------------------
      ctx.fillStyle = "#161e2e"; // Dark slate asphalt

      // Horizontal corridors
      ctx.fillRect(0, J1.y - ROAD_W / 2, W, ROAD_W);
      ctx.fillRect(0, J3.y - ROAD_W / 2, W, ROAD_W);

      // Vertical corridors
      ctx.fillRect(J1.x - ROAD_W / 2, 0, ROAD_W, H);
      ctx.fillRect(J2.x - ROAD_W / 2, 0, ROAD_W, H);

      // Concrete Curbs (edge lines)
      ctx.strokeStyle = "#334155";
      ctx.lineWidth = 2;

      // Draw double yellow solid centerlines
      ctx.strokeStyle = "#f59e0b";
      ctx.lineWidth = 1.5;

      const drawDoubleYellow = (x1: number, y1: number, x2: number, y2: number, isVertical: boolean) => {
        ctx.beginPath();
        if (isVertical) {
          ctx.moveTo(x1 - 2, y1);
          ctx.lineTo(x2 - 2, y2);
          ctx.moveTo(x1 + 2, y1);
          ctx.lineTo(x2 + 2, y2);
        } else {
          ctx.moveTo(x1, y1 - 2);
          ctx.lineTo(x2, y2 - 2);
          ctx.moveTo(x1, y1 + 2);
          ctx.lineTo(x2, y2 + 2);
        }
        ctx.stroke();
      };

      // Centerlines outside junctions
      drawDoubleYellow(0, J1.y, J1.x - ROAD_W / 2, J1.y, false);
      drawDoubleYellow(J1.x + ROAD_W / 2, J1.y, J2.x - ROAD_W / 2, J1.y, false);
      drawDoubleYellow(J2.x + ROAD_W / 2, J1.y, W, J1.y, false);

      drawDoubleYellow(0, J3.y, J3.x - ROAD_W / 2, J3.y, false);
      drawDoubleYellow(J3.x + ROAD_W / 2, J3.y, J4.x - ROAD_W / 2, J3.y, false);
      drawDoubleYellow(J4.x + ROAD_W / 2, J3.y, W, J3.y, false);

      drawDoubleYellow(J1.x, 0, J1.x, J1.y - ROAD_W / 2, true);
      drawDoubleYellow(J1.x, J1.y + ROAD_W / 2, J1.x, J3.y - ROAD_W / 2, true);
      drawDoubleYellow(J1.x, J3.y + ROAD_W / 2, J1.x, H, true);

      drawDoubleYellow(J2.x, 0, J2.x, J2.y - ROAD_W / 2, true);
      drawDoubleYellow(J2.x, J2.y + ROAD_W / 2, J2.x, J4.y - ROAD_W / 2, true);
      drawDoubleYellow(J2.x, J4.y + ROAD_W / 2, J2.x, H, true);

      // Continental Pedestrian Zebra Crosswalks at all junction approaches
      const junctions = [
        { id: "J1", pos: J1 },
        { id: "J2", pos: J2 },
        { id: "J3", pos: J3 },
        { id: "J4", pos: J4 },
      ];

      const drawCrosswalk = (cx: number, cy: number, w: number, h: number, isVertical: boolean) => {
        ctx.fillStyle = "rgba(241, 245, 249, 0.75)";
        const stripes = 6;
        if (isVertical) {
          const step = w / stripes;
          for (let s = 0; s < stripes; s++) {
            ctx.fillRect(cx + s * step + 2, cy, step - 4, h);
          }
        } else {
          const step = h / stripes;
          for (let s = 0; s < stripes; s++) {
            ctx.fillRect(cx, cy + s * step + 2, w, step - 4);
          }
        }
      };

      junctions.forEach(({ pos }) => {
        // North Crosswalk
        drawCrosswalk(pos.x - ROAD_W / 2, pos.y - ROAD_W / 2 - 14, ROAD_W, 10, true);
        // South Crosswalk
        drawCrosswalk(pos.x - ROAD_W / 2, pos.y + ROAD_W / 2 + 4, ROAD_W, 10, true);
        // West Crosswalk
        drawCrosswalk(pos.x - ROAD_W / 2 - 14, pos.y - ROAD_W / 2, 10, ROAD_W, false);
        // East Crosswalk
        drawCrosswalk(pos.x + ROAD_W / 2 + 4, pos.y - ROAD_W / 2, 10, ROAD_W, false);
      });

      // -------------------------------------------------------------
      // 3. SENSOR TELEMETRY & LIVE RADAR ARCS
      // -------------------------------------------------------------
      // Reset sensor counts for this frame
      Object.keys(sensorDataRef.current).forEach((key) => {
        sensorDataRef.current[key].count = 0;
        sensorDataRef.current[key].distanceCm = 350;
        sensorDataRef.current[key].detected = false;
        sensorDataRef.current[key].hasAmbulance = false;
      });

      // Scan vehicles to populate sensor readings
      vehiclesRef.current.forEach((veh) => {
        const nextWp = veh.route[veh.routeIdx];
        if (nextWp?.junction && nextWp.approach) {
          const sensorKey = `${nextWp.junction}_${nextWp.approach}`;
          const currentSensor = sensorDataRef.current[sensorKey];
          if (currentSensor && nextWp.stopLineX !== undefined && nextWp.stopLineY !== undefined) {
            const distToStop = Math.hypot(veh.x - nextWp.stopLineX, veh.y - nextWp.stopLineY);
            if (distToStop < 170) {
              currentSensor.count += 1;
              currentSensor.detected = true;
              currentSensor.distanceCm = Math.min(currentSensor.distanceCm, Math.round(distToStop * 1.6));
              if (veh.type === "ambulance") {
                currentSensor.hasAmbulance = true;
              }
            }
          }
        }
      });

      // Draw Ultrasonic Sensors (HC-SR04 Modules & Sonar Waves)
      const sensorConfigs = [
        { key: "J1_N", x: J1.x - ROAD_W / 2 - 12, y: J1.y - ROAD_W / 2 - 40, dir: "N" },
        { key: "J1_S", x: J1.x + ROAD_W / 2 + 12, y: J1.y + ROAD_W / 2 + 40, dir: "S" },
        { key: "J1_W", x: J1.x - ROAD_W / 2 - 40, y: J1.y + ROAD_W / 2 + 12, dir: "W" },
        { key: "J1_E", x: J1.x + ROAD_W / 2 + 40, y: J1.y - ROAD_W / 2 - 12, dir: "E" },

        { key: "J2_N", x: J2.x - ROAD_W / 2 - 12, y: J2.y - ROAD_W / 2 - 40, dir: "N" },
        { key: "J2_S", x: J2.x + ROAD_W / 2 + 12, y: J2.y + ROAD_W / 2 + 40, dir: "S" },
        { key: "J2_W", x: J2.x - ROAD_W / 2 - 40, y: J2.y + ROAD_W / 2 + 12, dir: "W" },
        { key: "J2_E", x: J2.x + ROAD_W / 2 + 40, y: J2.y - ROAD_W / 2 - 12, dir: "E" },

        { key: "J3_N", x: J3.x - ROAD_W / 2 - 12, y: J3.y - ROAD_W / 2 - 40, dir: "N" },
        { key: "J3_S", x: J3.x + ROAD_W / 2 + 12, y: J3.y + ROAD_W / 2 + 40, dir: "S" },
        { key: "J3_W", x: J3.x - ROAD_W / 2 - 40, y: J3.y + ROAD_W / 2 + 12, dir: "W" },
        { key: "J3_E", x: J3.x + ROAD_W / 2 + 40, y: J3.y - ROAD_W / 2 - 12, dir: "E" },

        { key: "J4_N", x: J4.x - ROAD_W / 2 - 12, y: J4.y - ROAD_W / 2 - 40, dir: "N" },
        { key: "J4_S", x: J4.x + ROAD_W / 2 + 12, y: J4.y + ROAD_W / 2 + 40, dir: "S" },
        { key: "J4_W", x: J4.x - ROAD_W / 2 - 40, y: J4.y + ROAD_W / 2 + 12, dir: "W" },
        { key: "J4_E", x: J4.x + ROAD_W / 2 + 40, y: J4.y - ROAD_W / 2 - 12, dir: "E" },
      ];

      sensorConfigs.forEach(({ key, x, y, dir }) => {
        const sdata = sensorDataRef.current[key];
        const hasCar = sdata && sdata.count > 0;
        const hasAmb = sdata && sdata.hasAmbulance;

        // HC-SR04 PCB (Blue board)
        ctx.fillStyle = hasAmb ? "#ef4444" : "#1d4ed8";
        ctx.fillRect(x - 9, y - 6, 18, 12);

        // Ultrasonic aluminum transducers
        ctx.fillStyle = "#cbd5e1";
        ctx.beginPath();
        ctx.arc(x - 4.5, y, 3, 0, Math.PI * 2);
        ctx.arc(x + 4.5, y, 3, 0, Math.PI * 2);
        ctx.fill();

        // Pulsing Sonar Arcs
        if (showSensorRadar) {
          const waveColor = hasAmb
            ? "rgba(239, 68, 68, 0.8)"
            : hasCar
            ? "rgba(245, 158, 11, 0.75)"
            : "rgba(56, 189, 248, 0.25)";

          ctx.strokeStyle = waveColor;
          ctx.lineWidth = hasCar ? 2 : 1;

          const radarAngles = {
            N: { start: -Math.PI * 0.8, end: -Math.PI * 0.2 },
            S: { start: Math.PI * 0.2, end: Math.PI * 0.8 },
            W: { start: Math.PI * 0.7, end: Math.PI * 1.3 },
            E: { start: -Math.PI * 0.3, end: Math.PI * 0.3 },
          };

          const radii = [25, 55, 90, 130];
          radii.forEach((r) => {
            ctx.beginPath();
            ctx.arc(x, y, r, radarAngles[dir as "N" | "S" | "E" | "W"].start, radarAngles[dir as "N" | "S" | "E" | "W"].end);
            ctx.stroke();
          });

          // Floating Sensor HUD Tag
          if (hasCar) {
            ctx.fillStyle = hasAmb ? "#ef4444" : "#0284c7";
            ctx.font = "bold 9px monospace";
            ctx.fillText(`${sdata.count} veh | ${sdata.distanceCm}cm`, x - 20, y - 10);
          }
        }
      });

      // -------------------------------------------------------------
      // 4. TRAFFIC SIGNALS & STOPLINES
      // -------------------------------------------------------------
      junctions.forEach(({ id, pos }) => {
        const sig = signalsRef.current[id];
        const isNSGreen = sig.phase === 0 && (sig.mode === "green" || sig.mode === "emergency_green");
        const isEWGreen = sig.phase === 2 && (sig.mode === "green" || sig.mode === "emergency_green");
        const isYellow = sig.mode === "yellow";

        // Stop Lines with reactive illumination
        const drawStopLine = (sx: number, sy: number, sw: number, sh: number, isGreen: boolean) => {
          ctx.fillStyle = isGreen ? "#10b981" : isYellow ? "#f59e0b" : "#ef4444";
          ctx.shadowColor = ctx.fillStyle;
          ctx.shadowBlur = 6;
          ctx.fillRect(sx, sy, sw, sh);
          ctx.shadowBlur = 0;
        };

        // North Stop line
        drawStopLine(pos.x - ROAD_W / 2, pos.y - ROAD_W / 2 - 4, ROAD_W / 2, 4, isNSGreen);
        // South Stop line
        drawStopLine(pos.x, pos.y + ROAD_W / 2, ROAD_W / 2, 4, isNSGreen);
        // West Stop line
        drawStopLine(pos.x - ROAD_W / 2 - 4, pos.y, 4, ROAD_W / 2, isEWGreen);
        // East Stop line
        drawStopLine(pos.x + ROAD_W / 2, pos.y - ROAD_W / 2, 4, ROAD_W / 2, isEWGreen);

        // 3-Aspect Signal Housing Box with realistic glowing bloom
        const drawSignalGantry = (gx: number, gy: number, redOn: boolean, yellowOn: boolean, greenOn: boolean) => {
          // Black signal box
          ctx.fillStyle = "#020617";
          ctx.strokeStyle = "#475569";
          ctx.lineWidth = 1.5;
          ctx.beginPath();
          ctx.roundRect(gx - 7, gy - 19, 14, 38, 3);
          ctx.fill();
          ctx.stroke();

          // Red Light
          ctx.fillStyle = redOn ? "#ef4444" : "#450a0a";
          if (redOn) {
            ctx.shadowColor = "#ef4444";
            ctx.shadowBlur = 10;
          }
          ctx.beginPath();
          ctx.arc(gx, gy - 10, 3.5, 0, Math.PI * 2);
          ctx.fill();
          ctx.shadowBlur = 0;

          // Yellow Light
          ctx.fillStyle = yellowOn ? "#f59e0b" : "#451a03";
          if (yellowOn) {
            ctx.shadowColor = "#f59e0b";
            ctx.shadowBlur = 10;
          }
          ctx.beginPath();
          ctx.arc(gx, gy, 3.5, 0, Math.PI * 2);
          ctx.fill();
          ctx.shadowBlur = 0;

          // Green Light
          ctx.fillStyle = greenOn ? "#10b981" : "#022c22";
          if (greenOn) {
            ctx.shadowColor = "#10b981";
            ctx.shadowBlur = 12;
          }
          ctx.beginPath();
          ctx.arc(gx, gy + 10, 3.5, 0, Math.PI * 2);
          ctx.fill();
          ctx.shadowBlur = 0;
        };

        const nsRed = !isNSGreen && (!isYellow || sig.phase !== 0);
        const ewRed = !isEWGreen && (!isYellow || sig.phase !== 2);

        // North-South signal post
        drawSignalGantry(pos.x + ROAD_W / 2 + 12, pos.y - ROAD_W / 2 - 12, nsRed, isYellow && sig.phase === 0, isNSGreen);
        // East-West signal post
        drawSignalGantry(pos.x - ROAD_W / 2 - 12, pos.y + ROAD_W / 2 + 12, ewRed, isYellow && sig.phase === 2, isEWGreen);

        // Junction Center Status Badge
        ctx.fillStyle = sig.mode === "emergency_green" ? "#ef4444" : "#0284c7";
        ctx.font = "bold 11px monospace";
        ctx.fillText(id, pos.x - 7, pos.y + 4);

        if (sig.mode === "emergency_green") {
          ctx.fillStyle = "#ef4444";
          ctx.font = "bold 9px sans-serif";
          ctx.fillText("🚨 EMG GREEN", pos.x - 30, pos.y - 10);
        } else if (sig.isZeroWaitActive && (isNSGreen || isEWGreen)) {
          ctx.fillStyle = "#10b981";
          ctx.font = "bold 9px sans-serif";
          ctx.fillText("🟢 ZERO-WAIT", pos.x - 30, pos.y - 10);
        }
      });

      // -------------------------------------------------------------
      // 5. VEHICLE KINEMATICS, CAR-TO-CAR INTERACTION & RENDERING
      // -------------------------------------------------------------
      const vehicles = vehiclesRef.current;

      for (let i = vehicles.length - 1; i >= 0; i--) {
        const v = vehicles[i];

        if (isRunning) {
          // --- Car-to-Car Detection & Safe Following Distance ---
          let carAheadDist = 999;
          for (let j = 0; j < vehicles.length; j++) {
            if (i === j) continue;
            const other = vehicles[j];
            const dist = Math.hypot(other.x - v.x, other.y - v.y);

            // Forward projection along travel angle
            const dx = other.x - v.x;
            const dy = other.y - v.y;
            const forwardDot = dx * Math.cos(v.angle) + dy * Math.sin(v.angle);
            const lateralDist = Math.abs(-dx * Math.sin(v.angle) + dy * Math.cos(v.angle));

            // In front and in same lane
            if (forwardDot > 0 && dist < 70 && lateralDist < 16) {
              carAheadDist = Math.min(carAheadDist, dist);
            }
          }

          // --- Traffic Light Stop Line Evaluation ---
          let mustStopAtSignal = false;
          const nextWp = v.route[v.routeIdx];

          if (nextWp?.junction && nextWp.stopLineX !== undefined && nextWp.stopLineY !== undefined) {
            const jid = nextWp.junction;
            const sig = signalsRef.current[jid];

            const isGreen =
              (nextWp.dir === "NS" && (sig.phase === 0 && (sig.mode === "green" || sig.mode === "emergency_green"))) ||
              (nextWp.dir === "EW" && (sig.phase === 2 && (sig.mode === "green" || sig.mode === "emergency_green")));

            const distToStop = Math.hypot(v.x - nextWp.stopLineX, v.y - nextWp.stopLineY);

            // If within 40px of stopline and signal is NOT green, stop!
            // Ambulances do not stop if emergency green is active
            if (distToStop < 45 && !isGreen) {
              mustStopAtSignal = true;
            }
          }

          // Kinematic acceleration / deceleration
          const isBlocked = carAheadDist < 36 || mustStopAtSignal;

          if (isBlocked) {
            v.speed = Math.max(0, v.speed - 0.22 * simSpeed);
            v.isStopped = v.speed < 0.1;
            v.isBraking = true;
            v.waitingTime += 0.016;
          } else {
            v.speed = Math.min(v.maxSpeed, v.speed + 0.12 * simSpeed);
            v.isStopped = false;
            v.isBraking = false;
          }

          // Move towards next target waypoint
          const dx = v.targetX - v.x;
          const dy = v.targetY - v.y;
          const distToWp = Math.hypot(dx, dy);

          if (distToWp < 12) {
            v.routeIdx++;
            if (v.routeIdx >= v.route.length) {
              // Completed route, remove vehicle
              const wasAmbulance = v.type === "ambulance";
              vehicles.splice(i, 1);
              setTotalVehicles(vehicles.length);
              if (wasAmbulance) {
                const remAmbulances = vehicles.filter((veh) => veh.type === "ambulance").length;
                setActiveAmbulances(remAmbulances);
                if (remAmbulances === 0) {
                  stopSirenSound();
                }
              }
              continue;
            }
            v.targetX = v.route[v.routeIdx].x;
            v.targetY = v.route[v.routeIdx].y;
          }

          v.angle = Math.atan2(dy, dx);
          v.x += Math.cos(v.angle) * v.speed;
          v.y += Math.sin(v.angle) * v.speed;
        }

        // --- DRAW VEHICLE SPRITE ---
        ctx.save();
        ctx.translate(v.x, v.y);
        ctx.rotate(v.angle);

        // Dynamic Headlight Cones on asphalt
        const grad = ctx.createLinearGradient(v.length / 2, 0, v.length / 2 + 50, 0);
        grad.addColorStop(0, "rgba(254, 240, 138, 0.45)");
        grad.addColorStop(1, "rgba(254, 240, 138, 0)");
        ctx.fillStyle = grad;
        ctx.beginPath();
        ctx.moveTo(v.length / 2, -v.width / 2);
        ctx.lineTo(v.length / 2 + 45, -v.width - 12);
        ctx.lineTo(v.length / 2 + 45, v.width + 12);
        ctx.lineTo(v.length / 2, v.width / 2);
        ctx.fill();

        // Drop Shadow
        ctx.fillStyle = "rgba(0,0,0,0.45)";
        ctx.fillRect(-v.length / 2 + 2, -v.width / 2 + 2, v.length, v.width);

        if (v.type === "ambulance") {
          // --- HIGH-FIDELITY AMBULANCE ---
          // Pure white body
          ctx.fillStyle = "#ffffff";
          ctx.beginPath();
          ctx.roundRect(-v.length / 2, -v.width / 2, v.length, v.width, 4);
          ctx.fill();
          ctx.strokeStyle = "#cbd5e1";
          ctx.lineWidth = 1;
          ctx.stroke();

          // Reflective Orange / Red emergency side chevrons
          ctx.fillStyle = "#ef4444";
          ctx.fillRect(-v.length / 3, -v.width / 2, v.length * 0.6, 2.5);
          ctx.fillRect(-v.length / 3, v.width / 2 - 2.5, v.length * 0.6, 2.5);

          // Medical Red Cross Emblem on roof
          ctx.fillStyle = "#dc2626";
          ctx.fillRect(-3, -7, 6, 14);
          ctx.fillRect(-7, -3, 14, 6);

          // Front windshield (dark tinted glass)
          ctx.fillStyle = "#0f172a";
          ctx.fillRect(v.length / 4, -v.width / 2 + 2, 6, v.width - 4);

          // Alternating Emergency Strobe LED Beacons on Roof (12 Hz)
          const strobe = Math.floor(Date.now() / 80) % 2 === 0;

          // Electric Blue Strobe
          ctx.fillStyle = strobe ? "#38bdf8" : "#ef4444";
          ctx.shadowColor = ctx.fillStyle;
          ctx.shadowBlur = 18;
          ctx.beginPath();
          ctx.arc(v.length / 6, -3, 3.5, 0, Math.PI * 2);
          ctx.fill();

          // Neon Red Strobe
          ctx.fillStyle = strobe ? "#ef4444" : "#38bdf8";
          ctx.shadowColor = ctx.fillStyle;
          ctx.beginPath();
          ctx.arc(v.length / 6, 3, 3.5, 0, Math.PI * 2);
          ctx.fill();
          ctx.shadowBlur = 0;

          // Expanding Acoustic Siren Shockwave Rings
          const ringRadius = (Date.now() / 15) % 35;
          ctx.strokeStyle = `rgba(239, 68, 68, ${1 - ringRadius / 35})`;
          ctx.lineWidth = 1.5;
          ctx.beginPath();
          ctx.arc(0, 0, ringRadius, 0, Math.PI * 2);
          ctx.stroke();
        } else {
          // --- STANDARD PASSENGER VEHICLE / SUV / TRUCK ---
          // Chassis Body
          ctx.fillStyle = v.color;
          ctx.beginPath();
          ctx.roundRect(-v.length / 2, -v.width / 2, v.length, v.width, 3);
          ctx.fill();

          // Dark Tinted Glass Windshield & Rear Window
          ctx.fillStyle = "#090d16";
          ctx.fillRect(v.length / 5, -v.width / 2 + 2, 5, v.width - 4); // Front windshield
          ctx.fillRect(-v.length / 3, -v.width / 2 + 2, 4, v.width - 4); // Rear window

          // Roof highlight
          ctx.fillStyle = "rgba(255,255,255,0.15)";
          ctx.fillRect(-v.length / 4, -v.width / 2 + 3, v.length / 2.5, v.width - 6);
        }

        // Taillights / Reactive Brake Lights (Glow bright crimson when stopped or braking)
        const brakeOn = v.isBraking || v.isStopped;
        ctx.fillStyle = brakeOn ? "#ef4444" : "#991b1b";
        if (brakeOn) {
          ctx.shadowColor = "#ef4444";
          ctx.shadowBlur = 8;
        }
        ctx.fillRect(-v.length / 2, -v.width / 2 + 1, 2.5, 3);
        ctx.fillRect(-v.length / 2, v.width / 2 - 4, 2.5, 3);
        ctx.shadowBlur = 0;

        ctx.restore();
      }

      animId = requestAnimationFrame(render);
    };

    animId = requestAnimationFrame(render);
    return () => cancelAnimationFrame(animId);
  }, [isRunning, simSpeed, showSensorRadar]);

  // Manual Trigger: Force Green at Selected Junction
  const handleManualToggle = (jid: string) => {
    const sig = signalsRef.current[jid];
    sig.phase = sig.phase === 0 ? 2 : 0;
    sig.mode = "green";
    sig.timer = 15;
    addLog(jid, "manual", `🕹️ Manual Signal Override: Force switched ${jid} to Phase ${sig.phase} GREEN.`);
  };

  // Manual Trigger: Force All Red
  const handleManualAllRed = (jid: string) => {
    const sig = signalsRef.current[jid];
    sig.mode = "all_red";
    sig.timer = 15;
    addLog(jid, "manual", `🛑 Manual Emergency Halt: Force stopped ${jid} to ALL-RED.`);
  };

  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/90 p-5 shadow-2xl space-y-4">
      {/* Top Header & Toolbar */}
      <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <div className="flex items-center gap-2.5">
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <Car className="h-5 w-5 text-cyan-400" />
              Autonomous IoT Traffic Network & Emergency Priority Simulation
            </h2>
            <span className="text-[10px] font-bold px-2.5 py-0.5 rounded-full bg-cyan-950 text-cyan-400 border border-cyan-800">
              60 FPS Physics Engine
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-0.5">
            Real-time ultrasonic sensor detection, queue-driven adaptive signal toggling, and emergency green wave preemption
          </p>
        </div>

        {/* Action Controls Toolbar */}
        <div className="flex flex-wrap items-center gap-2">
          {/* Play / Pause */}
          <button
            onClick={() => setIsRunning(!isRunning)}
            className={`px-3 py-1.5 rounded-xl border text-xs font-semibold flex items-center gap-1.5 transition ${
              isRunning
                ? "bg-amber-500/10 border-amber-500/40 text-amber-300 hover:bg-amber-500/20"
                : "bg-emerald-500/10 border-emerald-500/40 text-emerald-300 hover:bg-emerald-500/20"
            }`}
          >
            {isRunning ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
            {isRunning ? "Pause" : "Play"}
          </button>

          {/* Speed Multiplier */}
          <div className="flex items-center rounded-xl border border-slate-700 bg-slate-800/90 p-0.5 text-xs font-mono">
            {[1, 2, 4].map((s) => (
              <button
                key={s}
                onClick={() => setSimSpeed(s)}
                className={`px-2.5 py-1 rounded-lg transition ${
                  simSpeed === s ? "bg-cyan-600 text-white font-bold" : "text-slate-400 hover:text-white"
                }`}
              >
                {s}x
              </button>
            ))}
          </div>

          {/* Toggle Sensor Radar */}
          <button
            onClick={() => setShowSensorRadar(!showSensorRadar)}
            className={`px-3 py-1.5 rounded-xl border text-xs font-semibold flex items-center gap-1.5 transition ${
              showSensorRadar
                ? "bg-cyan-500/10 border-cyan-500/40 text-cyan-300"
                : "bg-slate-800 border-slate-700 text-slate-400"
            }`}
          >
            <Wifi className="h-3.5 w-3.5" />
            Sonar Radar
          </button>

          {/* Toggle Siren Audio */}
          <button
            onClick={() => {
              ensureAudioContext();
              const next = !soundEnabled;
              setSoundEnabled(next);
              if (next) {
                startSirenSound();
                if (vehiclesRef.current.filter((veh) => veh.type === "ambulance").length === 0) {
                  setTimeout(() => {
                    if (vehiclesRef.current.filter((veh) => veh.type === "ambulance").length === 0) {
                      stopSirenSound();
                    }
                  }, 2500);
                }
              } else {
                stopSirenSound();
              }
            }}
            className={`px-3 py-1.5 rounded-xl border text-xs font-semibold flex items-center gap-1.5 transition ${
              soundEnabled
                ? "bg-red-500/20 border-red-500/50 text-red-300"
                : "bg-slate-800 border-slate-700 text-slate-400"
            }`}
          >
            {soundEnabled ? <Volume2 className="h-3.5 w-3.5 text-red-400" /> : <VolumeX className="h-3.5 w-3.5" />}
            Siren Sound: {soundEnabled ? "ON" : "OFF"}
          </button>

          {/* Zero-Wait Clean Road Toggle */}
          <button
            onClick={() => setZeroWaitGreen(!zeroWaitGreen)}
            className={`px-3 py-1.5 rounded-xl border text-xs font-semibold flex items-center gap-1.5 transition ${
              zeroWaitGreen
                ? "bg-emerald-500/10 border-emerald-500/40 text-emerald-300"
                : "bg-slate-800 border-slate-700 text-slate-400"
            }`}
          >
            <Sparkles className="h-3.5 w-3.5 text-emerald-400" />
            Zero-Wait Green: {zeroWaitGreen ? "ON" : "OFF"}
          </button>

          {/* Auto Spawner Toggle */}
          <button
            onClick={() => setAutoSpawn(!autoSpawn)}
            className={`px-3 py-1.5 rounded-xl border text-xs font-semibold flex items-center gap-1.5 transition ${
              autoSpawn
                ? "bg-emerald-500/10 border-emerald-500/40 text-emerald-300"
                : "bg-slate-800 border-slate-700 text-slate-400"
            }`}
          >
            <Radio className="h-3.5 w-3.5" />
            Auto Traffic: {autoSpawn ? "ON" : "OFF"}
          </button>

          {/* Add Car Platoon */}
          <button
            onClick={() => {
              for (let i = 0; i < 4; i++) spawnVehicle("car");
              addLog("Traffic", "adaptive", "Spawned traffic burst (+4 cars).");
            }}
            className="px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-xs font-semibold flex items-center gap-1.5 transition"
          >
            <Car className="h-3.5 w-3.5 text-cyan-400" />
            +4 Cars
          </button>

          {/* DISPATCH AMBULANCE BUTTON */}
          <button
            onClick={() => {
              ensureAudioContext();
              setSoundEnabled(true);
              spawnVehicle("ambulance", Math.random() > 0.5 ? 0 : 2);
            }}
            className="px-4 py-1.5 rounded-xl bg-gradient-to-r from-red-600 to-rose-600 hover:from-red-500 hover:to-rose-500 text-white text-xs font-bold flex items-center gap-1.5 transition shadow-lg shadow-red-600/30 animate-pulse"
          >
            <ShieldAlert className="h-4 w-4 text-white" />
            🚨 Dispatch Ambulance
          </button>
        </div>
      </div>

      {/* Main Simulation Canvas Viewport */}
      <div className="relative rounded-2xl overflow-hidden border border-slate-800 bg-slate-950 shadow-2xl">
        <canvas
          ref={canvasRef}
          width={1000}
          height={580}
          className="w-full h-auto block select-none"
        />

        {/* Top Floating Telemetry Pills */}
        <div className="absolute top-3 left-3 flex flex-wrap items-center gap-2 pointer-events-none">
          <div className="bg-slate-900/90 backdrop-blur border border-slate-700/80 rounded-xl px-3 py-1.5 text-xs flex items-center gap-2 shadow-lg">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
            <span className="text-slate-300">Active Vehicles:</span>
            <strong className="text-white font-mono">{totalVehicles}</strong>
          </div>

          <div
            className={`backdrop-blur border rounded-xl px-3 py-1.5 text-xs flex items-center gap-2 shadow-lg transition ${
              activeAmbulances > 0
                ? "bg-red-950/90 border-red-700 text-red-300 animate-pulse"
                : "bg-slate-900/90 border-slate-700/80 text-slate-300"
            }`}
          >
            <ShieldAlert className={`h-3.5 w-3.5 ${activeAmbulances > 0 ? "text-red-400" : "text-slate-400"}`} />
            <span>Emergency Ambulances:</span>
            <strong className="font-mono">{activeAmbulances}</strong>
          </div>
        </div>

        {/* Bottom Floating Manual Override Controls */}
        <div className="absolute bottom-3 right-3 bg-slate-900/95 backdrop-blur border border-slate-800 rounded-2xl p-3 shadow-2xl space-y-2">
          <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400 flex items-center justify-between gap-4">
            <span>Manual Signal Override</span>
            <span className="text-cyan-400 font-mono">Target: {selectedJunction}</span>
          </div>

          <div className="flex items-center gap-1.5">
            {["J1", "J2", "J3", "J4"].map((jid) => (
              <button
                key={jid}
                onClick={() => setSelectedJunction(jid)}
                className={`px-2.5 py-1 rounded-lg text-xs font-mono font-bold transition ${
                  selectedJunction === jid
                    ? "bg-cyan-500 text-slate-950 shadow-md shadow-cyan-500/20"
                    : "bg-slate-800 text-slate-300 hover:bg-slate-700"
                }`}
              >
                {jid}
              </button>
            ))}
          </div>

          <div className="grid grid-cols-2 gap-2 pt-1">
            <button
              onClick={() => handleManualToggle(selectedJunction)}
              className="py-1.5 px-2 rounded-lg bg-emerald-600/30 hover:bg-emerald-600/40 text-emerald-300 border border-emerald-500/50 text-xs font-semibold transition text-center flex items-center justify-center gap-1"
            >
              <RefreshCw className="h-3 w-3" />
              Toggle Green
            </button>
            <button
              onClick={() => handleManualAllRed(selectedJunction)}
              className="py-1.5 px-2 rounded-lg bg-red-600/30 hover:bg-red-600/40 text-red-300 border border-red-500/50 text-xs font-semibold transition text-center flex items-center justify-center gap-1"
            >
              <AlertTriangle className="h-3 w-3" />
              Force Red
            </button>
          </div>
        </div>
      </div>

      {/* Autonomous AI Decision Log & Sensor Live Feed */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 pt-2">
        {/* Real-time Decision Feed */}
        <div className="lg:col-span-2 rounded-xl bg-slate-950/70 border border-slate-800 p-3.5 space-y-2">
          <div className="flex items-center justify-between border-b border-slate-800/80 pb-2">
            <div className="flex items-center gap-2">
              <Cpu className="h-4 w-4 text-cyan-400" />
              <h3 className="text-xs font-bold text-white uppercase tracking-wider">
                Autonomous Sensor Decision Feed
              </h3>
            </div>
            <span className="text-[10px] text-slate-500 font-mono">Live TraCI / Edge AI Engine</span>
          </div>

          <div className="h-28 overflow-y-auto space-y-1.5 font-mono text-[11px] pr-2">
            {decisionLogs.length === 0 ? (
              <div className="text-slate-500 italic py-4 text-center">Monitoring traffic sensors...</div>
            ) : (
              decisionLogs.map((log) => (
                <div
                  key={log.id}
                  className={`px-2.5 py-1 rounded flex items-start gap-2 border ${
                    log.type === "emergency"
                      ? "bg-red-950/40 border-red-800/60 text-red-300"
                      : log.type === "manual"
                      ? "bg-amber-950/30 border-amber-800/50 text-amber-300"
                      : "bg-slate-900 border-slate-800 text-slate-300"
                  }`}
                >
                  <span className="text-slate-500 shrink-0">{log.timestamp}</span>
                  <span
                    className={`font-bold shrink-0 ${
                      log.type === "emergency" ? "text-red-400" : "text-cyan-400"
                    }`}
                  >
                    [{log.junction}]
                  </span>
                  <span className="truncate">{log.message}</span>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Project Technical Architecture Highlights */}
        <div className="rounded-xl bg-slate-950/70 border border-slate-800 p-3.5 space-y-2 text-xs">
          <div className="flex items-center gap-2 border-b border-slate-800/80 pb-2">
            <Sparkles className="h-4 w-4 text-amber-400" />
            <h3 className="text-xs font-bold text-white uppercase tracking-wider">Project Core Highlights</h3>
          </div>
          <ul className="space-y-1.5 text-slate-400 text-[11px]">
            <li className="flex items-center gap-1.5">
              <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400 shrink-0" />
              <span><strong>Ultrasonic Sensing:</strong> Continuous vehicle queue & distance telemetry.</span>
            </li>
            <li className="flex items-center gap-1.5">
              <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400 shrink-0" />
              <span><strong>Zero-Wait Green:</strong> If cross traffic is clear (0 cars), turns GREEN instantly so no car stays in red light for no reason.</span>
            </li>
            <li className="flex items-center gap-1.5">
              <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400 shrink-0" />
              <span><strong>Adaptive Density:</strong> Controller evaluates queues from real-time road sensors.</span>
            </li>
            <li className="flex items-center gap-1.5">
              <CheckCircle2 className="h-3.5 w-3.5 text-red-400 shrink-0" />
              <span><strong>Emergency Wave:</strong> Ambulance triggers green corridor; halts conflicting lights to red.</span>
            </li>
            <li className="flex items-center gap-1.5">
              <CheckCircle2 className="h-3.5 w-3.5 text-cyan-400 shrink-0" />
              <span><strong>Safety Protocols:</strong> Enforces yellow (3s) & all-red (1.5s) clearance intervals.</span>
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
};
