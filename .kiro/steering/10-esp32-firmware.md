---
title: Ed — ESP32 Firmware Patterns
inclusion: fileMatch
fileMatch: "firmware/**"
---

# ESP32 Firmware Patterns

## Architecture
- `setup()`: init WiFi, WebSocket, all sensors, actuators
- `loop()`: non-blocking sensor reads → JSON serialize → WebSocket send → check for commands
- All sensor drivers in `src/sensors/` with a common `read()` interface
- All actuators in `src/actuators/` with async-safe command interface

## Timing Budget (per loop iteration, target < 50ms)
- IMU read: ~1ms
- HR read: ~5ms (only every 1s)
- Touch read: ~1ms
- Audio: DMA buffer, interrupt-driven (not in main loop)
- WebSocket send: ~5ms
- Command processing: ~2ms

## WiFi & WebSocket
- Connect to WiFi in `setup()` with timeout + retry
- WebSocket client to `ws://<backend_ip>:8000/ws/bear`
- Auto-reconnect on disconnect (non-blocking, check every 5s)
- Heartbeat ping every 10s to detect stale connections
- All messages are JSON via ArduinoJson `StaticJsonDocument<1024>`

## Sensor Message Format
```json
{
  "type": "sensor_data",
  "ts": 1714000000,
  "imu": {"ax": 0.1, "ay": 0.0, "az": 1.0, "gx": 0.0, "gy": 0.0, "gz": 0.0},
  "hr": {"bpm": 72, "spo2": 97, "valid": true},
  "touch": {"pads": [1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0], "any": true}
}
```

## Command Message Format
```json
{
  "type": "command",
  "action": "speak",
  "payload": {"url": "https://api.cartesia.ai/..."}
}
```
Actions: `speak` (stream TTS URL), `breathe` (motor pattern), `led` (color + pattern), `play_clip` (family voice URL)

## Safety
- Watchdog timer: 8 second timeout, auto-reset on hang
- No `delay()` calls — use `millis()` based timing
- Stack overflow guard: keep task stack sizes explicit
- If WebSocket disconnected > 60s, enter autonomous comfort mode (gentle LED pulse + slow breathing)

## Main Loop Pattern

```cpp
void loop() {
    esp_task_wdt_reset();
    unsigned long now = millis();

    // Sensor reads at different intervals
    if (now - lastIMU >= 100) {
        imu_read(&imuData);
        lastIMU = now;
    }
    if (now - lastHR >= 1000) {
        hr_read(&hrData);
        lastHR = now;
    }
    if (now - lastTouch >= 200) {
        touch_read(&touchData);
        lastTouch = now;
    }

    // Build and send JSON
    if (now - lastSend >= 100 && ws.isConnected()) {
        StaticJsonDocument<512> doc;
        doc["type"] = "sensor_data";
        doc["ts"] = now / 1000;
        JsonObject imu = doc.createNestedObject("imu");
        imu["ax"] = imuData.ax; imu["ay"] = imuData.ay; imu["az"] = imuData.az;
        imu["gx"] = imuData.gx; imu["gy"] = imuData.gy; imu["gz"] = imuData.gz;
        // ... hr, touch objects
        String output;
        serializeJson(doc, output);
        ws.sendTXT(output);
        lastSend = now;
    }

    // Process incoming commands
    ws.loop();

    // Autonomous mode if disconnected too long
    if (!ws.isConnected() && (now - lastConnected > 60000)) {
        autonomous_comfort_mode();
    }
}
```
