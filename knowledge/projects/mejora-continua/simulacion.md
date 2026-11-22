# Simulación de la mejora continua

> Generado por `scripts/simular_mejora.py` el 2026-11-21, con 2000 repeticiones por fila de Monte Carlo y 100 pautas de punta a punta. **Datos simulados.** Miden si el sistema distingue un patrón del ruido y si se adjudica mejoras que no causó; no miden cuánto se desvía un operario real ni cuánto sirve reescribir una pauta. Se regenera, no se edita a mano.

La pauta es `pauta-polin-demo` (8 pasos, 6 controles críticos). Las OT pasan por `app/servicios.py` real; la conducta simulada queda aparte de la bitácora, así cada propuesta se puede revisar contra lo que de verdad pasó.

## Perfiles

Cada perfil es una causa. Si la pauta la arregla, y con qué efecto, se declara acá antes de correr: la v2 no deja de desviarse porque el operario simulado lo tenga programado.

| Perfil | Causa | Conducta | ¿La arregla la pauta? | Remedio | Efecto en la v2 | Fuente |
|---|---|---|---|---|---|---|
| olvido | lapso de memoria tras una interrupción | `saltar` | sí | agregar la verificación explícita del paso | tasa × 0.3 | THERP, NUREG/CR-1278 tabla 20-7: omisión 0,01 sin casilla de verificación y 0,003 con ella |
| impracticable | la pauta no calza con cómo se hace el trabajo (violación situacional) | `saltar` | sí | reescribir el paso con quien hace la tarea | sin dato publicado | Peres et al. 2020 (33); Mendoza et al. 2024: desviación autodeclarada media 30,8 %. Sin efecto publicado |
| presion | presión de tiempo o del supervisor (violación por optimización) | `saltar` | **no** | ninguno en la pauta: hablar con la supervisión; nunca relajar el control | tasa × 1 | Peres et al. 2020: 7 de 16 se desvían para ahorrar tiempo; HEART: ×11 por falta de tiempo |
| apuro | declara el paso antes de terminarlo | `declarar_sin_hacer` | sí | reescribir cuándo el paso está hecho | sin dato publicado | Tabla de síntomas de la skill optimizar-proceso. Sin efecto publicado |
| equipo | el sensor no ve el paso | `sensor_falla` | **no** | revisar el sensor, no la pauta | tasa × 1 | Peres et al. 2020: equipo que falla, 5 de 16 |
| ruido | deslices sueltos, en cualquier paso | `declarar_sin_hacer` | **no** | ninguno: no es un patrón | tasa × 1 | IndustReal (13): 38 de 762 pasos mal completados, ~5 % |

## 1 · Fidelidad: lo simulado es lo que lee la mejora

| Corrida | Desviaciones simuladas con señal | Señales leídas | Faltan | Sobran |
|---|---|---|---|---|
| olvido en p2, con ruido 5 %, 20 OT | 16 | 16 | 0 | 0 |
| presion en p6, con ruido 5 %, 20 OT | 17 | 17 | 0 | 0 |
| apuro en p4, con ruido 5 %, 20 OT | 16 | 16 | 0 | 0 |
| equipo en p2, con ruido 5 %, 20 OT | 16 | 16 | 0 | 0 |
| impracticable en p7, con ruido 5 %, 20 OT | 16 | 16 | 0 | 0 |

Saltarse un paso deja señal solo si el saltado es un control crítico de sensor seguido de otro paso de sensor (alerta de orden), o si adelantar el siguiente deshace un control ya verificado (control perdido): en `pauta-polin-demo` son p1, p2, p6, p7. Saltarse p3, p4, p5, p8 no deja nada en la bitácora: la simulación lo rechaza en vez de contarlo como no detectado.

Contraste con el pipeline real: 100 pautas simuladas de punta a punta (olvido en p2 al 30 %, ruido 5 %, 20 OT). Pautas con alguna propuesta falsa: regla de 2 OT 87 %, prueba de recurrencia 3,0 %. Compáralo con la fila equivalente del Monte Carlo de abajo (20 OT, base 5 %, patrón 30 %): el ruido real cae en 8 pasos y el patrón deja su señal en p3.

## 2 · El criterio: ¿un patrón o ruido?

Ocho pasos que se desvían al azar con la tasa de ruido y, en las filas con patrón, uno que se desvía más. «Propuesta falsa»: la pauta tiene al menos un paso marcado sin patrón. La regla de hoy es `mejora.MINIMO = 2`; la recurrencia compara cada paso con el resto de su pauta (binomial exacta, Holm, α = 0.05).

