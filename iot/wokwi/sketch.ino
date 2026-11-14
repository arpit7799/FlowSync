/*
 * FlowSync — ESP32 Virtual IoT Traffic Controller Firmware
 * Intersection: J1 (North-West Intersection)
 * Compatible with Wokwi ESP32 Simulator and Mosquitto MQTT Broker
 */

#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>

// GPIO Pin Definitions
#define PIN_RED_LED     18
#define PIN_YELLOW_LED  19
#define PIN_GREEN_LED   21
#define PIN_TRIG        25
#define PIN_ECHO        26
#define PIN_BUTTON      27
#define PIN_BUZZER      14

// Intersection & Device Identification
const char* INTERSECTION_ID = "J1";
const char* DEVICE_ID       = "esp32_j1_controller";

// Network & MQTT Configuration
// For Wokwi web simulator, WiFi SSID is "Wokwi-GUEST" with empty password
const char* WIFI_SSID       = "Wokwi-GUEST";
const char* WIFI_PASSWORD   = "";

// MQTT Broker settings (update to your host machine IP or broker URL)
const char* MQTT_BROKER     = "192.168.1.100";  // or host.wokwi.internal
const int   MQTT_PORT       = 1883;
const char* MQTT_USER       = "";
const char* MQTT_PASS       = "";

// MQTT Topics
const char* TOPIC_SENSORS   = "flowsync/intersection/J1/sensors";
const char* TOPIC_SIGNALS   = "flowsync/intersection/J1/signals";
const char* TOPIC_STATUS    = "flowsync/intersection/J1/status";
const char* TOPIC_EMERGENCY = "flowsync/emergency/detected";

WiFiClient espClient;
PubSubClient mqttClient(espClient);

// Timing variables
unsigned long lastSensorPublish = 0;
unsigned long lastStatusPublish = 0;
unsigned long lastButtonPress   = 0;
unsigned long lastReconnectAttempt = 0;
unsigned int reconnectDelaySec  = 1;

const unsigned long SENSOR_INTERVAL_MS = 500;
const unsigned long STATUS_INTERVAL_MS = 10000;
const unsigned long DEBOUNCE_DELAY_MS  = 300;

// Current signal state
bool currentRed    = true;
bool currentYellow = false;
bool currentGreen  = false;
bool emergencyMode = false;

// Function declarations
void setupWiFi();
void reconnectMQTT();
void mqttCallback(char* topic, byte* payload, unsigned int length);
float readUltrasonicDistance();
void publishSensorReading();
void publishStatus(const char* statusMsg);
void handleEmergencyButton();
void applySignalLEDs();

void setup() {
  Serial.begin(115200);
  delay(200);

  Serial.println("\n======================================");
  Serial.println("  FlowSync ESP32 Controller (J1)");
  Serial.println("======================================");

  // Initialize GPIO pins
  pinMode(PIN_RED_LED, OUTPUT);
  pinMode(PIN_YELLOW_LED, OUTPUT);
  pinMode(PIN_GREEN_LED, OUTPUT);
  pinMode(PIN_BUZZER, OUTPUT);
  pinMode(PIN_TRIG, OUTPUT);
  pinMode(PIN_ECHO, INPUT);
  pinMode(PIN_BUTTON, INPUT);  // Ext pulldown or INPUT_PULLUP if inverted

  // Initial LED test (Safe state: RED)
  digitalWrite(PIN_RED_LED, HIGH);
  digitalWrite(PIN_YELLOW_LED, LOW);
  digitalWrite(PIN_GREEN_LED, LOW);
  digitalWrite(PIN_BUZZER, LOW);

  setupWiFi();

  mqttClient.setServer(MQTT_BROKER, MQTT_PORT);
  mqttClient.setCallback(mqttCallback);
}

void loop() {
  if (!mqttClient.connected()) {
    reconnectMQTT();
  } else {
    mqttClient.loop();
  }

  unsigned long now = millis();

  // Read ultrasonic and publish telemetry
  if (now - lastSensorPublish >= SENSOR_INTERVAL_MS) {
    lastSensorPublish = now;
    publishSensorReading();
  }

  // Periodic health/status heartbeat
  if (now - lastStatusPublish >= STATUS_INTERVAL_MS) {
    lastStatusPublish = now;
    publishStatus("online");
  }

  // Check emergency request pushbutton
  handleEmergencyButton();
}

void setupWiFi() {
  Serial.print("Connecting to WiFi: ");
  Serial.println(WIFI_SSID);
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    attempts++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nWiFi connected! IP: " + WiFi.localIP().toString());
  } else {
    Serial.println("\nWiFi connection timed out (simulation continues offline)");
  }
}

void reconnectMQTT() {
  unsigned long now = millis();
  if (now - lastReconnectAttempt < (reconnectDelaySec * 1000)) {
    return;
  }
  lastReconnectAttempt = now;

  Serial.print("Attempting MQTT connection to ");
  Serial.print(MQTT_BROKER);
  Serial.print("...");

  if (mqttClient.connect(DEVICE_ID, MQTT_USER, MQTT_PASS, TOPIC_STATUS, 1, true, "{\"status\":\"offline\"}")) {
    Serial.println(" connected!");
    reconnectDelaySec = 1; // Reset backoff

    // Subscribe to traffic signal commands
    mqttClient.subscribe(TOPIC_SIGNALS, 1);
    Serial.print("Subscribed to: ");
    Serial.println(TOPIC_SIGNALS);

    // Announce online
    publishStatus("online");
  } else {
    Serial.print(" failed, rc=");
    Serial.print(mqttClient.state());
    Serial.print(". Next retry in ");
    Serial.print(reconnectDelaySec);
    Serial.println("s");

    // Exponential backoff: 1s -> 2s -> 4s -> 8s -> 16s -> 30s max
    reconnectDelaySec = (reconnectDelaySec >= 30) ? 30 : reconnectDelaySec * 2;
  }
}

