/**
 * ESP32 Audio Bridge — Streams microphone audio to backend via WebSocket
 * 
 * Features:
 *   - Continuous audio streaming over WiFi WebSocket
 *   - Voice Activity Detection (VAD) to only send when speaking
 *   - Configurable sample rate and chunk size
 *   - Auto-reconnect on connection loss
 * 
 * Hardware: INMP441 I2S MEMS Microphone
 */

#include <Arduino.h>
#include <driver/i2s.h>
#include <WiFi.h>
#include <WebSocketsClient.h>

// ===== WiFi Configuration =====
const char* WIFI_SSID     = "jasoniphone";
const char* WIFI_PASSWORD = "12345678";

// ===== Backend WebSocket =====
// The AudioBridge.py runs on your laptop and connects to the backend
const char* WS_HOST = "172.20.10.12";  // Your laptop's IP on the hotspot
const uint16_t WS_PORT = 8081;        // AudioBridge WebSocket port
const char* WS_PATH = "/audio";

// ===== INMP441 Pins (ESP32-WROOM-32) =====
#define I2S_WS   25   // Word Select (LRCLK)
#define I2S_SCK  26   // Serial Clock (BCLK)
#define I2S_SD   33   // Serial Data (DOUT)

// ===== I2S Configuration =====
#define I2S_PORT       I2S_NUM_0
#define SAMPLE_RATE    16000
#define SAMPLE_BITS    I2S_BITS_PER_SAMPLE_32BIT
#define DMA_BUF_COUNT  8
#define DMA_BUF_LEN    512

// ===== Audio Streaming Config =====
#define CHUNK_SAMPLES  512           // Samples per WebSocket message (32ms at 16kHz)
#define VAD_THRESHOLD  500           // RMS threshold for voice activity
#define VAD_HOLDOFF_MS 300           // Keep streaming for this long after voice stops
#define RECONNECT_INTERVAL_MS 3000   // WebSocket reconnect interval

// Buffers
int32_t i2sBuffer[CHUNK_SAMPLES * 2];  // Stereo I2S read buffer
int16_t audioBuffer[CHUNK_SAMPLES];     // Mono 16-bit output buffer

// State
WebSocketsClient webSocket;
bool wsConnected = false;
unsigned long lastVoiceTime = 0;
float dcOffset = 0.0f;
bool dcInitialized = false;

// Stats
unsigned long totalBytesSent = 0;
unsigned long lastStatsTime = 0;

// ===== I2S Initialization =====
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
    
    Serial.println("  I2S initialized");
}