| OT | Ruido por paso | Patrón | Regla 2 OT: propuesta falsa | Regla 2 OT: detecta | Recurrencia: propuesta falsa | Recurrencia: detecta |
|---|---|---|---|---|---|---|
| 5 | 2,0 % | — | 2,6 % | — | 0,1 % | — |
| 5 | 2,0 % | 30 % | 2,5 % | 48 % | 0,1 % | 16 % |
| 5 | 5,0 % | — | 16 % | — | 0,8 % | — |
| 5 | 5,0 % | 30 % | 14 % | 46 % | 0,4 % | 14 % |
| 5 | 10 % | — | 49 % | — | 2,3 % | — |
| 5 | 10 % | 30 % | 44 % | 48 % | 1,1 % | 6,8 % |
| 10 | 2,0 % | — | 12 % | — | 0,2 % | — |
| 10 | 2,0 % | 30 % | 10 % | 86 % | 0,1 % | 52 % |
| 10 | 5,0 % | — | 52 % | — | 1,9 % | — |
| 10 | 5,0 % | 30 % | 47 % | 84 % | 0,9 % | 34 % |
| 10 | 10 % | — | 92 % | — | 2,3 % | — |
| 10 | 10 % | 30 % | 89 % | 86 % | 1,7 % | 16 % |
| 20 | 2,0 % | — | 38 % | — | 1,3 % | — |
| 20 | 2,0 % | 30 % | 33 % | 99 % | 1,1 % | 89 % |
| 20 | 5,0 % | — | 91 % | — | 2,9 % | — |
| 20 | 5,0 % | 30 % | 88 % | 99 % | 2,3 % | 70 % |
| 20 | 10 % | — | 100 % | — | 4,7 % | — |
| 20 | 10 % | 30 % | 100 % | 99 % | 2,4 % | 39 % |
| 50 | 2,0 % | — | 92 % | — | 4,1 % | — |
| 50 | 2,0 % | 30 % | 89 % | 100 % | 3,6 % | 100 % |
| 50 | 5,0 % | — | 100 % | — | 4,0 % | — |
| 50 | 5,0 % | 30 % | 100 % | 100 % | 4,5 % | 99 % |
| 50 | 10 % | — | 100 % | — | 4,3 % | — |
| 50 | 10 % | 30 % | 100 % | 100 % | 4,4 % | 84 % |

## 3 · La validación: ¿la v2 mejoró o fue azar?

La v1 y la v2 con OT distintas, un paso al 30 %. Hasta el 2026-11-21 `mejora.py` decía «mejoró» si la tasa de la v2 era menor; ahora pide Fisher exacta (`recurrencia.comprobar_cambio`) y si no alcanza dice «sin_evidencia».

| OT por versión | Efecto real de la v2 | «Mejoró» con la regla anterior | «Mejoró» con Fisher |
|---|---|---|---|
| 5 | ninguno | 36 % | 0,8 % |
| 5 | THERP: tasa × 0,3 | 67 % | 1,8 % |
| 10 | ninguno | 39 % | 2,1 % |
| 10 | THERP: tasa × 0,3 | 83 % | 15 % |
| 20 | ninguno | 42 % | 2,7 % |
| 20 | THERP: tasa × 0,3 | 94 % | 36 % |
| 50 | ninguno | 46 % | 2,8 % |
| 50 | THERP: tasa × 0,3 | 100 % | 80 % |

**Regresión a la media.** Se elige el paso que más se desvió en la v1 (8 pasos al 10 %, 20 OT) y se vuelve a medir sin cambiar nada: la regla anterior dice «mejoró» el 81 % de las veces; Fisher, el 6,2 %. Elegir el peor ya sesga a Fisher un poco sobre su 5 %; por eso la escena 1 deja pasos sin cambiar como control.

## 4 · El aviso en vivo al supervisor

La recomendación le aparece al supervisor apenas un paso se vuelve recurrente: la prueba corre después de cada señal (`servicios._vigilar_patrones`). Mirar después de cada OT es probar muchas veces, y eso infla los avisos falsos; por eso el aviso usa un α más estricto que la columna `recurrencia` de las propuestas.

