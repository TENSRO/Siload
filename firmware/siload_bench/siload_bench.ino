// Siload bench firmware: reads an HX711 load cell amplifier and sends the raw values
// to the bench server (server/server.py):
//   - over USB: every reading is printed as one JSON line; run server/serial_bridge.py,
//   - over LoRa: every LORA_INTERVAL_MS the latest reading goes to the farm hub (firmware/farm_hub), and
//   - over Wi-Fi: set WIFI_SSID in secrets.h and the board POSTs directly.
//
// Libraries: "HX711 Arduino Library" (Bogdan Necula), "OneWireNg", "RadioLib".
//          OneWireNg instead of OneWire/DallasTemperature: on the ESP32-S3, D7 is GPIO 44, and the OneWire
//          library refuses to drive pins above 33 (true on the original ESP32 only), so it never finds a sensor.
// Board:   Seeed Studio XIAO ESP32S3 with a Wio-SX1262 for XIAO on the header pins
//          (firmware/flash.sh detects the chip; USB CDC On Boot enabled).
//          The LoRa module uses D1-D5 and the SPI bus D8/D9/D10, so those are not free.
//          Wiring for leg 1: HX711 DT -> D0, SCK -> D6, VCC -> 3V3, GND -> GND.
//          DS18B20 temperature sensor(s): DATA -> D7, VDD -> 3V3, GND -> GND, plus a 4.7 kOhm
//          pull-up resistor between DATA and 3V3. Several DS18B20s can share D7 (one per leg).
//
// Raw values only: tare, calibration and temperature correction happen on the
// server/dashboard, so the firmware never needs reflashing to recalibrate.

#include <WiFi.h>
#include <HTTPClient.h>
#include <RadioLib.h>
#include <SPI.h>
#include "HX711.h"
#include "OneWireNg_CurrentPlatform.h"
#include "drivers/DSTherm.h"
#include "utils/Placeholder.h"
#include "secrets.h"   // WIFI_SSID, WIFI_PASSWORD, SERVER_URL (copy from secrets.h.example)

// ---- configure ----
const char* DEVICE_ID     = "bench-01";

// With the LoRa module only D0, D6 and D7 are free, so there is room for one HX711.
// SCK is on D6 rather than DT: D6 is UART TX and toggles during boot, which an HX711 input tolerates.
const int NUM_LEGS = 1;
const int DOUT_PINS[4] = {D0};                  // HX711 DT, per leg
const int SCK_PINS[4]  = {D6};                  // HX711 SCK, per leg

const int TEMP_PIN = D7;                        // DS18B20 1-Wire bus

const int SAMPLES_PER_READING = 10;            // HX711 averages per posted reading
const unsigned long SEND_INTERVAL_MS = 1000;

// LoRa: Wio-SX1262 for XIAO. Radio settings must match firmware/farm_hub.
// EU868 allows 1% airtime: a ~60-byte packet at SF7 takes ~100 ms, so at most one per 10 s.
const unsigned long LORA_INTERVAL_MS = 15000;
const int LORA_TX_DBM = 14;                     // EU868 maximum
// -------------------

#define LORA_NSS   D4
#define LORA_DIO1  D1
#define LORA_RST   D2
#define LORA_BUSY  D3
#define LORA_RF_SW D5
SX1262 radio = new Module(LORA_NSS, LORA_DIO1, LORA_RST, LORA_BUSY);
bool loraOk = false;

HX711 scales[4];
Placeholder<OneWireNg_CurrentPlatform> oneWire;
OneWireNg::Id tempIds[4];                       // ROM addresses of the DS18B20s found, in bus order
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
  new (&oneWire) OneWireNg_CurrentPlatform(TEMP_PIN, false);   // false: external 4.7k pull-up
  findTempSensors();
  setupLora();
  if (USE_WIFI) connectWifi();
}

void setupLora() {
  SPI.begin(D8, D9, D10, LORA_NSS);
  int state = radio.begin(868.0, 125.0, 7, 5, RADIOLIB_SX126X_SYNC_WORD_PRIVATE, LORA_TX_DBM, 8, 1.8);
  if (state == RADIOLIB_ERR_NONE) {
    radio.setRfSwitchPins(LORA_RF_SW, RADIOLIB_NC);
    radio.setDio2AsRfSwitch(true);
    loraOk = true;
  }
  if (loraOk) Serial.println("LoRa: OK, 868.0 MHz SF7");
  else Serial.printf("LoRa: not found, error %d\n", state);
}

// Scans the 1-Wire bus. Sensors are reported in bus order (by ROM address); the addresses
// are printed so they can later be mapped to legs.
void findTempSensors() {
  numTempSensors = 0;
  for (const auto& id : *oneWire) {
    if (numTempSensors < 4 && DSTherm::getFamilyName(id)) {   // DS18B20 and other Dallas thermometers only
      memcpy(tempIds[numTempSensors++], id, sizeof(OneWireNg::Id));
    }
  }
  Serial.printf("DS18B20: %d sensor(s) on D7\n", numTempSensors);
  if (numTempSensors == 0) {
    // Wiring diagnosis: an idle 1-Wire bus is held HIGH by the 4.7k pull-up, and a
    // connected sensor answers a reset pulse with a "presence" pulse.
    bool idleHigh = digitalRead(TEMP_PIN);
    bool presence = oneWire->reset() == OneWireNg::EC_SUCCESS;
    Serial.printf("  bus idle level: %s, presence pulse: %s\n",
                  idleHigh ? "HIGH (pull-up OK)" : "LOW (no 4.7k pull-up, or DATA shorted to GND)",
                  presence ? "yes (sensor answers, but ROM search failed)" : "no (no sensor on D7)");
    return;
  }
  for (int i = 0; i < numTempSensors; i++) {
    Serial.printf("  sensor %d: ", i + 1);
    for (int b = 0; b < 8; b++) Serial.printf("%02X", tempIds[i][b]);
    Serial.println();
  }
  DSTherm drv(oneWire);
  drv.writeScratchpadAll(0, 0, DSTherm::RES_12_BIT);   // 0.0625 degC steps, 750 ms per conversion
  drv.convertTempAll(0);                               // 0 = don't wait: convert in the background
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
    DSTherm drv(oneWire);
    Placeholder<DSTherm::Scratchpad> scratchpad;
    json += ",\"temp_c\":[";
    for (int i = 0; i < numTempSensors; i++) {
      if (i) json += ",";
      if (drv.readScratchpad(tempIds[i], scratchpad) == OneWireNg::EC_SUCCESS) {
        const DSTherm::Scratchpad& sp = scratchpad;
        json += String(sp.getTemp2() / 16.0, 2);     // getTemp2() is in 1/16 degC
      } else {
        json += "null";                               // sensor lost or CRC error
      }
    }
    json += "]";
    drv.convertTempAll(0);
  }
  json += "}";

  Serial.println(json);

  static unsigned long lastLora = 0;
  if (loraOk && (lastLora == 0 || millis() - lastLora >= LORA_INTERVAL_MS)) {
    lastLora = millis();
    int state = radio.transmit(json);
    if (state != RADIOLIB_ERR_NONE) Serial.printf("LoRa send failed: %d\n", state);
  }

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
