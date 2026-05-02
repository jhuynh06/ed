#include <Arduino.h>
#include <Wire.h>
#include <math.h>

// ============================================================
// MPU6050 Accelerometer (Shake Detection)
// ============================================================
namespace Accel {
  constexpr uint8_t MPU_ADDR = 0x68;

  constexpr int SDA_PIN = 21;
  constexpr int SCL_PIN = 22;

  constexpr uint8_t REG_PWR_MGMT_1   = 0x6B;
  constexpr uint8_t REG_WHO_AM_I     = 0x75;
  constexpr uint8_t REG_ACCEL_XOUT_H = 0x3B;

  constexpr uint8_t WHO_AM_I_EXPECTED = 0x68;
  constexpr float ACCEL_LSB_PER_G = 16384.0f;   // default +/-2g

  // Tuning
  constexpr float CHANGE_THRESHOLD_G = 0.25f;   // per-axis change threshold
  constexpr unsigned long SAMPLE_MS = 10;        // 100 Hz
  constexpr unsigned long COOLDOWN_MS = 200;     // min time between prints

  bool initialized = false;
  float lastAx = 0.0f, lastAy = 0.0f, lastAz = 0.0f;
  unsigned long lastSampleMs = 0;
  unsigned long lastTriggerMs = 0;

  bool writeRegister8(uint8_t reg, uint8_t value) {
    Wire.beginTransmission(MPU_ADDR);
    Wire.write(reg);
    Wire.write(value);
    return Wire.endTransmission() == 0;
  }

  bool readRegisters(uint8_t startReg, uint8_t *buffer, size_t len) {
    if (buffer == nullptr || len == 0U) {
      return false;
    }

    Wire.beginTransmission(MPU_ADDR);
    Wire.write(startReg);

    if (Wire.endTransmission(false) != 0) {
      return false;
    }

    const size_t received = Wire.requestFrom(MPU_ADDR, len);
    if (received != len) {
      return false;
    }

    for (size_t i = 0; i < len; ++i) {
      const int value = Wire.read();
      if (value < 0) {
        return false;
      }
      buffer[i] = static_cast<uint8_t>(value);
    }

    return true;
  }

  int16_t joinBytes(uint8_t highByte, uint8_t lowByte) {
    return static_cast<int16_t>(
      (static_cast<uint16_t>(highByte) << 8) |
      static_cast<uint16_t>(lowByte)
    );
  }

  bool readAccelG(float &ax_g, float &ay_g, float &az_g) {
    uint8_t raw[6] = {0};

    if (!readRegisters(REG_ACCEL_XOUT_H, raw, sizeof(raw))) {
      return false;
    }

    const int16_t ax = joinBytes(raw[0], raw[1]);
    const int16_t ay = joinBytes(raw[2], raw[3]);
    const int16_t az = joinBytes(raw[4], raw[5]);

    ax_g = static_cast<float>(ax) / ACCEL_LSB_PER_G;
    ay_g = static_cast<float>(ay) / ACCEL_LSB_PER_G;
    az_g = static_cast<float>(az) / ACCEL_LSB_PER_G;

    return true;
  }

  void init() {
    Serial.println("Initializing MPU6050...");

    if (!Wire.setPins(SDA_PIN, SCL_PIN)) {
      Serial.println("Wire.setPins failed - accelerometer disabled");
      return;
    }

    if (!Wire.begin()) {
      Serial.println("Wire.begin failed - accelerometer disabled");
      return;
    }

    Wire.setClock(400000);
    Wire.setTimeOut(50);

    if (!writeRegister8(REG_PWR_MGMT_1, 0x00)) {
      Serial.println("Failed to wake MPU6050 - accelerometer disabled");
      return;
    }

    delay(100);

    uint8_t whoAmI = 0;
    if (!readRegisters(REG_WHO_AM_I, &whoAmI, 1U)) {
      Serial.println("Failed to read WHO_AM_I - accelerometer disabled");
      return;
    }

    Serial.print("WHO_AM_I = 0x");
    Serial.println(whoAmI, HEX);

    if (whoAmI != WHO_AM_I_EXPECTED) {
      Serial.println("MPU6050 not found at 0x68 - accelerometer disabled");
      return;
    }

    float ax = 0.0f, ay = 0.0f, az = 0.0f;
    if (readAccelG(ax, ay, az)) {
      lastAx = ax;
      lastAy = ay;
      lastAz = az;
    }

    initialized = true;
    Serial.println("MPU6050 ready.");
  }

