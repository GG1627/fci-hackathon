# ESP32 hardware test

Run these commands from the VS Code PowerShell terminal in `firmware/esp32`.

## Find the ESP32 port

```powershell
& "$env:USERPROFILE\.platformio\penv\Scripts\pio.exe" device list
```

The current board uses the CH340 USB serial adapter and was detected as `COM4`.
The COM port can change after reconnecting the board, so check it again if a
command cannot open `COM4`.

## Build and upload

```powershell
& "$env:USERPROFILE\.platformio\penv\Scripts\pio.exe" run --target upload --upload-port COM4
```

## Open the serial monitor

```powershell
& "$env:USERPROFILE\.platformio\penv\Scripts\pio.exe" device monitor --port COM4 --baud 115200
```

Expected output:

```text
Temp: 74.3 F | Door: CLOSED
Temp: 74.3 F | Door: OPEN
```

Press `Ctrl+C` to close the serial monitor. Replace `COM4` in the commands if
`device list` reports a different port.

## Optional shorter commands

Add PlatformIO to the current terminal's PATH:

```powershell
$env:Path += ";$env:USERPROFILE\.platformio\penv\Scripts"
```

You can then use:

```powershell
pio device list
pio run --target upload --upload-port COM4
pio device monitor --port COM4 --baud 115200
```
