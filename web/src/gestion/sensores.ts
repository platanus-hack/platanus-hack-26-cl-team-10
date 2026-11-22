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

const ANOMALIA_VIEJA = /^(\w+) = (-?[\d.]+), lejos de su mediana (-?[\d.]+) \([\d.]+ desvíos\)$/
const uno = (n: string) => String(Math.round(Number(n) * 10) / 10)

/**
 * Un aviso en una línea que se lee de un vistazo: la primera oración, en palabras y sin mayúsculas gritadas.
 * «PERSONA JUNTO A LA MÁQUINA CON EL MOTOR ENCENDIDO. Alejarse; …» → «Persona junto a la máquina con el motor encendido».
 */
export function fraseCorta(texto: string): string {
  const primera = enPalabras(texto).split(/(?<=[^\d])\.\s|;\s/)[0]!.replace(/\.$/, '').trim()
  if (primera !== primera.toUpperCase()) return primera
  const min = primera.toLowerCase()
  return min.charAt(0).toUpperCase() + min.slice(1)
}

/**
 * Los avisos de anomalía que ya están en la bitácora se escribieron como estadística («dist_cm = 148.9, lejos de su
 * mediana 102.1 (22.9 desvíos)»). Se muestran como los nuevos (app/scoring.py): «Distancia 148.9 cm fuera de lo normal: lo
 * habitual es 102.1 cm». En cualquier otro texto, lo que reconoce la cámara va con su nombre de la faena
 * (`conNombresDeClase`).
 */
export function enPalabras(texto: string): string {
  const m = ANOMALIA_VIEJA.exec(texto.trim())
  if (!m) return conNombresDeClase(texto)
  const [, id, valor, centro] = m
  const u = UNIDAD[id!] ? ` ${UNIDAD[id!]}` : ''
  return `${NOMBRE_SENSOR[id!] ?? id} ${uno(valor!)}${u} fuera de lo normal: lo habitual es ${uno(centro!)}${u}`
}

// En la estación del demo los polines son latas: el detector las llama «soda can».
export const NOMBRE_CLASE: Record<string, string> = {
  'soda can': 'polín',
  'red soda can': 'polín rojo',
  'green soda can': 'polín verde',
}

/** Los nombres del detector, del más largo al más corto: «red soda can» antes que «soda can». */
const CLASES_EN_TEXTO = new RegExp(`\\b(${Object.keys(NOMBRE_CLASE).sort((a, b) => b.length - a.length).join('|')})\\b`, 'g')

/**
 * El servidor escribe lo que ve la cámara con el nombre del detector («ya no ve red soda can, y ve green soda can
 * en su lugar»). Aquí va con el de la faena: «ya no ve polín rojo, y ve polín verde en su lugar».
 */
export const conNombresDeClase = (texto: string): string => texto.replace(CLASES_EN_TEXTO, (clase) => NOMBRE_CLASE[clase] ?? clase)