| α del aviso | Aviso falso en 50 OT de solo ruido | Detecta un paso al 30 % dentro de 50 OT | OT de la detección (mediana) |
|---|---|---|---|
| 0.05 | 16 % | 99 % | 12 |
| 0.01 | 5,2 % | 98 % | 16 |
| 0.005 (el de `mejora.ALFA_AVISO`) | 2,9 % | 97 % | 18 |

De punta a punta, en la pauta del demo (`pauta-polin-estacion`, 7 pasos): el operario se acerca sin apagar el motor en el 30 % de las OT, con ruido al 5 % en el resto. En 100 corridas de 30 OT, la recomendación sobre «Apagar el motor» le llegó al supervisor en la OT 15 (mediana), no llegó en 10, y 2 corridas tuvieron además un aviso sobre otro paso. Si los demás pasos están limpios, el aviso llega a la tercera OT seguida que se salta el mismo paso (`tests/test_simulacion.py`).

## 5 · Las escenas del demo, de punta a punta

50 OT con la v1 y 50 OT nuevas con la v2, ruido 5 % en todos los pasos. Cada tabla son las propuestas de la v1 con su validación contra la v2.

### Escena 1 · Olvido en «Poner tu candado»

La v2 agrega la verificación explícita; su efecto es el de THERP, no uno elegido por nosotros.

| Paso | OT con señal (v1) | Señales | ¿Recurrente? | p | Validación con la v2 | p de la validación | La regla anterior habría dicho |
|---|---|---|---|---|---|---|---|
| p3 · Acercarte a la correa | 20 de 50 | orden 17, conflicto 3 | **sí** | < 0,0001 | mejoro (5 de 50) | 0,0005 | mejoro |
| p1 · Cortar la corriente del motor | 4 de 50 | conflicto 4 | no | 0,2725 | se_repite (5 de 50) | — | se_repite |
| p2 · Poner tu candado | 4 de 50 | conflicto 4 | no | 0,2725 | sin_evidencia (0 de 50) | 0,0587 | mejoro |
| p6 · Alejarte de la correa | 3 de 50 | conflicto 3 | no | 0,5396 | sin_evidencia (1 de 50) | 0,3087 | mejoro |
| p7 · Sacar tu candado | 3 de 50 | conflicto 3 | no | 0,5396 | se_repite (4 de 50) | — | se_repite |
| p8 · Encender el motor | 2 de 50 | conflicto 2 | no | 0,8070 | se_repite (2 de 50) | — | se_repite |
| p5 · Poner el polín nuevo | 2 de 50 | conflicto 2 | no | 0,8070 | se_repite (3 de 50) | — | se_repite |

Sugerencia del paso recurrente: «El paso se hace antes de su turno: revisar si el orden de la pauta calza con cómo se trabaja en el equipo, o si el paso anterior se puede cumplir antes. La palabra del operario y la evidencia no coinciden: revisar cómo está escrito el paso.»

### Escena 2 · Presión de tiempo en «Alejarte de la correa»

El operario saca el candado antes de alejarse. La señal cae en «Poner tu candado», el control que se deshizo. Ningún texto de la pauta ataca la presión: la v2 no cambia la conducta y el sistema no debe adjudicarse una mejora.

| Paso | OT con señal (v1) | Señales | ¿Recurrente? | p | Validación con la v2 | p de la validación | La regla anterior habría dicho |
|---|---|---|---|---|---|---|---|
| p2 · Poner tu candado | 21 de 50 | control 17, conflicto 6 | **sí** | < 0,0001 | sin_evidencia (13 de 50) | 0,0695 | mejoro |
| p3 · Acercarte a la correa | 5 de 50 | conflicto 5 | no | 0,1014 | sin_evidencia (3 de 50) | 0,3575 | mejoro |
| p1 · Cortar la corriente del motor | 4 de 50 | conflicto 4 | no | 0,2725 | se_repite (5 de 50) | — | se_repite |
| p6 · Alejarte de la correa | 3 de 50 | conflicto 3 | no | 0,5396 | sin_evidencia (1 de 50) | 0,3087 | mejoro |
| p7 · Sacar tu candado | 2 de 50 | conflicto 2 | no | 0,8070 | se_repite (3 de 50) | — | se_repite |
| p8 · Encender el motor | 2 de 50 | conflicto 2 | no | 0,8070 | se_repite (2 de 50) | — | se_repite |
| p5 · Poner el polín nuevo | 2 de 50 | conflicto 2 | no | 0,8070 | se_repite (3 de 50) | — | se_repite |

