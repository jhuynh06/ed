/**
 * ESP32 SpeakerSerial — Receives PCM audio over USB serial, plays via MAX98357A.
 *
 * Protocol (same sync marker as MicrophoneSerial):
 *   [0xED 0x0A] [2-byte LE sample count] [PCM bytes...]
 *   PCM is 16-bit signed LE mono at 16kHz.
 *
 * Sends "SPEAKER_READY\n" on boot so the bridge can identify this port.
 */

#include <Arduino.h>
#include <driver/i2s.h>

// ===== MAX98357A Pins =====
#define I2S_BCLK  27
#define I2S_LRC   26
#define I2S_DOUT  25

// ===== Config =====
#define I2S_PORT      I2S_NUM_0
#define SAMPLE_RATE   16000
#define BAUD_RATE     921600
#define MAX_SAMPLES   2048

static const uint8_t SYNC_0 = 0xED;
static const uint8_t SYNC_1 = 0x0A;

uint8_t pcmBuffer[MAX_SAMPLES * 2];

void i2s_init() {
    i2s_config_t cfg = {
        .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_TX),
        .sample_rate = SAMPLE_RATE,
        .bits_per_sample = I2S_BITS_PER_SAMPLE_16BIT,
        .channel_format = I2S_CHANNEL_FMT_ONLY_LEFT,
        .communication_format = I2S_COMM_FORMAT_STAND_I2S,
        .intr_alloc_flags = ESP_INTR_FLAG_LEVEL1,
        .dma_buf_count = 8,
        .dma_buf_len = 1024,
        .use_apll = false,
        .tx_desc_auto_clear = true
    };

    i2s_pin_config_t pins = {
        .bck_io_num   = I2S_BCLK,
        .ws_io_num    = I2S_LRC,
        .data_out_num = I2S_DOUT,
        .data_in_num  = I2S_PIN_NO_CHANGE
    };

    i2s_driver_install(I2S_PORT, &cfg, 0, NULL);
    i2s_set_pin(I2S_PORT, &pins);
    i2s_zero_dma_buffer(I2S_PORT);
}

// Read exactly n bytes from serial, returns false on timeout
bool serialReadBytes(uint8_t* buf, size_t n, unsigned long timeoutMs = 500) {
    size_t got = 0;
    unsigned long start = millis();
    while (got < n) {
        if (Serial.available()) {
            buf[got++] = Serial.read();
            start = millis();  // reset timeout on each byte
        } else if (millis() - start > timeoutMs) {
            return false;
        }
    }
    return true;
}

void setup() {
    Serial.begin(BAUD_RATE);
    i2s_init();
    // Identify this board to the bridge
    Serial.println("SPEAKER_READY");
}

void loop() {
    // Wait for sync marker
    if (Serial.available() < 1) return;

    uint8_t b = Serial.read();
    if (b != SYNC_0) return;

    uint8_t b2;
    if (!serialReadBytes(&b2, 1, 100) || b2 != SYNC_1) return;

    // Read sample count
    uint8_t countBuf[2];
    if (!serialReadBytes(countBuf, 2)) return;
    uint16_t sampleCount = countBuf[0] | (countBuf[1] << 8);

    if (sampleCount == 0 || sampleCount > MAX_SAMPLES) return;

    // Read PCM data
    uint32_t byteCount = sampleCount * 2;
    if (!serialReadBytes(pcmBuffer, byteCount)) return;

    // Play through I2S
    size_t written;
    i2s_write(I2S_PORT, pcmBuffer, byteCount, &written, portMAX_DELAY);
}
