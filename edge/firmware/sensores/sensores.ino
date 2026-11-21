// Lee sensores y emite una línea JSON por segundo por serial (115200).
// Sensor no conectado -> su campo sale null.
#include <DHT.h>

#define DHT_PIN   4
#define DHT_TYPE  DHT22   // cambiar a DHT11 si es el azul
#define TRIG_PIN  5
#define ECHO_PIN  18      // HC-SR04 entrega 5V en ECHO: usar divisor (1k/2k) hacia el ESP32

DHT dht(DHT_PIN, DHT_TYPE);

float distanciaCm() {
  digitalWrite(TRIG_PIN, LOW);  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH); delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);
  unsigned long us = pulseIn(ECHO_PIN, HIGH, 30000);  // ~5 m máx
  return us ? us / 58.0 : NAN;
}

void campo(const char* k, float v) {
  Serial.printf(",\"%s\":", k);
  if (isnan(v)) Serial.print("null"); else Serial.print(v, 1);
}

void setup() {
  Serial.begin(115200);
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  dht.begin();
}

void loop() {
  Serial.printf("{\"ms\":%lu", millis());
  campo("temp_c", dht.readTemperature());
  campo("hum_pct", dht.readHumidity());
  campo("dist_cm", distanciaCm());
  Serial.print("}\n");
  delay(1000);
}
