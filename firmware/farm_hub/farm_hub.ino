// Farm hub firmware: receives LoRa packets from Siload nodes and prints each one as a JSON line over USB.
// Board: Seeed Studio XIAO ESP32S3 with a Wio-SX1262 for XIAO on the header pins (same pins as the Siload).
// Ethernet (W5500) will be added once its pins are known; it shares the SPI bus D8/D9/D10.
//
// A Siload reading arrives as the same JSON the server expects ({"device_id":…,"raw":[…],…}); the hub adds
// "rssi" and "snr" and prints it, so server/serial_bridge.py on the hub's USB port feeds it to the dashboard.
// Other packets (e.g. from firmware/lora_test) are printed as [lora] lines.
//
// Radio settings must match the senders: 868.0 MHz, 125 kHz, SF7, CR 4/5, sync word 0x12.
#include <RadioLib.h>
#include <SPI.h>

#define LORA_NSS   D4
#define LORA_DIO1  D1
#define LORA_RST   D2
#define LORA_BUSY  D3
#define LORA_RF_SW D5

#define FREQ_MHZ   868.0

SX1262 radio = new Module(LORA_NSS, LORA_DIO1, LORA_RST, LORA_BUSY);
volatile bool packetReady = false;
bool radioOk = false;
uint32_t received = 0;

void IRAM_ATTR onPacket() { packetReady = true; }

void setup() {
  Serial.begin(115200);
  delay(4000);
  Serial.println("\n=== Siload farm hub ===");

  SPI.begin(D8, D9, D10, LORA_NSS);
  int state = radio.begin(FREQ_MHZ, 125.0, 7, 5, RADIOLIB_SX126X_SYNC_WORD_PRIVATE, 2, 8, 1.8);
  if (state != RADIOLIB_ERR_NONE) {
    Serial.printf("LoRa begin() failed (%d), retrying without TCXO\n", state);
    state = radio.begin(FREQ_MHZ, 125.0, 7, 5, RADIOLIB_SX126X_SYNC_WORD_PRIVATE, 2, 8, 0);
  }
  if (state != RADIOLIB_ERR_NONE) {
    Serial.printf("LoRa not found (%d): check NSS D4, RST D2, BUSY D3 and SPI D8/D9/D10\n", state);
    return;
  }
  radio.setRfSwitchPins(LORA_RF_SW, RADIOLIB_NC);
  radio.setDio2AsRfSwitch(true);
  radio.setPacketReceivedAction(onPacket);
  state = radio.startReceive();
  Serial.printf("LoRa OK, listening on %.1f MHz (startReceive = %d)\n", FREQ_MHZ, state);
  radioOk = true;
}

void loop() {
  if (!radioOk || !packetReady) return;
  packetReady = false;

  String msg;
  int state = radio.readData(msg);
  if (state == RADIOLIB_ERR_NONE) {
    received++;
    msg.trim();
    if (msg.startsWith("{\"device_id\"") && msg.endsWith("}")) {
      msg.remove(msg.length() - 1);
      Serial.printf("%s,\"rssi\":%.1f,\"snr\":%.1f}\n", msg.c_str(), radio.getRSSI(), radio.getSNR());
    } else {
      Serial.printf("[lora] \"%s\" rssi %.1f snr %.1f (#%lu)\n",
                    msg.c_str(), radio.getRSSI(), radio.getSNR(), (unsigned long)received);
    }
  } else if (state == RADIOLIB_ERR_CRC_MISMATCH) {
    Serial.println("[lora] packet with CRC error");
  } else {
    Serial.printf("[lora] readData failed (%d)\n", state);
  }
  radio.startReceive();
}
