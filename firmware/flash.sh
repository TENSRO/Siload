#!/usr/bin/env bash
# Compile and flash a sketch to a Seeed Studio XIAO (ESP32-C3 or ESP32-S3) over USB.
# The chip and port are detected automatically. Sketch defaults to siload_bench.
#   ./firmware/flash.sh                                # siload_bench
#   ./firmware/flash.sh farm_hub                       # or lora_test
#   ./firmware/flash.sh farm_hub /dev/cu.usbmodem101   # sketch and port, in either order
set -euo pipefail
FIRMWARE="$(cd "$(dirname "$0")" && pwd)"

SKETCH="siload_bench"
PORT=""
for arg in "$@"; do
  if [ -f "$FIRMWARE/$arg/$arg.ino" ]; then SKETCH="$arg"
  elif [[ "$arg" == /dev/* ]]; then PORT="$arg"
  else
    echo "Unknown argument '$arg'. Sketches: $(cd "$FIRMWARE" && ls -d */ | tr -d / | tr '\n' ' ')"
    exit 1
  fi
done
cd "$FIRMWARE/$SKETCH"

# Only siload_bench uses Wi-Fi settings.
if [ -f secrets.h.example ] && [ ! -f secrets.h ]; then cp secrets.h.example secrets.h; fi

PORT="${PORT:-$(ls /dev/cu.usbmodem* 2>/dev/null | head -1 || true)}"
if [ -z "$PORT" ]; then
  echo "No XIAO found on USB. Plug it in (use a data cable, not a charge-only one)."
  echo "Still not showing? Hold BOOT, press RESET, release BOOT, then run this again."
  exit 1
fi

ESPTOOL=$(ls -d ~/Library/Arduino15/packages/esp32/tools/esptool_py/*/esptool 2>/dev/null | tail -1)
if [ -z "$ESPTOOL" ]; then echo "esptool not found. Install the ESP32 core first (see server/README.md)."; exit 1; fi
CHIP=$("$ESPTOOL" --port "$PORT" chip-id 2>&1 | sed -n 's/^Chip type: *\(ESP32-[A-Z0-9]*\).*/\1/p' | head -1)
case "$CHIP" in
  ESP32-C3) FQBN="esp32:esp32:XIAO_ESP32C3" ;;
  ESP32-S3) FQBN="esp32:esp32:XIAO_ESP32S3" ;;
  *) echo "Could not detect a supported chip on $PORT (got: '${CHIP:-nothing}')."; exit 1 ;;
esac

echo "Flashing $SKETCH to $CHIP on $PORT ($FQBN) ..."
arduino-cli compile --fqbn "$FQBN" .
arduino-cli upload --fqbn "$FQBN" -p "$PORT" .
echo "Done. Start the bridge: python3 server/serial_bridge.py"
