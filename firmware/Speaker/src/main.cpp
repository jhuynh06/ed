#include <Arduino.h>
#include <WiFi.h>
#include <driver/i2s.h>

// ===== WiFi Configuration =====
const char* WIFI_SSID = "jasoniphone";
const char* WIFI_PASS = "12345678";

// ===== Server Configuration =====
const char* SERVER_IP   = "172.20.10.12";  // Your PC's IP (printed by SpeakerServer.py)
const uint16_t SERVER_PORT = 8081;

// ===== I2S Pin Configuration (MAX98357A) =====
#define I2S_BCLK_PIN   27
#define I2S_LRC_PIN    26
#define I2S_DOUT_PIN   25

void setupI2S(uint32_t sampleRate, uint16_t bitsPerSample, uint16_t numChannels) {
    i2s_bits_per_sample_t bits;
    if (bitsPerSample == 16) {
        bits = I2S_BITS_PER_SAMPLE_16BIT;
    } else if (bitsPerSample == 32) {
        bits = I2S_BITS_PER_SAMPLE_32BIT;
    } else {
        bits = I2S_BITS_PER_SAMPLE_8BIT;
    }

    i2s_channel_fmt_t channelFmt = (numChannels == 2)
        ? I2S_CHANNEL_FMT_RIGHT_LEFT
        : I2S_CHANNEL_FMT_ONLY_LEFT;

    i2s_config_t i2s_config = {
        .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_TX),
        .sample_rate = sampleRate,
        .bits_per_sample = bits,
        .channel_format = channelFmt,
        .communication_format = I2S_COMM_FORMAT_STAND_I2S,
        .intr_alloc_flags = ESP_INTR_FLAG_LEVEL1,
        .dma_buf_count = 8,
        .dma_buf_len = 1024,
        .use_apll = false,
        .tx_desc_auto_clear = true
    };

    i2s_pin_config_t pin_config = {
        .bck_io_num = I2S_BCLK_PIN,
        .ws_io_num = I2S_LRC_PIN,
        .data_out_num = I2S_DOUT_PIN,
        .data_in_num = I2S_PIN_NO_CHANGE
    };

    i2s_driver_install(I2S_NUM_0, &i2s_config, 0, NULL);
    i2s_set_pin(I2S_NUM_0, &pin_config);
    i2s_zero_dma_buffer(I2S_NUM_0);
}

void connectWiFi() {
    Serial.printf("Connecting to %s", WIFI_SSID);
    WiFi.begin(WIFI_SSID, WIFI_PASS);

    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }

    Serial.printf("\nConnected! IP: %s\n", WiFi.localIP().toString().c_str());
}

void streamAndPlay() {
    Serial.printf("Connecting to server %s:%d...\n", SERVER_IP, SERVER_PORT);

    WiFiClient client;
    if (!client.connect(SERVER_IP, SERVER_PORT)) {
        Serial.println("Connection failed!");
        return;
    }

    Serial.println("Connected to server, receiving audio params...");

    // Wait for header data (16 bytes: sampleRate, bitsPerSample, numChannels, dataSize)
    unsigned long timeout = millis() + 5000;
    while (client.available() < 16 && millis() < timeout) {
        delay(10);
    }

    if (client.available() < 16) {
        Serial.println("Timeout waiting for header");
        client.stop();
        return;
    }

    // Read audio parameters (12 bytes)
    uint32_t sampleRate, bitsPerSample, numChannels;
    client.read((uint8_t*)&sampleRate, 4);
    client.read((uint8_t*)&bitsPerSample, 4);
    client.read((uint8_t*)&numChannels, 4);

    // Read data size (4 bytes)
    uint32_t dataSize;
    client.read((uint8_t*)&dataSize, 4);

    Serial.printf("Audio: %d Hz, %d-bit, %d ch, %d bytes\n",
                  sampleRate, bitsPerSample, numChannels, dataSize);

    // Setup I2S with received parameters
    setupI2S(sampleRate, bitsPerSample, numChannels);

    // Stream audio data to I2S
    const size_t bufSize = 1024;
    uint8_t buf[bufSize];
    uint32_t bytesReceived = 0;

    Serial.println("Playing...");

    while (bytesReceived < dataSize) {
        // Wait for data with timeout
        unsigned long waitStart = millis();
        while (client.available() == 0 && client.connected() && (millis() - waitStart < 3000)) {
            delay(1);
        }

        if (!client.connected() && client.available() == 0) {
            break;
        }

        size_t toRead = min(bufSize, (size_t)(dataSize - bytesReceived));
        size_t bytesRead = client.read(buf, toRead);

        if (bytesRead > 0) {
            size_t bytesWritten;
            i2s_write(I2S_NUM_0, buf, bytesRead, &bytesWritten, portMAX_DELAY);
            bytesReceived += bytesRead;
        }
    }

    // Let DMA buffer drain
    delay(200);
    i2s_zero_dma_buffer(I2S_NUM_0);
    i2s_driver_uninstall(I2S_NUM_0);

    client.stop();
    Serial.printf("Playback complete (%d bytes)\n", bytesReceived);
}

void setup() {
    Serial.begin(115200);
    delay(1000);

    connectWiFi();
    streamAndPlay();
}

void loop() {
    // Reconnect and play again on serial command
    if (Serial.available()) {
        char c = Serial.read();
        if (c == 'p' || c == 'P') {
            Serial.println("\nReplaying...");
            streamAndPlay();
        }
    }
    delay(100);
}