// ===== WiFi Initialization =====
void wifi_init() {
    Serial.printf("  Connecting to %s", WIFI_SSID);
    WiFi.mode(WIFI_STA);
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
    
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

// ===== WebSocket Event Handler =====
void webSocketEvent(WStype_t type, uint8_t* payload, size_t length) {
    switch (type) {
        case WStype_DISCONNECTED:
            wsConnected = false;
            Serial.println("  [WS] Disconnected");
            break;
            
        case WStype_CONNECTED:
            wsConnected = true;
            Serial.printf("  [WS] Connected to %s:%d%s\n", WS_HOST, WS_PORT, WS_PATH);
            // Send hello message
            webSocket.sendTXT("{\"type\":\"hello\",\"device\":\"esp32\",\"sample_rate\":16000}");
            break;
            
        case WStype_TEXT:
            // Handle commands from backend (e.g., start/stop streaming)
            Serial.printf("  [WS] Received: %s\n", payload);
            break;
            
        case WStype_BIN:
            // Binary data from backend (e.g., TTS audio to play)
            Serial.printf("  [WS] Binary: %d bytes\n", length);
            break;
            
        case WStype_ERROR:
            Serial.println("  [WS] Error");
            break;
            
        case WStype_PING:
        case WStype_PONG:
            break;
    }
}

// ===== WebSocket Initialization =====
void websocket_init() {
    webSocket.begin(WS_HOST, WS_PORT, WS_PATH);
    webSocket.onEvent(webSocketEvent);
    webSocket.setReconnectInterval(RECONNECT_INTERVAL_MS);
    webSocket.enableHeartbeat(15000, 3000, 2);  // Ping every 15s, timeout 3s, 2 retries
    Serial.printf("  WebSocket connecting to ws://%s:%d%s\n", WS_HOST, WS_PORT, WS_PATH);
}

// ===== Read and Process Audio =====
// Returns RMS level for VAD
uint16_t readAudioChunk() {
    size_t bytesRead = 0;
    
    esp_err_t err = i2s_read(
        I2S_PORT,
        i2sBuffer,
        CHUNK_SAMPLES * 2 * sizeof(int32_t),  // Stereo
        &bytesRead,
        portMAX_DELAY
    );
    
    if (err != ESP_OK) {
        return 0;
    }
    
    int samplesRead = bytesRead / (2 * sizeof(int32_t));
    uint64_t sumSquares = 0;
    
    for (int i = 0; i < samplesRead; i++) {
        // Extract left channel and shift to 16-bit range
        int32_t raw = i2sBuffer[i * 2];
        int32_t shifted = raw >> 12;
        
        // DC offset removal with slow-moving average
        if (!dcInitialized) {
            dcOffset = (float)shifted;
            dcInitialized = true;
        } else {
            dcOffset = dcOffset * 0.999f + (float)shifted * 0.001f;
        }
        
        int32_t cleaned = shifted - (int32_t)dcOffset;
        
        // Clamp to 16-bit range
        if (cleaned > 32767) cleaned = 32767;
        if (cleaned < -32768) cleaned = -32768;
        
        audioBuffer[i] = (int16_t)cleaned;
        sumSquares += (int64_t)cleaned * cleaned;
    }
    
    // Calculate RMS
    return (uint16_t)sqrt((double)sumSquares / samplesRead);
}

// ===== Send Audio Over WebSocket =====
void sendAudioChunk() {
    if (!wsConnected) return;
    
    // Send as binary (raw 16-bit PCM)
    webSocket.sendBIN((uint8_t*)audioBuffer, CHUNK_SAMPLES * sizeof(int16_t));
    totalBytesSent += CHUNK_SAMPLES * sizeof(int16_t);
}

// ===== Print Stats =====
void printStats() {
    unsigned long now = millis();
    if (now - lastStatsTime >= 5000) {
        float kbps = (totalBytesSent * 8.0f) / ((now - lastStatsTime) / 1000.0f) / 1000.0f;
        Serial.printf("  [Stats] %.1f kbps, heap: %d\n", kbps, ESP.getFreeHeap());
        totalBytesSent = 0;
        lastStatsTime = now;
    }
}

// ===== Setup =====
void setup() {
    Serial.begin(115200);
    delay(2000);
    
    Serial.println("\n=== Ed Audio Bridge ===");
    Serial.printf("  Free heap: %d bytes\n", ESP.getFreeHeap());
    Serial.printf("  Sample rate: %d Hz\n", SAMPLE_RATE);
    Serial.printf("  Chunk size: %d samples (%.1f ms)\n", CHUNK_SAMPLES, CHUNK_SAMPLES * 1000.0f / SAMPLE_RATE);
    Serial.println();
    
    i2s_init();
    wifi_init();
    websocket_init();
    
    lastStatsTime = millis();
    Serial.println("\n  Streaming audio...\n");
}

// ===== Main Loop =====
void loop() {
    // Handle WebSocket events
    webSocket.loop();
    
    // Read audio chunk
    uint16_t rms = readAudioChunk();
    
    // Voice Activity Detection
    bool voiceActive = rms > VAD_THRESHOLD;
    unsigned long now = millis();
    
    if (voiceActive) {
        lastVoiceTime = now;
    }
    
    // Stream if voice detected or within holdoff period
    bool shouldStream = (now - lastVoiceTime) < VAD_HOLDOFF_MS;
    
    if (shouldStream && wsConnected) {
        sendAudioChunk();
    }
    
    // Print periodic stats
    printStats();
    
    // Handle serial commands
    if (Serial.available()) {
        char cmd = Serial.read();
        switch (cmd) {
            case 's':  // Status
                Serial.printf("  Connected: %s, RMS: %d, Voice: %s\n", 
                    wsConnected ? "yes" : "no", rms, voiceActive ? "yes" : "no");
                break;
            case 'r':  // Reconnect
                Serial.println("  Reconnecting WebSocket...");
                webSocket.disconnect();
                websocket_init();
                break;
        }
    }
}
