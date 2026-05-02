#include <Arduino.h>
#include <Wire.h>
#include <ArduinoJson.h>
#include <math.h>

// ============================================================
// Configuration
// ============================================================
namespace Config {
  // How often to send a JSON sensor packet over serial (ms)
  constexpr unsigned long SEND_INTERVAL_MS = 250;  // 4 Hz
}

// ============================================================
// MPU6050 Accelerometer
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

  constexpr unsigned long SAMPLE_MS = 10;  // 100 Hz internal

  bool initialized = false;
  unsigned long lastSampleMs = 0;

  float ax = 0.0f, ay = 0.0f, az = 0.0f;

  // Derived features
  float jerkMagnitude = 0.0f;
  float prevMag = 1.0f;
  unsigned long stillnessStartMs = 0;
  float stillnessDurationS = 0.0f;
  bool rockingDetected = false;
  bool hugDetected = false;
  bool fallDetected = false;

  // Rocking detection via zero-crossings
  constexpr int JERK_HISTORY_SIZE = 20;
  float jerkHistory[JERK_HISTORY_SIZE] = {0};
  int jerkIdx = 0;

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

    readAccelG(ax, ay, az);
    prevMag = sqrtf(ax*ax + ay*ay + az*az);
    stillnessStartMs = millis();
    initialized = true;
    Serial.println("[Accel] MPU6050 ready.");
  }

  void update() {
    if (!initialized) return;
    unsigned long now = millis();
    if (now - lastSampleMs < SAMPLE_MS) return;
    lastSampleMs = now;

    float nx, ny, nz;
    if (!readAccelG(nx, ny, nz)) return;

    float mag = sqrtf(nx*nx + ny*ny + nz*nz);
    float jerk = fabsf(mag - prevMag);
    prevMag = mag;

    jerkMagnitude = jerkMagnitude * 0.7f + jerk * 0.3f;

    if (jerkMagnitude < 0.02f) {
      stillnessDurationS = (float)(now - stillnessStartMs) / 1000.0f;
    } else {
      stillnessStartMs = now;
      stillnessDurationS = 0.0f;
    }

    fallDetected = (mag < 0.3f) || (jerk > 2.5f);

    jerkHistory[jerkIdx] = mag - 1.0f;
    jerkIdx = (jerkIdx + 1) % JERK_HISTORY_SIZE;
    int zeroCrossings = 0;
    for (int i = 1; i < JERK_HISTORY_SIZE; i++) {
      if ((jerkHistory[i-1] >= 0 && jerkHistory[i] < 0) ||
          (jerkHistory[i-1] < 0 && jerkHistory[i] >= 0)) {
        zeroCrossings++;
      }
    }
    rockingDetected = (zeroCrossings >= 6) && (jerkMagnitude > 0.05f) && (jerkMagnitude < 0.8f);
    hugDetected = (fabsf(nx) > 0.3f && fabsf(ny) > 0.3f && stillnessDurationS > 1.5f);

    ax = nx; ay = ny; az = nz;
  }
}

// ============================================================
// Capacitive Touch Sensors
// ============================================================
namespace Touch {
  struct TouchSensor {
    const char* name;
    uint8_t pin;
    bool currentState;
    bool lastState;
    unsigned long lastChangeTime;
    unsigned long pressStartMs;
  };

  constexpr unsigned long DEBOUNCE_MS = 40;

  TouchSensor sensors[] = {
    {"front_left",  13, false, false, 0, 0},
    {"front_right", 12, false, false, 0, 0},
    {"back_left",   14, false, false, 0, 0},
    {"back_right",  27, false, false, 0, 0},
    {"upper_back",  26, false, false, 0, 0},
    {"lower_back",  25, false, false, 0, 0},
    {"upper_chest", 33, false, false, 0, 0},
    {"lower_chest", 32, false, false, 0, 0}
  };

  constexpr size_t SENSOR_COUNT = sizeof(sensors) / sizeof(sensors[0]);

