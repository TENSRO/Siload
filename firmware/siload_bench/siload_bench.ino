// Siload bench firmware: reads up to 4 HX711 load cell amplifiers and sends the raw
// values to the bench server (server/server.py), either:
//   - over USB: every reading is printed as one JSON line; run server/serial_bridge.py, or
//   - over Wi-Fi: set WIFI_SSID in secrets.h and the board POSTs directly.
//
// Libraries: "HX711 Arduino Library" (Bogdan Necula), "OneWire", "DallasTemperature".
// Board:   Seeed Studio XIAO ESP32C3 or ESP32S3 (firmware/flash.sh detects which; USB CDC On Boot enabled).
//          Wiring for leg 1: HX711 DT -> D9, SCK -> D10, VCC -> 3V3, GND -> GND.
//          DS18B20 temperature sensor(s): DATA -> D7, VDD -> 3V3, GND -> GND, plus a 4.7 kOhm
//          pull-up resistor between DATA and 3V3. Several DS18B20s can share D7 (one per leg).
//
// Raw values only: tare, calibration and temperature correction happen on the
// server/dashboard, so the firmware never needs reflashing to recalibrate.

#include <WiFi.h>
#include <HTTPClient.h>
#include "HX711.h"
#include <OneWire.h>
#include <DallasTemperature.h>
#include "secrets.h"   // WIFI_SSID, WIFI_PASSWORD, SERVER_URL (copy from secrets.h.example)

// ---- configure ----
const char* DEVICE_ID     = "bench-01";

const int NUM_LEGS = 1;                        // 1..4 HX711 boards connected
const int DOUT_PINS[4] = {D9,  D0, D2, D4};     // HX711 DT, per leg
const int SCK_PINS[4]  = {D10, D1, D3, D5};     // HX711 SCK, per leg

const int TEMP_PIN = D7;                        // DS18B20 1-Wire bus

const int SAMPLES_PER_READING = 10;            // HX711 averages per posted reading
const unsigned long SEND_INTERVAL_MS = 1000;
// -------------------

HX711 scales[4];
OneWire oneWire(TEMP_PIN);
DallasTemperature tempSensors(&oneWire);
int numTempSensors = 0;
const bool USE_WIFI = sizeof(WIFI_SSID) > 1;   // empty SSID = USB-only mode

void connectWifi() {
  if (WiFi.status() == WL_CONNECTED) return;
  Serial.printf("Connecting to %s", WIFI_SSID);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  for (int i = 0; i < 40 && WiFi.status() != WL_CONNECTED; i++) {
    delay(250);
    Serial.print(".");
  }
  Serial.println(WiFi.status() == WL_CONNECTED ? " ok, IP " + WiFi.localIP().toString() : " failed");
}

void setup() {
  Serial.begin(115200);
  for (int i = 0; i < NUM_LEGS; i++) {
    scales[i].begin(DOUT_PINS[i], SCK_PINS[i]);
    scales[i].set_gain(128);
  }
  findTempSensors();
  if (USE_WIFI) connectWifi();
}

// Scans the 1-Wire bus. Sensors are reported in bus order (by ROM address); the addresses
// are printed so they can later be mapped to legs.
void findTempSensors() {
  tempSensors.begin();
  tempSensors.setResolution(12);                // 0.0625 degC steps, 750 ms per conversion
  tempSensors.setWaitForConversion(false);      // convert in the background between readings
  numTempSensors = min((int)tempSensors.getDeviceCount(), 4);
  Serial.printf("DS18B20: %d sensor(s) on D7\n", numTempSensors);
  if (numTempSensors == 0) {
    // Wiring diagnosis: an idle 1-Wire bus is held HIGH by the 4.7k pull-up, and a
    // connected sensor answers a reset pulse with a "presence" pulse.
    pinMode(TEMP_PIN, INPUT);
    delay(1);
    bool idleHigh = digitalRead(TEMP_PIN);
    bool presence = oneWire.reset();
    Serial.printf("  bus idle level: %s, presence pulse: %s\n",
                  idleHigh ? "HIGH (pull-up OK)" : "LOW (no 4.7k pull-up, or DATA shorted to GND)",
                  presence ? "yes (sensor answers, but ROM search failed)" : "no (no sensor on D7)");
  }
  for (int i = 0; i < numTempSensors; i++) {
    DeviceAddress addr;
    if (!tempSensors.getAddress(addr, i)) continue;
    Serial.print("  sensor ");
    Serial.print(i + 1);
    Serial.print(": ");
    for (int b = 0; b < 8; b++) Serial.printf("%02X", addr[b]);
    Serial.println();
  }
  if (numTempSensors) tempSensors.requestTemperatures();
}

void loop() {
  static unsigned long lastSend = 0;
  if (millis() - lastSend < SEND_INTERVAL_MS) return;
  lastSend = millis();

  String json = "{\"device_id\":\"" + String(DEVICE_ID) + "\",\"raw\":[";
  for (int i = 0; i < NUM_LEGS; i++) {
    if (i) json += ",";
    if (scales[i].wait_ready_timeout(500)) {
      json += String(scales[i].read_average(SAMPLES_PER_READING));
    } else {
      json += "null";   // HX711 not responding: check wiring
    }
  }
  json += "]";

  // Temperatures: the conversion was started after the previous reading (>= 1 s ago),
  // so the results are ready now. Start the next conversion right after reading.
  static unsigned long lastScan = 0;
  if (numTempSensors == 0 && millis() - lastScan > 10000) {   // retry if a sensor is plugged in later
    lastScan = millis();
    findTempSensors();
  }
  if (numTempSensors) {
    json += ",\"temp_c\":[";
    for (int i = 0; i < numTempSensors; i++) {
      if (i) json += ",";
      float t = tempSensors.getTempCByIndex(i);
      json += (t == DEVICE_DISCONNECTED_C) ? String("null") : String(t, 2);   // null = sensor lost
    }
    json += "]";
    tempSensors.requestTemperatures();
  }
  json += "}";

  Serial.println(json);

  if (!USE_WIFI) return;
  connectWifi();
  if (WiFi.status() != WL_CONNECTED) return;
  HTTPClient http;
  http.begin(SERVER_URL);
  http.addHeader("Content-Type", "application/json");
  int code = http.POST(json);
  if (code != 201) Serial.printf("POST failed: %d\n", code);
  http.end();
}
