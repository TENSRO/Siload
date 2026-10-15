# Compile and flash siload_bench to a Seeed Studio XIAO (ESP32-C3 or ESP32-S3) over USB. Windows version of flash.sh.
# The chip is detected automatically. Run via flash.cmd, which bypasses the PowerShell script policy:
#   firmware\flash.cmd           # auto-detects the port
#   firmware\flash.cmd COM5
param([string]$Port)
$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "siload_bench")

if (-not (Test-Path secrets.h)) { Copy-Item secrets.h.example secrets.h }

if (-not (Get-Command arduino-cli -ErrorAction SilentlyContinue)) {
    $env:Path += ";$env:ProgramFiles\Arduino CLI"
}

if (-not $Port) {
    # First USB serial port (skips built-in and Bluetooth COM ports).
    $map = Get-ItemProperty "HKLM:\HARDWARE\DEVICEMAP\SERIALCOMM" -ErrorAction SilentlyContinue
    if ($map) {
        $Port = $map.PSObject.Properties |
            Where-Object { $_.Name -notmatch '^(PS|\\Device\\(Serial|BthModem))' } |
            ForEach-Object { $_.Value } |
            Sort-Object { [int]($_ -replace '\D', '') } |
            Select-Object -First 1
    }
}
if (-not $Port) {
    Write-Host "No XIAO found on USB. Plug it in (use a data cable, not a charge-only one)."
    Write-Host "Still not showing? Hold BOOT, press RESET, release BOOT, then run this again."
    exit 1
}

$esptool = Get-ChildItem "$env:LOCALAPPDATA\Arduino15\packages\esp32\tools\esptool_py\*\esptool.exe" -ErrorAction SilentlyContinue |
    Sort-Object FullName | Select-Object -Last 1 -ExpandProperty FullName
if (-not $esptool) { Write-Host "esptool not found. Install the ESP32 core first (see server/README.md)."; exit 1 }

$chip = (& $esptool --port $Port chip-id 2>&1 | Out-String) -split "`n" |
    ForEach-Object { if ($_ -match '^Chip type:\s*(ESP32-[A-Z0-9]+)') { $Matches[1] } } | Select-Object -First 1
switch ($chip) {
    "ESP32-C3" { $fqbn = "esp32:esp32:XIAO_ESP32C3" }
    "ESP32-S3" { $fqbn = "esp32:esp32:XIAO_ESP32S3" }
    default { Write-Host "Could not detect a supported chip on $Port (got: '$chip')."; exit 1 }
}

Write-Host "Flashing $chip on $Port ($fqbn) ..."
arduino-cli compile --fqbn $fqbn .
if ($LASTEXITCODE) { exit $LASTEXITCODE }
arduino-cli upload --fqbn $fqbn -p $Port .
if ($LASTEXITCODE) { exit $LASTEXITCODE }
Write-Host "Done. Start the bridge: python server\serial_bridge.py"
