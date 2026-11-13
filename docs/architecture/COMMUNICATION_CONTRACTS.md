# FlowSync Communication Contracts

## 1. General Rules

- All timestamps use UTC ISO 8601 format.
- All messages include a schema version.
- All intersection identifiers use intersection_1 through intersection_4.
- All message payloads use JSON unless otherwise specified.
- Messages must be validated before processing.
- Simulation ground truth and AI inference must remain separate.

## 2. Simulation Telemetry

Producer: SUMO / TraCI bridge
Consumer: Traffic Intelligence / Backend

{
  "schema_version": "1.0",
  "event_type": "simulation.telemetry",
  "timestamp": "2026-01-01T10:00:00Z",
  "intersection_id": "intersection_1",
  "simulation_time": 120.5,
  "lanes": [
    {
      "lane_id": "lane_1",
      "vehicle_count": 12,
      "queue_length": 6,
      "occupancy": 0.72,
      "average_waiting_time": 18.4
    }
  ]
}

## 3. AI Detection Event

Producer: Edge AI
Consumer: Traffic Intelligence / Backend

{
  "schema_version": "1.0",
  "event_type": "ai.detection",
  "timestamp": "2026-01-01T10:00:00Z",
  "camera_id": "camera_1",
  "intersection_id": "intersection_1",
  "frame_id": 1250,
  "detections": [
    {
      "class_name": "car",
      "confidence": 0.94,
      "bbox": [120, 80, 240, 190],
      "track_id": 12
    }
  ]
}

Detection results must originate from actual model inference.
Emergency classifications must include model provenance.

## 4. Traffic Signal Decision

Producer: Traffic Intelligence
Consumer: SUMO Controller / MQTT

{
  "schema_version": "1.0",
  "event_type": "traffic.signal.command",
  "command_id": "unique-command-id",
  "timestamp": "2026-01-01T10:00:00Z",
  "intersection_id": "intersection_1",
  "phase_id": "north_south_green",
  "duration_seconds": 25,
  "reason": "adaptive_density_control",
  "priority": "normal"
}

Commands must be validated against the intersection's legal
signal phases and minimum/maximum timing constraints.

## 5. Emergency Priority Request

Producer: Edge AI or Manual Operator
Consumer: Emergency Priority Engine

{
  "schema_version": "1.0",
  "event_type": "emergency.priority.request",
  "request_id": "unique-request-id",
  "timestamp": "2026-01-01T10:00:00Z",
  "vehicle_id": "ambulance_1",
  "vehicle_type": "ambulance",
  "detection_source": "manual_or_ai",
  "current_intersection": "intersection_1",
  "target_intersection": "intersection_4",
  "route": [
    "intersection_1",
    "intersection_2",
    "intersection_4"
  ],
  "confidence": 0.98
}

AI confidence is required for AI-originated requests.
Manual requests must identify their source explicitly.

## 6. MQTT Topic Structure

Telemetry:
flowsync/intersections/{intersection_id}/telemetry

Signal commands:
flowsync/intersections/{intersection_id}/signals/command

Signal status:
flowsync/intersections/{intersection_id}/signals/status

Emergency requests:
flowsync/emergency/requests

Emergency status:
flowsync/emergency/status

IoT health:
flowsync/iot/{node_id}/health

System events:
flowsync/system/events

## 7. Backend API Responsibilities

GET /api/v1/health
GET /api/v1/intersections
GET /api/v1/intersections/{intersection_id}
GET /api/v1/intersections/{intersection_id}/telemetry
GET /api/v1/emergency/requests
POST /api/v1/emergency/requests
POST /api/v1/emergency/requests/{request_id}/cancel
GET /api/v1/analytics/summary
GET /api/v1/analytics/comparison

These endpoints are proposed contracts and must be implemented
and tested before being considered available.

## 8. WebSocket Contract

Endpoint:
ws://localhost:8000/ws/live

Example event:

{
  "schema_version": "1.0",
  "event_type": "intersection.updated",
  "timestamp": "2026-01-01T10:00:00Z",
  "data": {
    "intersection_id": "intersection_1",
    "signal_state": "green"
  }
}

## 9. Error Handling

- Reject malformed messages.
- Reject unknown intersection identifiers.
- Reject illegal signal commands.
- Include error codes in API responses.
- Log communication failures.
- Do not silently discard emergency requests.
- Use safe fallback control during communication failures.

## 10. Contract Evolution

Schema changes must be versioned.
Breaking changes require updates to all producers and consumers.
