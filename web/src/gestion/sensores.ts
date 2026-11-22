// Cómo se llaman, para una persona, los sensores y lo que reconoce la cámara de la estación.

export const NOMBRE_SENSOR: Record<string, string> = {
  energia: 'Energía',
  motor: 'Motor',
  guarda: 'Guarda',
  bloqueo: 'Bloqueo',
  reed_bloqueo: 'Candado',
  operario: 'Persona junto a la máquina',
  equipo: 'Equipo',
  temp_c: 'Temperatura',
  hum_pct: 'Humedad',
  dist_cm: 'Distancia',
  tierra: 'Puesta a tierra',
  tension: 'Tensión',
  seccionador: 'Seccionador',
  zona: 'Zona',
  implementos: 'Implementos',
}

export const UNIDAD: Record<string, string> = { temp_c: '°C', hum_pct: '%', dist_cm: 'cm' }

// En la estación del demo los polines son latas: el detector las llama «soda can».
export const NOMBRE_CLASE: Record<string, string> = { 'soda can': 'polín', 'red soda can': 'polín' }
