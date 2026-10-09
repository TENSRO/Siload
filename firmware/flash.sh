#!/usr/bin/env bash
# Compile and flash siload_bench to a Seeed Studio XIAO (ESP32-C3 or ESP32-S3) over USB.
# The chip is detected automatically.
#   ./firmware/flash.sh                      # auto-detects the port
#   ./firmware/flash.sh /dev/cu.usbmodem101
set -euo pipefail
cd "$(dirname "$0")/siload_bench"

[ -f secrets.h ] || cp secrets.h.example secrets.h

PORT="${1:-$(ls /dev/cu.usbmodem* 2>/dev/null | head -1 || true)}"
if [ -z "$PORT" ]; then
  echo "No XIAO found on USB. Plug it in (use a data cable, not a charge-only one)."
  echo "Still not showing? Hold BOOT, press RESET, release BOOT, then run this again."
  exit 1
fi

ESPTOOL=$(ls -d ~/Library/Arduino15/packages/esp32/tools/esptool_py/*/esptool 2>/dev/null | tail -1)
CHIP=$("$ESPTOOL" --port "$PORT" chip-id 2>&1 | sed -n 's/^Chip type: *\(ESP32-[A-Z0-9]*\).*/\1/p' | head -1)
case "$CHIP" in
  ESP32-C3) FQBN="esp32:esp32:XIAO_ESP32C3" ;;
  ESP32-S3) FQBN="esp32:esp32:XIAO_ESP32S3" ;;
  *) echo "Could not detect a supported chip on $PORT (got: '${CHIP:-nothing}')."; exit 1 ;;
esac

echo "Flashing $CHIP on $PORT ($FQBN) ..."
arduino-cli compile --fqbn "$FQBN" .
arduino-cli upload --fqbn "$FQBN" -p "$PORT" .
echo "Done. Start the bridge: python3 server/serial_bridge.py"
