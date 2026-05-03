/**
 * ESP32 Sensors — Reads raw accelerometer + touch data and sends JSON over serial.
 * All feature computation (jerk, fall, rocking, etc.) happens in the backend.
 *
 * JSON format (compact, ~100 bytes):
 * {"type":"sensor_data","ts":12.3,"imu":{"ax":0.010,"ay":-0.020,"az":1.000},"touch":{"pads":[0,3]}}
 */

#include <Arduino.h>
#include <Wire.h>

// ============================================================
// Configuration
// ============================================================
namespace Config {
  constexpr unsigned long SEND_INTERVAL_MS = 250;  // 4 Hz
}

// ============================================================
// MPU6050 Accelerometer — raw reads only
// ============================================================
namespace Accel {
  constexpr uint8_t MPU_ADDR = 0x68;
  constexpr int SDA_PIN = 21;
  constexpr int SCL_PIN = 22;

  constexpr uint8_t REG_PWR_MGMT_1   = 0x6B;
  constexpr uint8_t REG_WHO_AM_I     = 0x75;
  constexpr uint8_t REG_ACCEL_XOUT_H = 0x3B;
  constexpr uint8_t WHO_AM_I_EXPECTED = 0x68;
  constexpr float ACCEL_LSB_PER_G = 16384.0f;

  bool initialized = false;
  float ax = 0.0f, ay = 0.0f, az = 0.0f;

  constexpr unsigned long SAMPLE_MS = 10;
  unsigned long lastReadMs = 0;

  constexpr int MAX_READ_FAILURES = 10;
  int consecutiveReadFailures = 0;

  bool writeRegister8(uint8_t reg, uint8_t value) {
    Wire.beginTransmission(MPU_ADDR);
    Wire.write(reg);
    Wire.write(value);
    return Wire.endTransmission() == 0;
  }

  bool readRegisters(uint8_t startReg, uint8_t *buffer, size_t len) {
    if (!buffer || len == 0) return false;
    Wire.beginTransmission(MPU_ADDR);
    Wire.write(startReg);
    if (Wire.endTransmission(false) != 0) return false;
    if (Wire.requestFrom(MPU_ADDR, len) != len) return false;
    for (size_t i = 0; i < len; ++i) {
      int v = Wire.read();
      if (v < 0) return false;
      buffer[i] = (uint8_t)v;
    }
    return true;
  }

  int16_t joinBytes(uint8_t h, uint8_t l) {
    return (int16_t)((uint16_t)h << 8 | (uint16_t)l);
  }

  bool readAccelG(float &ox, float &oy, float &oz) {
    uint8_t raw[6] = {0};
    if (!readRegisters(REG_ACCEL_XOUT_H, raw, 6)) return false;
    ox = (float)joinBytes(raw[0], raw[1]) / ACCEL_LSB_PER_G;
    oy = (float)joinBytes(raw[2], raw[3]) / ACCEL_LSB_PER_G;
    oz = (float)joinBytes(raw[4], raw[5]) / ACCEL_LSB_PER_G;
    return true;
  }

  void recoverI2C() {
    Serial.println("[Accel] I2C recovery");
    Wire.end();
    delay(50);
    Wire.setPins(SDA_PIN, SCL_PIN);
    Wire.begin();
    Wire.setClock(400000);
    Wire.setTimeOut(50);
    writeRegister8(REG_PWR_MGMT_1, 0x00);
    delay(10);
    consecutiveReadFailures = 0;
  }

  void init() {
    Serial.println("[Accel] Initializing MPU6050...");
    if (!Wire.setPins(SDA_PIN, SCL_PIN)) { Serial.println("[Accel] setPins failed"); return; }
    if (!Wire.begin()) { Serial.println("[Accel] Wire.begin failed"); return; }
    Wire.setClock(400000);
    Wire.setTimeOut(50);

    if (!writeRegister8(REG_PWR_MGMT_1, 0x00)) { Serial.println("[Accel] wake failed"); return; }
    delay(100);

    uint8_t whoAmI = 0;
    if (!readRegisters(REG_WHO_AM_I, &whoAmI, 1)) { Serial.println("[Accel] WHO_AM_I failed"); return; }
    if (whoAmI != WHO_AM_I_EXPECTED) { Serial.printf("[Accel] wrong ID: 0x%02X\n", whoAmI); return; }

    initialized = true;
    Serial.println("[Accel] MPU6050 ready.");

    float tx, ty, tz;
    if (readAccelG(tx, ty, tz)) {
      Serial.printf("[Accel] Initial: ax=%.3f ay=%.3f az=%.3f\n", tx, ty, tz);
      ax = tx; ay = ty; az = tz;
    }
  }

