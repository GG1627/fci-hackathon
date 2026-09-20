#include <Arduino.h>
#include <Adafruit_TMP117.h>
#include <Wire.h>

constexpr uint8_t SDA_PIN = 21;
constexpr uint8_t SCL_PIN = 22;
constexpr uint8_t REED_PIN = 27;

Adafruit_TMP117 tmp117;

void setup() {
  Serial.begin(115200);
  pinMode(REED_PIN, INPUT_PULLUP);

  Wire.begin(SDA_PIN, SCL_PIN);
  if (!tmp117.begin()) {
    while (true) {
      delay(1000);
    }
  }
}

void loop() {
  sensors_event_t temperature;
  tmp117.getEvent(&temperature);

  const float fahrenheit = temperature.temperature * 9.0F / 5.0F + 32.0F;
  const bool doorOpen = digitalRead(REED_PIN) != LOW;

  Serial.printf(
      "{\"device_id\":\"fridge-sensor-01\",\"temperature_f\":%.1f,"
      "\"door_open\":%s}\n",
      fahrenheit, doorOpen ? "true" : "false");
  delay(1000);
}
