#include <Arduino.h>
#include <driver/i2s.h>
#include <WiFi.h>
#include <HTTPClient.h>

// ===== WiFi — your phone hotspot =====
const char* WIFI_SSID     = "jasoniphone";
const char* WIFI_PASSWORD = "12345678";

// ===== Server — your laptop's IP on the hotspot =====
// Run the Python server first, it prints the IP to use
String serverUrl = "http://172.20.10.7:8080/upload";

// ===== INMP441 Pins (WROOM-32) =====
#define I2S_WS   25
#define I2S_SCK  26
#define I2S_SD   33

// ===== I2S Config =====
#define I2S_PORT       I2S_NUM_0
#define SAMPLE_RATE    16000
#define SAMPLE_BITS    I2S_BITS_PER_SAMPLE_32BIT
#define DMA_BUF_COUNT  8
#define DMA_BUF_LEN    1024

// ===== Recording Config =====
#define RECORD_SECONDS   3
#define NUM_SAMPLES      (SAMPLE_RATE * RECORD_SECONDS)
#define WAV_DATA_SIZE    (NUM_SAMPLES * sizeof(int16_t))

// Small chunk buffers only (~3KB)
#define CHUNK_FRAMES     256
int32_t chunkBuffer[CHUNK_FRAMES * 2];
int16_t convertBuffer[CHUNK_FRAMES];

// ===== WAV Header =====
void buildWavHeader(uint8_t* h, uint32_t dataSize) {
    uint32_t fileSize   = dataSize + 36;
    uint32_t sr         = SAMPLE_RATE;
    uint16_t ch         = 1;
    uint16_t bps        = 16;
    uint32_t byteRate   = sr * ch * bps / 8;
    uint16_t blockAlign = ch * bps / 8;
    uint16_t pcm        = 1;
    uint32_t fmtSize    = 16;

    memcpy(h,    "RIFF", 4);  memcpy(h+4,  &fileSize, 4);
    memcpy(h+8,  "WAVE", 4);  memcpy(h+12, "fmt ", 4);
    memcpy(h+16, &fmtSize, 4); memcpy(h+20, &pcm, 2);
    memcpy(h+22, &ch, 2);     memcpy(h+24, &sr, 4);
    memcpy(h+28, &byteRate,4); memcpy(h+32, &blockAlign, 2);
    memcpy(h+34, &bps, 2);    memcpy(h+36, "data", 4);
    memcpy(h+40, &dataSize,4);
}

// ===== I2S Init =====
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

    size_t discard;
    int32_t trash[256];
    for (int i = 0; i < 10; i++) {
        i2s_read(I2S_PORT, trash, sizeof(trash), &discard, portMAX_DELAY);
    }
}

// ===== WiFi Init =====
void wifi_init() {
    Serial.printf("Connecting to %s", WIFI_SSID);
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }
    Serial.printf("\nConnected! IP: %s\n", WiFi.localIP().toString().c_str());
}

// ===== Record and send =====
void recordAndSend() {
    Serial.printf("Recording %d seconds...\n", RECORD_SECONDS);

    // Build complete WAV in a temporary buffer
    // Use chunked allocation: record to small buffer, build WAV, send
    // We'll accumulate into a large buffer allocated just for this
    uint8_t* wavFile = (uint8_t*)malloc(44 + WAV_DATA_SIZE);
    if (!wavFile) {
        // If can't fit full recording, try half
        Serial.println("ERROR: Can't allocate WAV buffer");
        Serial.printf("  Need %d, free %d, largest %d\n",
            44 + WAV_DATA_SIZE, ESP.getFreeHeap(), ESP.getMaxAllocHeap());
        return;
    }

    // Write WAV header
    buildWavHeader(wavFile, WAV_DATA_SIZE);

    // Record audio into buffer after header
    int16_t* audioPtr = (int16_t*)(wavFile + 44);
    int samplesWritten = 0;
    float dcOffset = 0.0f;
    bool dcInit = false;

    while (samplesWritten < NUM_SAMPLES) {
        size_t bytesRead = 0;
        int framesToRead = min(CHUNK_FRAMES, NUM_SAMPLES - samplesWritten);

        esp_err_t err = i2s_read(
            I2S_PORT,
            chunkBuffer,
            framesToRead * 2 * sizeof(int32_t),
            &bytesRead,
            portMAX_DELAY
        );
        if (err != ESP_OK) { free(wavFile); return; }

        int framesRead = bytesRead / (2 * sizeof(int32_t));

        for (int i = 0; i < framesRead; i++) {
            int32_t raw = chunkBuffer[i * 2];  // Left channel
            int32_t shifted = raw >> 12;

            if (!dcInit) {
                dcOffset = (float)shifted;
                dcInit = true;
            } else {
                dcOffset = dcOffset * 0.999f + (float)shifted * 0.001f;
            }

            int32_t cleaned = shifted - (int32_t)dcOffset;
            if (cleaned > 32767) cleaned = 32767;
            if (cleaned < -32768) cleaned = -32768;
            audioPtr[samplesWritten + i] = (int16_t)cleaned;
        }
        samplesWritten += framesRead;
    }

    Serial.printf("Recorded %d samples. Sending to server...\n", samplesWritten);

    // Send over HTTP
    HTTPClient http;
    http.begin(serverUrl);
    http.addHeader("Content-Type", "audio/wav");
    http.setTimeout(30000);

    int httpCode = http.POST(wavFile, 44 + WAV_DATA_SIZE);

    if (httpCode > 0) {
        Serial.printf("Server responded: %d - %s\n", httpCode, http.getString().c_str());
    } else {
        Serial.printf("HTTP error: %s\n", http.errorToString(httpCode).c_str());
    }

    http.end();
    free(wavFile);
}

void setup() {
    Serial.begin(115200);
    delay(2000);

    Serial.println("\n=== INMP441 WiFi Recorder ===");
    Serial.printf("Free heap: %d, largest block: %d\n", ESP.getFreeHeap(), ESP.getMaxAllocHeap());

    i2s_init();
    wifi_init();

    Serial.println("\nREADY — press button or send 'r' to record");
}

void loop() {
    // Record on serial command or every loop with a prompt
    if (Serial.available() && Serial.read() == 'r') {
        recordAndSend();
        Serial.println("\nREADY — send 'r' to record again");
    }
    delay(10);
}