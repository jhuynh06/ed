/**
 * ESP32 SpeakerSerial — Raw PCM over serial, ring buffer, dual-core playback.
 *
 * Core 1 (loop): reads raw PCM bytes from serial into ring buffer
 * Core 0 (task): drains ring buffer into I2S
 *
 * No framing protocol. Just raw 16-bit signed LE mono PCM at 16kHz.
 * Sends "SPEAKER_READY\n" on boot.
 */

#include <Arduino.h>
#include <driver/i2s.h>
#include <freertos/FreeRTOS.h>
#include <freertos/ringbuf.h>

#define I2S_BCLK  27
#define I2S_LRC   26
#define I2S_DOUT  25

#define I2S_PORT      I2S_NUM_0
#define SAMPLE_RATE   16000
#define BAUD_RATE     921600
#define RING_BUF_SIZE (32 * 1024)

static RingbufHandle_t ringBuf = NULL;

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

void i2s_task(void* param) {
    uint8_t buf[1024];
    while (true) {
        size_t itemSize = 0;
        void* item = xRingbufferReceiveUpTo(ringBuf, &itemSize, pdMS_TO_TICKS(50), sizeof(buf));
        if (item && itemSize > 0) {
            // Ensure even byte count for 16-bit samples
            size_t toWrite = itemSize & ~1;
            if (toWrite > 0) {
                size_t written;
                i2s_write(I2S_PORT, item, toWrite, &written, portMAX_DELAY);
            }
            vRingbufferReturnItem(ringBuf, item);
        }
    }
}

void setup() {
    Serial.setRxBufferSize(8192);
    Serial.begin(BAUD_RATE);
    i2s_init();

    ringBuf = xRingbufferCreate(RING_BUF_SIZE, RINGBUF_TYPE_BYTEBUF);
    xTaskCreatePinnedToCore(i2s_task, "i2s", 4096, NULL, 1, NULL, 0);

    Serial.println("SPEAKER_READY");
}

void loop() {
    int avail = Serial.available();
    if (avail <= 0) return;

    uint8_t buf[1024];
    int toRead = min(avail, (int)sizeof(buf));
    int got = Serial.readBytes(buf, toRead);
    if (got > 0) {
        xRingbufferSend(ringBuf, buf, got, 0);
    }
}