Sugerencia del paso recurrente: «Un control se deshizo antes de tiempo: revisar si la pauta deja claro hasta cuándo se mantiene. La palabra del operario y la evidencia no coinciden: revisar cómo está escrito el paso. Es un control crítico: que se desvíe seguido no lo vuelve prescindible.»

### Escena 3 · Solo ruido

Nadie se desvía con patrón. Lo correcto es no proponer nada.

| Paso | OT con señal (v1) | Señales | ¿Recurrente? | p | Validación con la v2 | p de la validación | La regla anterior habría dicho |
|---|---|---|---|---|---|---|---|
| p4 · Sacar el polín malo | 5 de 50 | conflicto 5 | no | 0,0927 | sin_evidencia (1 de 50) | 0,1022 | mejoro |
| p5 · Poner el polín nuevo | 4 de 50 | conflicto 4 | no | 0,2520 | sin_evidencia (1 de 50) | 0,1811 | mejoro |
| p2 · Poner tu candado | 3 de 50 | conflicto 3 | no | 0,5109 | se_repite (4 de 50) | — | se_repite |
| p3 · Acercarte a la correa | 3 de 50 | conflicto 3 | no | 0,5109 | sin_evidencia (2 de 50) | 0,5000 | mejoro |
| p6 · Alejarte de la correa | 2 de 50 | conflicto 2 | no | 0,7847 | se_repite (4 de 50) | — | se_repite |
| p8 · Encender el motor | 2 de 50 | conflicto 2 | no | 0,7847 | sin_evidencia (1 de 50) | 0,5000 | mejoro |

### Escena 4 · El sensor del candado falla

La propuesta tiene que mandar a revisar el sensor, no la pauta.

| Paso | OT con señal (v1) | Señales | ¿Recurrente? | p | Validación con la v2 | p de la validación | La regla anterior habría dicho |
|---|---|---|---|---|---|---|---|
| p2 · Poner tu candado | 21 de 50 | conflicto 21, persona 17 | **sí** | < 0,0001 | sin_evidencia (13 de 50) | 0,0695 | mejoro |
| p3 · Acercarte a la correa | 5 de 50 | conflicto 5 | no | 0,1014 | sin_evidencia (3 de 50) | 0,3575 | mejoro |
| p1 · Cortar la corriente del motor | 4 de 50 | conflicto 4 | no | 0,2725 | se_repite (5 de 50) | — | se_repite |
| p6 · Alejarte de la correa | 3 de 50 | conflicto 3 | no | 0,5396 | sin_evidencia (1 de 50) | 0,3087 | mejoro |
| p7 · Sacar tu candado | 2 de 50 | conflicto 2 | no | 0,8070 | se_repite (3 de 50) | — | se_repite |
| p8 · Encender el motor | 2 de 50 | conflicto 2 | no | 0,8070 | se_repite (2 de 50) | — | se_repite |
| p5 · Poner el polín nuevo | 2 de 50 | conflicto 2 | no | 0,8070 | se_repite (3 de 50) | — | se_repite |

Sugerencia del paso recurrente: «La palabra del operario y la evidencia no coinciden: revisar cómo está escrito el paso. La evidencia no vio el paso y una persona lo confirmó: revisar el sensor o la pregunta de la cámara de este paso antes que a quien lo ejecuta. Es un control crítico: que se desvíe seguido no lo vuelve prescindible.»

## Lo que esto no prueba

- Las tasas por paso de una faena real. No hay estudios con tasas de desviación por paso en mantención minera; la desviación autodeclarada va de 0 a 90 % (Mendoza et al. 2024).
- Cuánto baja la desviación al reescribir un paso. Fuera de la casilla de verificación de THERP no hay un efecto publicado: «impracticable» y «apuro» quedan sin efecto declarado y la simulación no los usa para afirmar mejoras.
- Las tasas de THERP y HEART son de errores no intencionales, sobre todo de la industria nuclear. No cubren las violaciones.
- Saltarse un paso que no es control crítico no deja señal: lo que la evidencia no ve, la mejora no lo propone.

Fuentes: REFERENCIAS 10, 13, 33, 34 y 40; NUREG/CR-1278 tabla 20-7; NIST/SEMATECH e-Handbook 7.2.4 y 7.3.3; Sommers et al. 2025 (*Process Science*); Barnett et al. 2005 (regresión a la media).
