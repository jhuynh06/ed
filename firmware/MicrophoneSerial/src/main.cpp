/**
 * ESP32 MicrophoneSerial — Streams INMP441 audio over USB serial.
 * No WiFi needed. SerialAudioBridge.py reads from the COM port.
 *
 * Protocol: [0xED 0xAU] [2-byte little-endian sample count] [PCM bytes...]
 * PCM is 16-bit signed little-endian mono at 16kHz.
 */

#include <Arduino.h>
#include <driver/i2s.h>

// ===== INMP441 Pins =====
#define I2S_WS   25
#define I2S_SCK  26
#define I2S_SD   33

// ===== I2S Config =====
#define I2S_PORT       I2S_NUM_0
#define SAMPLE_RATE    16000
#define SAMPLE_BITS    I2S_BITS_PER_SAMPLE_32BIT
#define DMA_BUF_COUNT  8
#define DMA_BUF_LEN    512
#define CHUNK_SAMPLES  512  // 32ms at 16kHz

// ===== Serial Config =====
#define BAUD_RATE      921600
static const uint8_t SYNC_MARKER[2] = {0xED, 0xAU};

// Buffers
int32_t i2sBuffer[CHUNK_SAMPLES * 2];
int16_t audioBuffer[CHUNK_SAMPLES];

// DC offset
float dcOffset = 0.0f;
bool dcInitialized = false;

void i2s_init() {
    const i2s_config_t i2s_config = {
        .mode            = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_RX),
        .sample_rate     = SAMPLE_RATE,
        .bits_per_sample = (i2s_bits_per_sample_t)SAMPLE_BITS,
        .channel_format  = I2S_CHANNEL_FMT_RIGHT_LEFT,
        .communication_format = I2S_COMM_FORMAT_STAND_MSB,
        .intr_alloc_flags     = ESP_INTR_FLAG_LEVEL1,
        .dma_buf_count   = DMA_BUF_COUNT,
        .dma_buf_len     = DMA_BUF_LEN,
        .use_apll        = false,
        .tx_desc_auto_clear = false,
        .fixed_mclk      = 0
    };

    const i2s_pin_config_t pin_config = {
        .bck_io_num   = I2S_SCK,
        .ws_io_num    = I2S_WS,
        .data_out_num = I2S_PIN_NO_CHANGE,
        .data_in_num  = I2S_SD
    };

    ESP_ERROR_CHECK(i2s_driver_install(I2S_PORT, &i2s_config, 0, NULL));
    ESP_ERROR_CHECK(i2s_set_pin(I2S_PORT, &pin_config));
    i2s_zero_dma_buffer(I2S_PORT);

    // Discard initial noisy samples
    size_t discard;
    int32_t trash[256];
    for (int i = 0; i < 10; i++) {
        i2s_read(I2S_PORT, trash, sizeof(trash), &discard, portMAX_DELAY);
    }
}

void readAndSend() {
    size_t bytesRead = 0;
    i2s_read(I2S_PORT, i2sBuffer, CHUNK_SAMPLES * 2 * sizeof(int32_t), &bytesRead, portMAX_DELAY);

    int samplesRead = bytesRead / (2 * sizeof(int32_t));

    for (int i = 0; i < samplesRead; i++) {
        int32_t raw = i2sBuffer[i * 2];
        int32_t shifted = raw >> 12;

        if (!dcInitialized) {
            dcOffset = (float)shifted;
            dcInitialized = true;
        } else {
            dcOffset = dcOffset * 0.999f + (float)shifted * 0.001f;
        }

        int32_t cleaned = shifted - (int32_t)dcOffset;
        if (cleaned > 32767) cleaned = 32767;
        if (cleaned < -32768) cleaned = -32768;
        audioBuffer[i] = (int16_t)cleaned;
    }

    // Send: sync marker + sample count + PCM data
    uint16_t count = (uint16_t)samplesRead;
    Serial.write(SYNC_MARKER, 2);
    Serial.write((uint8_t*)&count, 2);
    Serial.write((uint8_t*)audioBuffer, samplesRead * sizeof(int16_t));
}

void setup() {
    Serial.begin(BAUD_RATE);
    i2s_init();
}

void loop() {
    readAndSend();
}
