#include <Arduino.h>
#include <unity.h>
#include <math.h>

// ============================================================
// Replicate core logic functions for unit testing
// ============================================================

static constexpr float ACCEL_LSB_PER_G = 16384.0f;
static constexpr float CHANGE_THRESHOLD_G = 0.15f;

int16_t joinBytes(uint8_t highByte, uint8_t lowByte) {
  return static_cast<int16_t>(
    (static_cast<uint16_t>(highByte) << 8) |
    static_cast<uint16_t>(lowByte)
  );
}

float rawToG(int16_t raw) {
  return static_cast<float>(raw) / ACCEL_LSB_PER_G;
}

float computeMagnitude(float ax, float ay, float az) {
  return sqrtf(ax * ax + ay * ay + az * az);
}

bool isAxisChangeDetected(float current, float last) {
  return fabsf(current - last) > CHANGE_THRESHOLD_G;
}

// ============================================================
// Tests: joinBytes
// ============================================================

void test_joinBytes_zero(void) {
  TEST_ASSERT_EQUAL_INT16(0, joinBytes(0x00, 0x00));
}

void test_joinBytes_positive(void) {
  TEST_ASSERT_EQUAL_INT16(16384, joinBytes(0x40, 0x00));
}

void test_joinBytes_negative(void) {
  TEST_ASSERT_EQUAL_INT16(-1, joinBytes(0xFF, 0xFF));
}

void test_joinBytes_negative_large(void) {
  TEST_ASSERT_EQUAL_INT16(-16384, joinBytes(0xC0, 0x00));
}

void test_joinBytes_mixed(void) {
  TEST_ASSERT_EQUAL_INT16(256, joinBytes(0x01, 0x00));
  TEST_ASSERT_EQUAL_INT16(1, joinBytes(0x00, 0x01));
}

// ============================================================
// Tests: rawToG conversion
// ============================================================

void test_rawToG_one_g(void) {
  TEST_ASSERT_FLOAT_WITHIN(0.001f, 1.0f, rawToG(16384));
}

void test_rawToG_negative_one_g(void) {
  TEST_ASSERT_FLOAT_WITHIN(0.001f, -1.0f, rawToG(-16384));
}

void test_rawToG_zero(void) {
  TEST_ASSERT_FLOAT_WITHIN(0.001f, 0.0f, rawToG(0));
}

void test_rawToG_two_g(void) {
  TEST_ASSERT_FLOAT_WITHIN(0.01f, 2.0f, rawToG(32767));
}

// ============================================================
// Tests: magnitude computation
// ============================================================

void test_magnitude_at_rest(void) {
  float mag = computeMagnitude(0.0f, 0.0f, 1.0f);
  TEST_ASSERT_FLOAT_WITHIN(0.001f, 1.0f, mag);
}

void test_magnitude_tilted(void) {
  float mag = computeMagnitude(0.707f, 0.0f, 0.707f);
  TEST_ASSERT_FLOAT_WITHIN(0.01f, 1.0f, mag);
}

void test_magnitude_shaking(void) {
  float mag = computeMagnitude(1.5f, 1.0f, 1.5f);
  TEST_ASSERT_TRUE(mag > 2.0f);
}

// ============================================================
// Tests: per-axis change detection
// ============================================================

void test_axis_change_not_detected_small(void) {
  // 0.05g change is below 0.15g threshold
  TEST_ASSERT_FALSE(isAxisChangeDetected(1.0f, 0.95f));
}

void test_axis_change_not_detected_at_threshold(void) {
  // Exactly at threshold should NOT trigger (must be >)
  TEST_ASSERT_FALSE(isAxisChangeDetected(1.15f, 1.0f));
}

void test_axis_change_detected_above_threshold(void) {
  // 0.2g change exceeds 0.15g threshold
  TEST_ASSERT_TRUE(isAxisChangeDetected(1.2f, 1.0f));
}

void test_axis_change_detected_negative(void) {
  // Negative direction change
  TEST_ASSERT_TRUE(isAxisChangeDetected(0.5f, 1.0f));
}

