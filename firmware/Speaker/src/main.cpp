/**
 * ESP32 Speaker Bridge — Receives audio from laptop over WebSocket and plays
 * through MAX98357A I2S amplifier.
 *
 * Uses a ring buffer to decouple WiFi reception from I2S playback.
 * The WebSocket callback fills the buffer, a FreeRTOS task drains it to I2S.
 * This absorbs WiFi jitter and prevents audio breakup.
 *
 * Hardware: MAX98357A I2S amplifier
 *   BCLK  → GPIO 27
 *   LRC   → GPIO 26
 *   DIN   → GPIO 25
 */

#include <Arduino.h>
#include <driver/i2s.h>
#include <freertos/ringbuf.h>
#include <WiFi.h>
#include <WebSocketsClient.h>

// ===== WiFi Configuration =====
const char* WIFI_SSID = "TristaniPhone";
const char* WIFI_PASS = "herothedog";

// ===== SpeakerBridge WebSocket =====
const char* WS_HOST = "172.20.10.2";
const uint16_t WS_PORT = 8082;
const char* WS_PATH = "/speaker";

// ===== I2S Pin Configuration (MAX98357A) =====
#define I2S_BCLK_PIN   27
#define I2S_LRC_PIN    26
#define I2S_DOUT_PIN   25

// ===== Buffering =====
// 32KB ring buffer ≈ 1 second of 16-bit mono 16kHz audio
#define RING_BUF_SIZE  (32 * 1024)
// Wait until this many bytes are buffered before starting playback
#define PREBUFFER_BYTES (8 * 1024)

// ===== State =====
WebSocketsClient webSocket;
RingbufHandle_t ringBuf = NULL;
TaskHandle_t i2sTaskHandle = NULL;

bool wsConnected = false;
bool i2sReady = false;
bool headerReceived = false;
bool playbackStarted = false;
bool eofReceived = false;

uint32_t expectedBytes = 0;
uint32_t bytesBuffered = 0;
uint32_t bytesPlayed = 0;

// ===== I2S Setup =====
void setupI2S(uint32_t sampleRate, uint16_t bitsPerSample, uint16_t numChannels) {
    if (i2sReady) {
        i2s_zero_dma_buffer(I2S_NUM_0);
        i2s_driver_uninstall(I2S_NUM_0);
        i2sReady = false;
    }

    i2s_bits_per_sample_t bits;
    switch (bitsPerSample) {
        case 32: bits = I2S_BITS_PER_SAMPLE_32BIT; break;
        case 16: bits = I2S_BITS_PER_SAMPLE_16BIT; break;
        default: bits = I2S_BITS_PER_SAMPLE_8BIT;  break;
    }

    i2s_channel_fmt_t chFmt = (numChannels == 2)
        ? I2S_CHANNEL_FMT_RIGHT_LEFT
        : I2S_CHANNEL_FMT_ONLY_LEFT;

    i2s_config_t cfg = {
        .mode            = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_TX),
        .sample_rate     = sampleRate,
        .bits_per_sample = bits,
        .channel_format  = chFmt,
        .communication_format = I2S_COMM_FORMAT_STAND_I2S,
        .intr_alloc_flags     = ESP_INTR_FLAG_LEVEL1,
        .dma_buf_count   = 16,
        .dma_buf_len     = 1024,
        .use_apll        = false,
        .tx_desc_auto_clear = true
    };

    i2s_pin_config_t pins = {
        .bck_io_num   = I2S_BCLK_PIN,
        .ws_io_num    = I2S_LRC_PIN,
        .data_out_num = I2S_DOUT_PIN,
        .data_in_num  = I2S_PIN_NO_CHANGE
    };

    ESP_ERROR_CHECK(i2s_driver_install(I2S_NUM_0, &cfg, 0, NULL));
    ESP_ERROR_CHECK(i2s_set_pin(I2S_NUM_0, &pins));
    i2s_zero_dma_buffer(I2S_NUM_0);

    i2sReady = true;
    Serial.printf("  I2S ready: %d Hz, %d-bit, %d ch\n", sampleRate, bitsPerSample, numChannels);
}

// ===== I2S Playback Task (runs on core 0) =====
void i2sTask(void* param) {
    const size_t readSize = 512;

    while (true) {
        // Wait until prebuffer threshold is reached
        if (!playbackStarted || !i2sReady) {
            vTaskDelay(pdMS_TO_TICKS(10));
            continue;
        }

        // Try to read from ring buffer (non-blocking with short timeout)
        size_t itemSize = 0;
        uint8_t* data = (uint8_t*)xRingbufferReceiveUpTo(
            ringBuf, &itemSize, pdMS_TO_TICKS(50), readSize
        );

        if (data && itemSize > 0) {
            size_t written;
            i2s_write(I2S_NUM_0, data, itemSize, &written, portMAX_DELAY);
            bytesPlayed += written;
            vRingbufferReturnItem(ringBuf, data);
        } else if (eofReceived) {
            // Buffer drained and EOF received — playback done
            Serial.printf("  Playback complete: %d / %d bytes\n", bytesPlayed, expectedBytes);

            delay(200);
            i2s_zero_dma_buffer(I2S_NUM_0);

            // Reset state
            headerReceived = false;
            playbackStarted = false;
            eofReceived = false;
            bytesBuffered = 0;
            bytesPlayed = 0;
            expectedBytes = 0;

            webSocket.sendTXT("{\"type\":\"ready\"}");
        }
    }
}