  void read() {
    if (!initialized) return;
    unsigned long now = millis();
    if (now - lastReadMs < SAMPLE_MS) return;
    lastReadMs = now;

    float nx, ny, nz;
    if (!readAccelG(nx, ny, nz)) {
      consecutiveReadFailures++;
      if (consecutiveReadFailures >= MAX_READ_FAILURES) recoverI2C();
    } else {
      consecutiveReadFailures = 0;
      ax = nx; ay = ny; az = nz;
    }
  }
}

// ============================================================
// Capacitive Touch Sensors — debounced pad states only
// ============================================================
namespace Touch {
  struct TouchSensor {
    uint8_t pin;
    bool currentState;
    bool lastState;
    unsigned long lastChangeTime;
  };

  constexpr unsigned long DEBOUNCE_MS = 40;

  TouchSensor sensors[] = {
    {13, false, false, 0},  // 0: front_left
    {12, false, false, 0},  // 1: front_right
    {14, false, false, 0},  // 2: back_left
    {27, false, false, 0},  // 3: back_right
    { 5, false, false, 0},  // 4: upper_back
    { 4, false, false, 0},  // 5: lower_back
    {15, false, false, 0},  // 6: upper_chest
    {32, false, false, 0},  // 7: lower_chest
  };

  constexpr size_t SENSOR_COUNT = sizeof(sensors) / sizeof(sensors[0]);

  void init() {
    Serial.println("[Touch] Initializing sensors...");
    for (size_t i = 0; i < SENSOR_COUNT; i++) {
      pinMode(sensors[i].pin, INPUT);
      sensors[i].currentState = digitalRead(sensors[i].pin);
      sensors[i].lastState = sensors[i].currentState;
      sensors[i].lastChangeTime = millis();
    }
    Serial.println("[Touch] Ready.");
  }

  void read() {
    unsigned long now = millis();
    for (size_t i = 0; i < SENSOR_COUNT; i++) {
      bool rawState = digitalRead(sensors[i].pin);
      if (rawState != sensors[i].lastState) {
        sensors[i].lastChangeTime = now;
        sensors[i].lastState = rawState;
      }
      if ((now - sensors[i].lastChangeTime) > DEBOUNCE_MS) {
        sensors[i].currentState = rawState;
      }
    }
  }
}

// ============================================================
// Compact JSON Output (~100 bytes vs ~140 with ArduinoJson)
// ============================================================
namespace Output {
  unsigned long lastSendMs = 0;

  void send() {
    unsigned long now = millis();
    if (now - lastSendMs < Config::SEND_INTERVAL_MS) return;
    lastSendMs = now;

    char buf[160];
    int len = snprintf(buf, sizeof(buf),
      "{\"type\":\"sensor_data\",\"ts\":%.1f,\"imu\":{\"ax\":%.3f,\"ay\":%.3f,\"az\":%.3f},\"touch\":{\"pads\":[",
      (double)now / 1000.0, Accel::ax, Accel::ay, Accel::az);

    bool first = true;
    for (size_t i = 0; i < Touch::SENSOR_COUNT; i++) {
      if (Touch::sensors[i].currentState == HIGH) {
        len += snprintf(buf + len, sizeof(buf) - len, first ? "%d" : ",%d", (int)i);
        first = false;
      }
    }
    strncat(buf, "]}}", sizeof(buf) - len - 1);
    Serial.println(buf);
  }
}

// ============================================================
// Main
// ============================================================
void setup() {
  Serial.begin(115200);
  delay(1000);
  Accel::init();
  Touch::init();
}

void loop() {
  Accel::read();
  Touch::read();
  Output::send();
}