void mqttCallback(char* topic, byte* payload, unsigned int length) {
  char message[512];
  if (length >= sizeof(message)) {
    Serial.println("Payload too large, dropping");
    return;
  }
  memcpy(message, payload, length);
  message[length] = '\0';

  Serial.print("[MQTT RX] Topic: ");
  Serial.println(topic);

  StaticJsonDocument<512> doc;
  DeserializationError error = deserializeJson(doc, message);
  if (error) {
    Serial.print("JSON parse failed: ");
    Serial.println(error.c_str());
    return;
  }

  // Parse signal command
  if (strcmp(topic, TOPIC_SIGNALS) == 0) {
    if (doc.containsKey("red"))    currentRed    = doc["red"].as<bool>();
    if (doc.containsKey("yellow")) currentYellow = doc["yellow"].as<bool>();
    if (doc.containsKey("green"))  currentGreen  = doc["green"].as<bool>();

    if (doc.containsKey("emergency_priority")) {
      emergencyMode = doc["emergency_priority"].as<bool>();
      if (emergencyMode) {
        // Alert buzzer chirp
        tone(PIN_BUZZER, 1000, 200);
      }
    }

    applySignalLEDs();
  }
}

void applySignalLEDs() {
  digitalWrite(PIN_RED_LED,    currentRed    ? HIGH : LOW);
  digitalWrite(PIN_YELLOW_LED, currentYellow ? HIGH : LOW);
  digitalWrite(PIN_GREEN_LED,  currentGreen  ? HIGH : LOW);
}

float readUltrasonicDistance() {
  digitalWrite(PIN_TRIG, LOW);
  delayMicroseconds(2);
  digitalWrite(PIN_TRIG, HIGH);
  delayMicroseconds(10);
  digitalWrite(PIN_TRIG, LOW);

  long duration = pulseIn(PIN_ECHO, HIGH, 30000); // 30ms timeout (~5m)
  if (duration <= 0) {
    return 400.0; // Out of range default (400 cm)
  }

  float distanceCm = (duration * 0.0343) / 2.0;
  return distanceCm;
}

void publishSensorReading() {
  float distance = readUltrasonicDistance();
  bool vehicleDetected = (distance < 50.0); // Within 50cm simulates vehicle queue at stopline

  StaticJsonDocument<256> doc;
  doc["schema_version"]   = "1.0";
  doc["event_type"]       = "sensor.reading";
  doc["timestamp"]        = millis();
  doc["intersection_id"]  = INTERSECTION_ID;
  doc["device_id"]        = DEVICE_ID;
  doc["distance_cm"]      = serialized(String(distance, 1));
  doc["vehicle_detected"] = vehicleDetected;

  char buffer[256];
  serializeJson(doc, buffer);

  if (mqttClient.connected()) {
    mqttClient.publish(TOPIC_SENSORS, buffer);
  }
}

void publishStatus(const char* statusMsg) {
  StaticJsonDocument<256> doc;
  doc["schema_version"]  = "1.0";
  doc["event_type"]      = "device.status";
  doc["timestamp"]       = millis();
  doc["intersection_id"] = INTERSECTION_ID;
  doc["device_id"]       = DEVICE_ID;
  doc["status"]          = statusMsg;
  doc["uptime_ms"]       = millis();
  doc["wifi_rssi"]       = WiFi.RSSI();
  doc["ip_address"]      = WiFi.localIP().toString();

  char buffer[256];
  serializeJson(doc, buffer);

  if (mqttClient.connected()) {
    mqttClient.publish(TOPIC_STATUS, buffer, true); // Retained
  }
}

void handleEmergencyButton() {
  int reading = digitalRead(PIN_BUTTON);
  unsigned long now = millis();

  if (reading == HIGH && (now - lastButtonPress > DEBOUNCE_DELAY_MS)) {
    lastButtonPress = now;
    Serial.println("[ALERT] Emergency request pushbutton activated!");

    // Audible feedback
    tone(PIN_BUZZER, 1500, 300);

    StaticJsonDocument<256> doc;
    doc["schema_version"]       = "1.0";
    doc["event_type"]           = "emergency.detected";
    doc["timestamp"]            = now;
    doc["intersection_id"]      = INTERSECTION_ID;
    doc["device_id"]            = DEVICE_ID;
    doc["source"]               = "iot_manual_button";
    doc["vehicle_type"]         = "ambulance";
    doc["requested_corridor"]   = "north_to_south";

    char buffer[256];
    serializeJson(doc, buffer);

    if (mqttClient.connected()) {
      mqttClient.publish(TOPIC_EMERGENCY, buffer, 1);
      Serial.println("Published emergency priority request to MQTT");
    }
  }
}
