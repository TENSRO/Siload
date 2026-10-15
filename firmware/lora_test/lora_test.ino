// Wiring test for the Seeed "Wio-SX1262 for XIAO" on the header pins of a XIAO ESP32S3.
// Prints a step-by-step report over USB, then sends a short low-power test packet every 5 s.
//
// Pins: NSS D4, DIO1 D1, RESET D2, BUSY D3, RF switch D5, SCK D8, MISO D9, MOSI D10.
// D8/D9/D10 are the SPI bus, so they can't also be used for the HX711.
#include <RadioLib.h>
#include <SPI.h>

#define LORA_NSS   D4
#define LORA_DIO1  D1
#define LORA_RST   D2
#define LORA_BUSY  D3
#define LORA_RF_SW D5

#define FREQ_MHZ   868.0   // EU868
#define TX_DBM     2       // low power: bench test only

SX1262 radio = new Module(LORA_NSS, LORA_DIO1, LORA_RST, LORA_BUSY);
bool radioOk = false;
uint32_t packets = 0;

void result(const char *step, bool ok, const char *detail) {
  Serial.printf("[%s] %s: %s\n", ok ? " OK " : "FAIL", step, detail);
}

// RESET low must make BUSY high; after release BUSY must drop low within a few ms.
void checkResetBusy() {
  pinMode(LORA_BUSY, INPUT);
  pinMode(LORA_RST, OUTPUT);
  digitalWrite(LORA_RST, LOW);
  delay(2);
  int busyInReset = digitalRead(LORA_BUSY);
  digitalWrite(LORA_RST, HIGH);
  uint32_t t0 = millis();
  while (digitalRead(LORA_BUSY) == HIGH && millis() - t0 < 100) {}
  uint32_t ms = millis() - t0;
  char buf[96];
  snprintf(buf, sizeof(buf), "BUSY in reset=%s, BUSY low %lu ms after release",
           busyInReset ? "HIGH" : "LOW", (unsigned long)ms);
  result("RESET (D2) / BUSY (D3)", busyInReset == HIGH && ms < 100, buf);
}

void setup() {
  Serial.begin(115200);
  delay(4000);
  Serial.println("\n=== Siload SX1262 wiring test ===");

  checkResetBusy();

  SPI.begin(D8, D9, D10, LORA_NSS);
  // begin() reads the chip's version string over SPI, so success proves NSS/SCK/MISO/MOSI.
  float tcxo = 1.8;
  int state = radio.begin(FREQ_MHZ, 125.0, 7, 5, RADIOLIB_SX126X_SYNC_WORD_PRIVATE, TX_DBM, 8, tcxo);
  if (state != RADIOLIB_ERR_NONE) {
    Serial.printf("       begin() with 1.8 V TCXO failed (%d), retrying without TCXO\n", state);
    tcxo = 0;
    state = radio.begin(FREQ_MHZ, 125.0, 7, 5, RADIOLIB_SX126X_SYNC_WORD_PRIVATE, TX_DBM, 8, tcxo);
  }
  char buf[96];
  snprintf(buf, sizeof(buf), "radio.begin() = %d%s", state,
           state == RADIOLIB_ERR_CHIP_NOT_FOUND ? " (no chip answering on SPI)" : "");
  result("SPI (D4, D8-D10) + chip detect", state == RADIOLIB_ERR_NONE, buf);
  if (state != RADIOLIB_ERR_NONE) {
    Serial.println("Stopping: check NSS (D4) and SCK/MISO/MOSI (D8/D9/D10), and that nothing else uses D8-D10.");
    return;
  }
  Serial.printf("       TCXO: %s\n", tcxo > 0 ? "1.8 V (DIO3)" : "none");

  radio.setRfSwitchPins(LORA_RF_SW, RADIOLIB_NC);
  radio.setDio2AsRfSwitch(true);

  // transmit() waits for the TX-done interrupt on DIO1, so a timeout means DIO1 isn't connected.
  uint32_t t0 = millis();
  state = radio.transmit("siload lora test");
  snprintf(buf, sizeof(buf), "transmit() = %d, %lu ms (expected ~50 ms at SF7)", state,
           (unsigned long)(millis() - t0));
  result("TX + DIO1 (D1) interrupt", state == RADIOLIB_ERR_NONE, buf);

  // Noise floor through the antenna path. Roughly -100..-125 dBm is normal on the bench.
  radio.startReceive();
  delay(50);
  float rssi = 0;
  for (int i = 0; i < 20; i++) { rssi += radio.getRSSI(false); delay(10); }
  rssi /= 20;
  snprintf(buf, sizeof(buf), "%.1f dBm", rssi);
  result("RX noise floor (RF switch D5)", rssi < -80 && rssi > -140, buf);

  radioOk = true;
  Serial.println("=== done; now sending a test packet every 5 s ===");
}

void loop() {
  if (!radioOk) { delay(1000); return; }
  delay(5000);
  char msg[40];
  snprintf(msg, sizeof(msg), "siload test #%lu", (unsigned long)++packets);
  int state = radio.transmit(msg);
  Serial.printf("TX \"%s\" -> %d\n", msg, state);
}