// ===== Process incoming binary message =====
void handleBinary(uint8_t* payload, size_t length) {
    // First binary message is the 12-byte header
    if (!headerReceived) {
        if (length < 12) {
            Serial.println("  Header too short, ignoring");
            return;
        }

        uint32_t sampleRate;
        uint16_t bitsPerSample, numChannels;
        uint32_t totalBytes;

        memcpy(&sampleRate,     payload + 0, 4);
        memcpy(&bitsPerSample,  payload + 4, 2);
        memcpy(&numChannels,    payload + 6, 2);
        memcpy(&totalBytes,     payload + 8, 4);

        expectedBytes = totalBytes;
        bytesBuffered = 0;
        bytesPlayed = 0;
        playbackStarted = false;
        eofReceived = false;
        headerReceived = true;

        Serial.printf("  Audio header: %d Hz, %d-bit, %d ch, %d bytes\n",
                      sampleRate, bitsPerSample, numChannels, totalBytes);

        setupI2S(sampleRate, bitsPerSample, numChannels);

        // If header message has trailing PCM data, buffer it
        if (length > 12) {
            size_t pcmLen = length - 12;
            xRingbufferSend(ringBuf, payload + 12, pcmLen, pdMS_TO_TICKS(100));
            bytesBuffered += pcmLen;
        }

        Serial.println("  Prebuffering...");
        return;
    }

    // Buffer incoming PCM data
    if (length > 0) {
        // Send to ring buffer (will block briefly if full, giving I2S time to drain)
        if (xRingbufferSend(ringBuf, payload, length, pdMS_TO_TICKS(200))) {
            bytesBuffered += length;
        } else {
            Serial.println("  WARNING: Ring buffer full, dropping chunk");
        }

        // Start playback once we've prebuffered enough
        if (!playbackStarted && bytesBuffered >= PREBUFFER_BYTES) {
            Serial.printf("  Prebuffered %d bytes, starting playback\n", bytesBuffered);
            playbackStarted = true;
        }
    }
}

// ===== Handle text (JSON) messages =====
void handleText(uint8_t* payload, size_t length) {
    String msg = String((char*)payload);

    if (msg.indexOf("\"eof\"") >= 0) {
        Serial.printf("  EOF received, %d bytes buffered\n", bytesBuffered);
        eofReceived = true;

        // If we never hit the prebuffer threshold (very short file), start now
        if (!playbackStarted && bytesBuffered > 0) {
            playbackStarted = true;
        }
    }
}

// ===== WebSocket Event Handler =====
void webSocketEvent(WStype_t type, uint8_t* payload, size_t length) {
    switch (type) {
        case WStype_DISCONNECTED:
            wsConnected = false;
            headerReceived = false;
            playbackStarted = false;
            Serial.println("  [WS] Disconnected");
            break;

        case WStype_CONNECTED:
            wsConnected = true;
            Serial.printf("  [WS] Connected to %s:%d%s\n", WS_HOST, WS_PORT, WS_PATH);
            webSocket.sendTXT("{\"type\":\"hello\",\"device\":\"esp32-speaker\"}");
            break;

        case WStype_TEXT:
            handleText(payload, length);
            break;

        case WStype_BIN:
            handleBinary(payload, length);
            break;

        case WStype_PING:
        case WStype_PONG:
            break;

        case WStype_ERROR:
            Serial.println("  [WS] Error");
            break;
    }
}

// ===== WiFi =====
void connectWiFi() {
    Serial.printf("  Connecting to %s", WIFI_SSID);
    WiFi.mode(WIFI_STA);
    WiFi.begin(WIFI_SSID, WIFI_PASS);

    int attempts = 0;
    while (WiFi.status() != WL_CONNECTED && attempts < 30) {
        delay(500);
        Serial.print(".");
        attempts++;
    }

    if (WiFi.status() == WL_CONNECTED) {
        Serial.printf("\n  Connected! IP: %s\n", WiFi.localIP().toString().c_str());
    } else {
        Serial.println("\n  WiFi connection failed!");
    }
}

// ===== Setup =====
void setup() {
    Serial.begin(115200);
    delay(1000);

    Serial.println("\n=== Ed Speaker Bridge ===");
    Serial.printf("  Free heap: %d bytes\n", ESP.getFreeHeap());
    Serial.println();

    // Create ring buffer
    ringBuf = xRingbufferCreate(RING_BUF_SIZE, RINGBUF_TYPE_BYTEBUF);
    if (!ringBuf) {
        Serial.println("  ERROR: Failed to create ring buffer!");
        return;
    }
    Serial.printf("  Ring buffer: %d bytes\n", RING_BUF_SIZE);

    // Start I2S playback task on core 0 (WiFi/WebSocket runs on core 1)
    xTaskCreatePinnedToCore(i2sTask, "i2s_play", 4096, NULL, 5, &i2sTaskHandle, 0);

    connectWiFi();

    webSocket.begin(WS_HOST, WS_PORT, WS_PATH);
    webSocket.onEvent(webSocketEvent);
    webSocket.setReconnectInterval(3000);
    webSocket.enableHeartbeat(15000, 3000, 2);

    Serial.printf("  WebSocket connecting to ws://%s:%d%s\n", WS_HOST, WS_PORT, WS_PATH);
    Serial.println("  Waiting for audio...\n");
}

// ===== Loop (core 1 — handles WiFi + WebSocket) =====
void loop() {
    webSocket.loop();

    if (Serial.available()) {
        char cmd = Serial.read();
        switch (cmd) {
            case 's':
                Serial.printf("  WS: %s | Playing: %s | Buf: %d | Played: %d/%d\n",
                    wsConnected ? "yes" : "no",
                    playbackStarted ? "yes" : "no",
                    bytesBuffered - bytesPlayed,
                    bytesPlayed, expectedBytes);
                break;
            case 'r':
                Serial.println("  Reconnecting...");
                webSocket.disconnect();
                webSocket.begin(WS_HOST, WS_PORT, WS_PATH);
                break;
        }
    }
}