void test_axis_change_detected_large(void) {
  TEST_ASSERT_TRUE(isAxisChangeDetected(2.0f, 0.0f));
}

// ============================================================
// Tests: touch sensor debounce logic
// ============================================================

struct MockTouchSensor {
  bool currentState;
  bool lastState;
  unsigned long lastChangeTime;
};

bool simulateDebounce(MockTouchSensor &sensor, bool rawState, unsigned long now, unsigned long debounceMs) {
  bool stateChanged = false;

  if (rawState != sensor.lastState) {
    sensor.lastChangeTime = now;
    sensor.lastState = rawState;
  }

  if ((now - sensor.lastChangeTime) > debounceMs) {
    if (sensor.currentState != rawState) {
      sensor.currentState = rawState;
      stateChanged = true;
    }
  }

  return stateChanged;
}

void test_debounce_no_change(void) {
  MockTouchSensor s = {false, false, 0};
  TEST_ASSERT_FALSE(simulateDebounce(s, false, 100, 40));
}

void test_debounce_rejects_short_press(void) {
  MockTouchSensor s = {false, false, 0};
  simulateDebounce(s, true, 100, 40);
  TEST_ASSERT_FALSE(simulateDebounce(s, true, 130, 40));
  TEST_ASSERT_FALSE(s.currentState);
}

void test_debounce_accepts_long_press(void) {
  MockTouchSensor s = {false, false, 0};
  simulateDebounce(s, true, 100, 40);
  bool changed = simulateDebounce(s, true, 150, 40);
  TEST_ASSERT_TRUE(changed);
  TEST_ASSERT_TRUE(s.currentState);
}

void test_debounce_release(void) {
  MockTouchSensor s = {true, true, 0};
  simulateDebounce(s, false, 200, 40);
  bool changed = simulateDebounce(s, false, 250, 40);
  TEST_ASSERT_TRUE(changed);
  TEST_ASSERT_FALSE(s.currentState);
}

void test_debounce_bouncing_rejected(void) {
  MockTouchSensor s = {false, false, 0};
  simulateDebounce(s, true, 100, 40);
  simulateDebounce(s, false, 110, 40);
  simulateDebounce(s, true, 120, 40);
  bool changed = simulateDebounce(s, true, 130, 40);
  TEST_ASSERT_FALSE(changed);
  TEST_ASSERT_FALSE(s.currentState);
}

// ============================================================
// Test runner (runs on ESP32)
// ============================================================

void setup() {
  delay(2000);  // give serial monitor time to connect

  UNITY_BEGIN();

  // joinBytes tests
  RUN_TEST(test_joinBytes_zero);
  RUN_TEST(test_joinBytes_positive);
  RUN_TEST(test_joinBytes_negative);
  RUN_TEST(test_joinBytes_negative_large);
  RUN_TEST(test_joinBytes_mixed);

  // rawToG tests
  RUN_TEST(test_rawToG_one_g);
  RUN_TEST(test_rawToG_negative_one_g);
  RUN_TEST(test_rawToG_zero);
  RUN_TEST(test_rawToG_two_g);

  // magnitude tests
  RUN_TEST(test_magnitude_at_rest);
  RUN_TEST(test_magnitude_tilted);
  RUN_TEST(test_magnitude_shaking);

  // axis change detection tests
  RUN_TEST(test_axis_change_not_detected_small);
  RUN_TEST(test_axis_change_not_detected_at_threshold);
  RUN_TEST(test_axis_change_detected_above_threshold);
  RUN_TEST(test_axis_change_detected_negative);
  RUN_TEST(test_axis_change_detected_large);

  // debounce tests
  RUN_TEST(test_debounce_no_change);
  RUN_TEST(test_debounce_rejects_short_press);
  RUN_TEST(test_debounce_accepts_long_press);
  RUN_TEST(test_debounce_release);
  RUN_TEST(test_debounce_bouncing_rejected);

  UNITY_END();
}

void loop() {
}
