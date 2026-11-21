# Simulación de la capa 2

> Generado por `scripts/simular_capa2.py --semillas 40` el 2026-11-21. Señales **sintéticas**:
> descartan detectores que fallan en patrones conocidos; no calibran umbrales. Se regenera, no se edita a mano.

Cada corrida tiene 800 lecturas. Los detectores con línea base fija la toman al principio, de al menos
dos ciclos de trabajo, y la falla empieza entre 60 y 260 lecturas después. **Detecta** es la fracción de corridas en que la alarma se
encendió durante la falla; **retardo**, la mediana de lecturas entre el inicio de la falla y la alarma;
**cubre**, qué fracción de la falla la alarma estuvo encendida. Una falsa alarma es una alarma que se
enciende fuera de la falla.

## Detectores

- **MAD con historia móvil (antes)**: como corría hasta el 2026-11-21: compara contra las últimas 300 lecturas, falla incluida, sin piso de dispersión.
- **MAD que no aprende de la falla (hoy)**: scoring.capa2 tal cual corre en servicios.py: la historia solo suma lecturas normales y la dispersión tiene el piso de ruido de scoring.py (2 % de la mediana, calibrado con sensores reales).
- **MAD con línea base fija**: la misma fórmula, pero la línea base se toma al calibrar y no se mueve.
- **EWMA (λ 0,2 · L 3)**: media móvil exponencial contra su límite de control; suaviza el ruido y ve cambios chicos sostenidos.
- **CUSUM (k 0,5 · h 5)**: suma acumulada de desvíos; el clásico para detectar un corrimiento sostenido de la media.
- **CUSUM sobre el residuo del ciclo**: el mismo CUSUM, pero contra lo esperado en ese momento del ciclo de trabajo. Necesita saber en qué parte del ciclo va la máquina: en terreno, otra señal como la corriente o la carga.
- **Umbral fijo**: un límite tipo fabricante: media nominal más 6 desvíos, sin aprender nada.
- **Sensor pegado**: aparte de los demás: 10 lecturas idénticas seguidas son una falla del sensor.

## Resultados

### Minería · vibración del rodillo

Media 2 mm/s, ruido 0.12, sin ciclo. Línea base: 60 lecturas.

| Detector | Falsas alarmas / 1.000 lecturas | Pico | Escalón: detecta · retardo · cubre | Deriva: detecta · retardo | Alarma por sensor pegado |
|---|---|---|---|---|---|
| MAD con historia móvil (antes) | 7.8 | 100 % | 100 % · 0 · 47 % | 100 % · 25 | 0 % |
| MAD que no aprende de la falla (hoy) | 0.9 | 100 % | 100 % · 0 · 100 % | 100 % · 25 | 0 % |
| MAD con línea base fija | 2.2 | 100 % | 100 % · 0 · 100 % | 100 % · 24 | 0 % |
| EWMA (λ 0,2 · L 3) | 9.0 | 95 % | 100 % · 0 · 100 % | 100 % · 12 | 28 % |
| CUSUM (k 0,5 · h 5) | 8.2 | 100 % | 100 % · 0 · 100 % | 100 % · 12 | 60 % |
| CUSUM sobre el residuo del ciclo | 7.1 | 100 % | 100 % · 0 · 100 % | 100 % · 10 | 62 % |
| Umbral fijo | 0.0 | 100 % | 100 % · 0 · 98 % | 100 % · 48 | 0 % |

El detector de sensor pegado encontró el pegado en 100 % de las corridas, con 0.0 falsas alarmas por 1.000 lecturas.

### Eléctrica · temperatura de la conexión

Media 45 °C, ruido 1.5, con un ciclo de ±4.5 °C cada 120 lecturas. Línea base: 240 lecturas.

| Detector | Falsas alarmas / 1.000 lecturas | Pico | Escalón: detecta · retardo · cubre | Deriva: detecta · retardo | Alarma por sensor pegado |
|---|---|---|---|---|---|
| MAD con historia móvil (antes) | 0.0 | 20 % | 62 % · 1 · 4 % | 32 % · 73 | 0 % |
| MAD que no aprende de la falla (hoy) | 0.0 | 20 % | 62 % · 1 · 6 % | 32 % · 73 | 0 % |
| MAD con línea base fija | 0.0 | 15 % | 100 % · 14 · 22 % | 52 % · 62 | 0 % |
| EWMA (λ 0,2 · L 3) | 29.6 | 35 % | 100 % · 2 · 99 % | 100 % · 26 | 20 % |
| CUSUM (k 0,5 · h 5) | 14.1 | 80 % | 100 % · 0 · 100 % | 100 % · 0 | 80 % |
| CUSUM sobre el residuo del ciclo | 8.5 | 100 % | 100 % · 0 · 100 % | 100 % · 10 | 98 % |
| Umbral fijo | 0.2 | 70 % | 100 % · 0 · 77 % | 100 % · 46 | 0 % |

El detector de sensor pegado encontró el pegado en 100 % de las corridas, con 0.0 falsas alarmas por 1.000 lecturas.

### Construcción · temperatura del aceite hidráulico

Media 60 °C, ruido 2, con un ciclo de ±4 °C cada 40 lecturas. Línea base: 80 lecturas.

| Detector | Falsas alarmas / 1.000 lecturas | Pico | Escalón: detecta · retardo · cubre | Deriva: detecta · retardo | Alarma por sensor pegado |
|---|---|---|---|---|---|
| MAD con historia móvil (antes) | 0.0 | 68 % | 100 % · 0 · 13 % | 92 % · 55 | 0 % |
| MAD que no aprende de la falla (hoy) | 0.0 | 68 % | 100 % · 0 · 30 % | 92 % · 55 | 0 % |
| MAD con línea base fija | 0.0 | 75 % | 100 % · 0 · 72 % | 100 % · 48 | 0 % |
| EWMA (λ 0,2 · L 3) | 25.9 | 55 % | 100 % · 1 · 100 % | 100 % · 12 | 38 % |
| CUSUM (k 0,5 · h 5) | 26.6 | 60 % | 100 % · 1 · 100 % | 100 % · 3 | 78 % |
| CUSUM sobre el residuo del ciclo | 11.0 | 100 % | 100 % · 0 · 100 % | 100 % · 12 | 100 % |
| Umbral fijo | 0.0 | 92 % | 100 % · 0 · 86 % | 100 % · 42 | 0 % |

El detector de sensor pegado encontró el pegado en 100 % de las corridas, con 0.0 falsas alarmas por 1.000 lecturas.