  void update() {
    if (!initialized) {
      return;
    }

    const unsigned long now = millis();

    if (now - lastSampleMs < SAMPLE_MS) {
      return;
    }
    lastSampleMs = now;

    float ax = 0.0f, ay = 0.0f, az = 0.0f;

    if (!readAccelG(ax, ay, az)) {
      return;
    }

    const float dx = fabsf(ax - lastAx);
    const float dy = fabsf(ay - lastAy);
    const float dz = fabsf(az - lastAz);

    if ((dx > CHANGE_THRESHOLD_G || dy > CHANGE_THRESHOLD_G || dz > CHANGE_THRESHOLD_G)
        && (now - lastTriggerMs) > COOLDOWN_MS) {
      Serial.print("ACCEL CHANGE: dX=");
      Serial.print(dx, 3);
      Serial.print("g dY=");
      Serial.print(dy, 3);
      Serial.print("g dZ=");
      Serial.print(dz, 3);
      Serial.print("g  (X=");
      Serial.print(ax, 2);
      Serial.print(" Y=");
      Serial.print(ay, 2);
      Serial.print(" Z=");
      Serial.print(az, 2);
      Serial.println(")");
      lastTriggerMs = now;
    }

    lastAx = ax;
    lastAy = ay;
    lastAz = az;
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
  };

  constexpr unsigned long DEBOUNCE_MS = 40;

  TouchSensor sensors[] = {
    {"front left",  13, false, false, 0},
    {"front right", 12, false, false, 0},
    {"back left",   14, false, false, 0},
    {"back right",  27, false, false, 0},
    {"upper back",  26, false, false, 0},
    {"lower back",  25, false, false, 0},
    {"upper chest", 33, false, false, 0},
    {"lower chest", 32, false, false, 0}
  };

  constexpr size_t SENSOR_COUNT = sizeof(sensors) / sizeof(sensors[0]);

  void init() {
    Serial.println("Initializing touch sensors...");

    for (size_t i = 0; i < SENSOR_COUNT; i++) {
      pinMode(sensors[i].pin, INPUT);
      sensors[i].currentState = digitalRead(sensors[i].pin);
      sensors[i].lastState = sensors[i].currentState;
      sensors[i].lastChangeTime = millis();
    }

    Serial.println("Touch sensors ready.");
  }

  void update() {
    const unsigned long now = millis();

    for (size_t i = 0; i < SENSOR_COUNT; i++) {
      bool rawState = digitalRead(sensors[i].pin);

      if (rawState != sensors[i].lastState) {
        sensors[i].lastChangeTime = now;
        sensors[i].lastState = rawState;
      }

      if ((now - sensors[i].lastChangeTime) > DEBOUNCE_MS) {
        if (sensors[i].currentState != rawState) {
          sensors[i].currentState = rawState;

          if (sensors[i].currentState == HIGH) {
            Serial.print("TOUCHED: ");
            Serial.println(sensors[i].name);
          } else {
            Serial.print("RELEASED: ");
            Serial.println(sensors[i].name);
          }
        }
      }
    }
  }
}

// ============================================================
// Main
// ============================================================
void setup() {
  Serial.begin(115200);
  delay(1000);

  Serial.println();
  Serial.println("=== Combined Sensor System ===");

  Accel::init();
  Touch::init();

  Serial.println("All systems ready.");
}

void loop() {
  Accel::update();
  Touch::update();
}