  bool anyContact = false;
  float squeezeIntensity = 0.0f;
  float gripDurationS = 0.0f;
  bool pettingDetected = false;
  int activePadCount = 0;

  unsigned long lastActivationMs = 0;
  int sequentialActivations = 0;

  void init() {
    Serial.println("[Touch] Initializing sensors...");
    for (size_t i = 0; i < SENSOR_COUNT; i++) {
      pinMode(sensors[i].pin, INPUT);
      sensors[i].currentState = digitalRead(sensors[i].pin);
      sensors[i].lastState = sensors[i].currentState;
      sensors[i].lastChangeTime = millis();
      sensors[i].pressStartMs = 0;
    }
    Serial.println("[Touch] Ready.");
  }

  void update() {
    unsigned long now = millis();
    activePadCount = 0;
    float longestGrip = 0.0f;

    for (size_t i = 0; i < SENSOR_COUNT; i++) {
      bool rawState = digitalRead(sensors[i].pin);

      if (rawState != sensors[i].lastState) {
        sensors[i].lastChangeTime = now;
        sensors[i].lastState = rawState;
      }

      if ((now - sensors[i].lastChangeTime) > DEBOUNCE_MS) {
        if (sensors[i].currentState != rawState) {
          sensors[i].currentState = rawState;
          if (rawState == HIGH) {
            sensors[i].pressStartMs = now;
            if (now - lastActivationMs < 500) {
              sequentialActivations++;
            } else {
              sequentialActivations = 1;
            }
            lastActivationMs = now;
          }
        }
      }

      if (sensors[i].currentState == HIGH) {
        activePadCount++;
        float dur = (float)(now - sensors[i].pressStartMs) / 1000.0f;
        if (dur > longestGrip) longestGrip = dur;
      }
    }

    anyContact = (activePadCount > 0);
    squeezeIntensity = (float)activePadCount / (float)SENSOR_COUNT;
    gripDurationS = longestGrip;
    pettingDetected = (sequentialActivations >= 3) && (now - lastActivationMs < 1000);

    if (now - lastActivationMs > 1500) {
      sequentialActivations = 0;
      pettingDetected = false;
    }
  }
}

// ============================================================
// Serial JSON Output
// ============================================================
namespace Output {
  unsigned long lastSendMs = 0;

  void send() {
    unsigned long now = millis();
    if (now - lastSendMs < Config::SEND_INTERVAL_MS) return;
    lastSendMs = now;

    JsonDocument doc;
    doc["type"] = "sensor_data";
    doc["ts"] = (double)millis() / 1000.0;

    JsonObject imu = doc["imu"].to<JsonObject>();
    imu["jerk_magnitude"] = Accel::jerkMagnitude;
    imu["hug_detected"] = Accel::hugDetected;
    imu["fall_detected"] = Accel::fallDetected;
    imu["tremor_power"] = 0.0;
    imu["rocking_detected"] = Accel::rockingDetected;
    imu["stillness_duration_s"] = Accel::stillnessDurationS;

    JsonObject hr = doc["hr"].to<JsonObject>();
    hr["bpm"] = 0;
    hr["spo2"] = 0;
    hr["valid"] = false;
    hr["baseline_bpm"] = 72.0;
    hr["elevation_pct"] = 0.0;

    JsonObject touch = doc["touch"].to<JsonObject>();
    touch["any_contact"] = Touch::anyContact;
    touch["squeeze_intensity"] = Touch::squeezeIntensity;
    touch["petting_detected"] = Touch::pettingDetected;
    touch["grip_duration_s"] = Touch::gripDurationS;
    JsonArray pads = touch["active_pads"].to<JsonArray>();
    for (size_t i = 0; i < Touch::SENSOR_COUNT; i++) {
      if (Touch::sensors[i].currentState == HIGH) {
        pads.add((int)i);
      }
    }

    serializeJson(doc, Serial);
    Serial.println();  // newline delimiter
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
  Accel::update();
  Touch::update();
  Output::send();
}
