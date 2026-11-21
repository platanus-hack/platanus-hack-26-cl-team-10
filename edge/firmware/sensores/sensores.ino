// Lee sensores y emite una línea JSON por segundo por serial (115200).
// Sensor no conectado -> su campo sale null.
// El servo MG996R (180°) parte encendido y el pulsador lo apaga y prende: encendido barre de lado a lado sin parar,
// apagado se detiene donde está. Su estado sale en el campo "motor".
#include <DHT.h>

#define DHT_PIN   4
#define DHT_TYPE  DHT22   // cambiar a DHT11 si es el azul
#define TRIG_PIN  5
#define ECHO_PIN  18      // HC-SR04 entrega 5V en ECHO: usar divisor (1k/2k) hacia el ESP32
#define SERVO_PIN 26      // señal (cable naranjo) del MG996R; rojo y café van a la fuente externa de 5-6 V
#define SERVO_MIN_US 800  // extremos del barrido; si zumba al llegar a un extremo, achicar el rango
#define SERVO_MAX_US 2200
#define PASO_US      50   // cuánto avanza cada 20 ms: un barrido de ida tarda ~0,6 s (el MG996R no da mucho más)
#define BTN_PIN   27      // pulsador entre el pin y GND (pull-up interno)

DHT dht(DHT_PIN, DHT_TYPE);
bool motor = true, btnAntes = HIGH;  // parte encendido: la demo empieza con la cinta andando
int pos = 1500, paso = PASO_US;
unsigned long ultimoEnvio = 0;

float distanciaCm() {
  digitalWrite(TRIG_PIN, LOW);  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH); delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);
  unsigned long us = pulseIn(ECHO_PIN, HIGH, 30000);  // ~5 m máx
  return us ? us / 58.0 : NAN;
}

void servoUs(int us) { ledcWrite(SERVO_PIN, us * 16384L / 20000); }  // µs -> duty de 14 bits a 50 Hz

void campo(const char* k, float v) {
  Serial.printf(",\"%s\":", k);
  if (isnan(v)) Serial.print("null"); else Serial.print(v, 1);
}

void setup() {
  Serial.begin(115200);
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  ledcAttach(SERVO_PIN, 50, 14);  // servo: pulso cada 20 ms
  pinMode(BTN_PIN, INPUT_PULLUP);
  dht.begin();
}

void loop() {
  // shortcut: el botón no se mira durante la lectura de sensores (~40 ms por segundo);
  // un toque más corto que eso se puede perder. Pasar a interrupción si molesta.
  bool btn = digitalRead(BTN_PIN);
  if (btnAntes == HIGH && btn == LOW) {
    motor = !motor;
    if (!motor) ledcWrite(SERVO_PIN, 0);  // sin pulsos el servo se detiene y queda suelto
  }
  btnAntes = btn;
  if (motor) {
    pos += paso;
    if (pos >= SERVO_MAX_US || pos <= SERVO_MIN_US) paso = -paso;
    servoUs(pos);
  }
  delay(20);  // antirrebote

  if (millis() - ultimoEnvio < 1000) return;
  ultimoEnvio = millis();
  Serial.printf("{\"ms\":%lu", millis());
  campo("temp_c", dht.readTemperature());
  campo("hum_pct", dht.readHumidity());
  campo("dist_cm", distanciaCm());
  Serial.printf(",\"motor\":%d}\n", motor);
}
