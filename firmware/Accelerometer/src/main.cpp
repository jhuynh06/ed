#include <Arduino.h>
#include <Wire.h>
#include <math.h>

namespace {
  constexpr uint8_t MPU_ADDR = 0x68;

  constexpr int SDA_PIN = 21;
  constexpr int SCL_PIN = 22;

  constexpr uint8_t REG_PWR_MGMT_1   = 0x6B;
  constexpr uint8_t REG_WHO_AM_I     = 0x75;
  constexpr uint8_t REG_ACCEL_XOUT_H = 0x3B;

  constexpr uint8_t WHO_AM_I_EXPECTED = 0x68;
  constexpr float ACCEL_LSB_PER_G = 16384.0f;   // default +/-2g

  // Tuning
  constexpr float SHAKE_THRESHOLD_G = 0.35f;    // try 0.25 to 0.60
  constexpr unsigned long SAMPLE_MS = 25;       // 40 Hz
  constexpr unsigned long COOLDOWN_MS = 800;    // avoid repeat spam
}

float lastMagnitudeG = 1.0f;
unsigned long lastSampleMs = 0;
unsigned long lastTriggerMs = 0;

bool writeRegister8(const uint8_t reg, const uint8_t value) {
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(reg);
  Wire.write(value);
  return Wire.endTransmission() == 0;
}

bool readRegisters(const uint8_t startReg, uint8_t *buffer, const size_t len) {
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

int16_t joinBytes(const uint8_t highByte, const uint8_t lowByte) {
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

void setup() {
  Serial.begin(115200);
  delay(1000);

  Serial.println();
  Serial.println("MPU6050 shake detector");

  if (!Wire.setPins(SDA_PIN, SCL_PIN)) {
    Serial.println("Wire.setPins failed");
    while (true) {
      delay(1000);
    }
  }

  if (!Wire.begin()) {
    Serial.println("Wire.begin failed");
    while (true) {
      delay(1000);
    }
  }

  Wire.setClock(400000);
  Wire.setTimeOut(50);

  if (!writeRegister8(REG_PWR_MGMT_1, 0x00)) {
    Serial.println("Failed to wake MPU6050");
    while (true) {
      delay(1000);
    }
  }

  delay(100);

  uint8_t whoAmI = 0;
  if (!readRegisters(REG_WHO_AM_I, &whoAmI, 1U)) {
    Serial.println("Failed to read WHO_AM_I");
    while (true) {
      delay(1000);
    }
  }

  Serial.print("WHO_AM_I = 0x");
  Serial.println(whoAmI, HEX);

  if (whoAmI != WHO_AM_I_EXPECTED) {
    Serial.println("MPU6050 not found at 0x68");
    while (true) {
      delay(1000);
    }
  }

  float ax = 0.0f;
  float ay = 0.0f;
  float az = 0.0f;
  if (readAccelG(ax, ay, az)) {
    lastMagnitudeG = sqrtf(ax * ax + ay * ay + az * az);
  }

  Serial.println("Ready. Shake the sensor.");
}

void loop() {
  const unsigned long now = millis();

  if (now - lastSampleMs < SAMPLE_MS) {
    return;
  }
  lastSampleMs = now;

  float ax = 0.0f;
  float ay = 0.0f;
  float az = 0.0f;

  if (!readAccelG(ax, ay, az)) {
    return;
  }

  const float magnitudeG = sqrtf(ax * ax + ay * ay + az * az);
  const float deltaG = fabsf(magnitudeG - lastMagnitudeG);
  lastMagnitudeG = magnitudeG;

  if (deltaG > SHAKE_THRESHOLD_G && (now - lastTriggerMs) > COOLDOWN_MS) {
    Serial.println("Decent shaking detected!");
    lastTriggerMs = now;
  }
}