# FlowSync MQTT Specification

## 1. Broker

Broker: Eclipse Mosquitto
Protocol: MQTT 3.1.1 initially
Default development address: localhost
Default development port: 1883

Authentication and TLS will be configured where supported
and appropriate for the deployment environment.

## 2. Topic Naming Convention

Root namespace: flowsync

Intersection telemetry:
flowsync/intersections/{intersection_id}/telemetry

Signal commands:
flowsync/intersections/{intersection_id}/signals/command

Signal status:
flowsync/intersections/{intersection_id}/signals/status

Emergency requests:
flowsync/emergency/requests

Emergency status:
flowsync/emergency/status

IoT node health:
flowsync/iot/{node_id}/health

System events:
flowsync/system/events

## 3. Quality of Service

QoS 0:
- High-frequency, replaceable telemetry where occasional loss
  is acceptable.

QoS 1:
- Intersection telemetry requiring delivery confirmation.
- Node health updates.
- Non-critical system events.

QoS 1 with application acknowledgement:
- Traffic signal commands.
- Emergency priority requests.
- Emergency cancellation and completion events.

Critical commands must include unique identifiers and duplicate
handling. MQTT QoS alone does not guarantee exactly-once execution.

## 4. Retained Messages

Retained messages may be used for:
- Latest intersection signal status.
- Latest IoT node health state.

Retained messages must not be used to replay emergency requests
or execute old traffic signal commands.

## 5. Message Validation

Every application message must:
- Include schema_version.
- Include timestamp.
- Include event_type.
- Use a valid intersection or node identifier.
- Pass payload validation.
- Reject expired or duplicate commands.

## 6. Reliability

- Monitor broker connection status.
- Reconnect with bounded exponential backoff.
- Log publishing and subscription failures.
- Maintain a safe local fallback controller.
- Never treat a publish operation as proof that a signal
  command was executed.
- Record command acknowledgements.

## 7. Security

- Use separate credentials for different clients where feasible.
- Restrict topic read/write permissions.
- Do not publish credentials in source code.
- Use TLS for non-local deployment.
- Validate all commands before execution.

## 8. Client Identity

Each simulated intersection node must use a unique client ID.

Example:
flowsync_intersection_1
flowsync_intersection_2
flowsync_intersection_3
flowsync_intersection_4

## 9. Testing Requirements

- Publish and subscribe test.
- QoS behavior test.
- Invalid message rejection.
- Duplicate command handling.
- Broker disconnection and reconnection.
- Emergency request delivery.
- Command acknowledgement.
