import { Badge, Box, Group, Paper, SegmentedControl, Stack, Text, Tooltip, VisuallyHidden } from '@mantine/core'
import { useEffect, useState } from 'react'
import { api } from '../api/cliente'
import type { PuntoSerie } from '../api/tipos'

type Rango = 'semana' | 'mes' | 'año'
type Punto = { clave: string; corta: string; larga: string }
type Medida = 'ots_completas' | 'desviaciones' | 'alertas_de_seguridad'

/**
 * Tres líneas, un eje. Colores propios del gráfico, no los del tema: los del tema (lima, ámbar y rojo apagados) no
 * pasan el validador de color en oscuro. Estos sí, en todos los pares (dataviz/validate_palette.js, --pairs all):
 * azul lo que se termina, ámbar lo que se desvía, carmesí lo que es de seguridad.
 */
const SERIES: { medida: Medida; nombre: string; color: string }[] = [
  { medida: 'ots_completas', nombre: 'OT completas', color: '#3a8ccf' },
  { medida: 'desviaciones', nombre: 'Desviaciones', color: '#c08a1a' },
  { medida: 'alertas_de_seguridad', nombre: 'Alertas de seguridad', color: '#d1407a' },
]
const ANCHO = 1000
const ALTO = 200

const iso = (d: Date) => d.toLocaleDateString('sv-SE') // AAAA-MM-DD, en la hora del supervisor

/** Los periodos del rango, sin huecos: los últimos 7 o 30 días, o los últimos 12 meses. */
function periodos(rango: Rango, hoy = new Date()): Punto[] {
  if (rango === 'año') {
    return Array.from({ length: 12 }, (_, i) => {
      const d = new Date(hoy.getFullYear(), hoy.getMonth() - 11 + i, 1)
      return {
        clave: iso(d),
        corta: d.toLocaleDateString('es-CL', { month: 'short' }).replace('.', ''),
        larga: d.toLocaleDateString('es-CL', { month: 'long', year: 'numeric' }),
      }
    })
  }
  const dias = rango === 'semana' ? 7 : 30
  return Array.from({ length: dias }, (_, i) => {
    const d = new Date(hoy.getFullYear(), hoy.getMonth(), hoy.getDate() - (dias - 1) + i)
    return {
      clave: iso(d),
      corta: rango === 'semana' ? d.toLocaleDateString('es-CL', { weekday: 'short' }).replace('.', '') : String(d.getDate()),
      larga: d.toLocaleDateString('es-CL', { weekday: 'long', day: 'numeric', month: 'long' }),
    }
  })
}

/**
 * Datos de ejemplo, solo para que se entienda el gráfico mientras no hay historia: más OT completas con el tiempo y
 * menos desviaciones, que es lo que la mejora continua busca. Deterministas, para que no salten en cada recarga.
 */
function ejemplo(n: number, rango: Rango): Record<Medida, number>[] {
  const escala = rango === 'año' ? 20 : 1
  return Array.from({ length: n }, (_, i) => {
    const t = n > 1 ? i / (n - 1) : 1
    const ruido = (k: number) => Math.sin(i * 2.3 + k) * 0.8
    return {
      ots_completas: Math.max(0, Math.round((3 + 4 * t + ruido(1)) * escala)),
      desviaciones: Math.max(0, Math.round((5 - 3 * t + ruido(2)) * escala)),
      alertas_de_seguridad: Math.max(0, Math.round((2 - 1.6 * t + ruido(3) * 0.6) * escala)),
    }
  })
}

/** La actividad de la empresa en el tiempo: tres líneas en un mismo eje, por semana, mes o año. */
export function Actividad() {
  const [rango, setRango] = useState<Rango>('semana')
  const [serie, setSerie] = useState<PuntoSerie[] | null>(null)
  const [encima, setEncima] = useState<number | null>(null)
  const puntos = periodos(rango)

  useEffect(() => {
    let vivo = true
    api.leerSerie(rango === 'año' ? 'mes' : 'dia', periodos(rango)[0]!.clave).then(
      (s) => vivo && setSerie(s),
      () => vivo && setSerie([]),
    )
    return () => {
      vivo = false
    }
  }, [rango])

  const de = new Map((serie ?? []).map((s) => [s.periodo, s]))
  const reales = puntos.map((p) => ({
    ots_completas: de.get(p.clave)?.ots_completas ?? 0,
    desviaciones: de.get(p.clave)?.desviaciones ?? 0,
    alertas_de_seguridad: de.get(p.clave)?.alertas_de_seguridad ?? 0,
  }))
  // Con menos de 3 periodos con algo, una línea no dice nada: se muestra un ejemplo, y se dice que lo es.
  const conHistoria = reales.filter((r) => r.ots_completas + r.desviaciones + r.alertas_de_seguridad > 0).length >= 3
  const valores = conHistoria ? reales : ejemplo(puntos.length, rango)
  const max = Math.max(1, ...valores.flatMap((v) => SERIES.map((s) => v[s.medida])))
  const x = (i: number) => (puntos.length > 1 ? (i / (puntos.length - 1)) * ANCHO : ANCHO / 2)
  const y = (v: number) => ALTO - (v / max) * ALTO
  const cadaCuanto = puntos.length > 12 ? 5 : 1

  return (
    <Paper component="section" aria-label="Actividad" withBorder radius="md" p="md">
      <Group justify="space-between" mb="sm" gap="sm">
        <Group gap="sm">
          <Text fw={800}>Actividad</Text>
          {serie && !conHistoria && (
            <Badge variant="light" color="roca" radius="sm" tt="none">
              Datos de ejemplo: todavía no hay historia suficiente
            </Badge>
          )}
        </Group>
        <SegmentedControl
          size="xs"
          aria-label="Periodo del gráfico"
          value={rango}
          onChange={(v) => setRango(v as Rango)}
          data={[
            { value: 'semana', label: 'Semana' },
            { value: 'mes', label: 'Mes' },
            { value: 'año', label: 'Año' },
          ]}
        />
      </Group>

      {/* La leyenda: cada línea con su color, su nombre y su total del periodo. El color nunca va solo. */}
      <Group gap="lg" mb="sm">
        {SERIES.map((s) => (
          <Group key={s.medida} gap={6} wrap="nowrap">
            <Box w={16} h={3} style={{ background: s.color, borderRadius: 2 }} />
            <Text size="sm">{s.nombre}</Text>
            <Text size="sm" c="dimmed">
              {valores.reduce((a, v) => a + v[s.medida], 0)}
            </Text>
          </Group>
        ))}
      </Group>

      <Box pos="relative" h={ALTO} ml={28} aria-hidden>
        {[1, 0.5, 0].map((f) => (
          <Box key={f} pos="absolute" left={0} right={0} top={`${(1 - f) * 100}%`} style={{ borderTop: `1px ${f ? 'dashed' : 'solid'} var(--f-linea${f ? '' : '-2'})` }}>
            <Text pos="absolute" left={-28} top={-8} size="xs" c="dimmed" w={22} ta="right" lh={1}>
              {Math.round(max * f)}
            </Text>
          </Box>
        ))}
        <svg viewBox={`0 0 ${ANCHO} ${ALTO}`} preserveAspectRatio="none" width="100%" height={ALTO} style={{ position: 'absolute', inset: 0, overflow: 'visible' }}>
          {encima !== null && <line x1={x(encima)} x2={x(encima)} y1={0} y2={ALTO} stroke="var(--f-linea-2)" strokeWidth={1} vectorEffect="non-scaling-stroke" />}
          {SERIES.map((s) => (
            <polyline
              key={s.medida}
              points={valores.map((v, i) => `${x(i)},${y(v[s.medida])}`).join(' ')}
              fill="none"
              stroke={s.color}
              strokeWidth={2}
              strokeLinejoin="round"
              strokeLinecap="round"
              vectorEffect="non-scaling-stroke"
            />
          ))}
        </svg>
        {/* Las zonas de hover: una por periodo, más anchas que la línea, con los tres valores. */}
        <Box pos="absolute" style={{ inset: 0, display: 'flex' }}>
          {puntos.map((p, i) => (
            <Tooltip
              key={p.clave}
              withArrow
              openDelay={30}
              label={
                <Stack gap={2}>
                  <Text size="xs" fw={700}>
                    {p.larga}
                  </Text>
                  {SERIES.map((s) => (
                    <Group key={s.medida} gap={6} wrap="nowrap">
                      <Box w={10} h={3} style={{ background: s.color, borderRadius: 2 }} />
                      <Text size="xs">
                        {s.nombre}: {valores[i]![s.medida]}
                      </Text>
                    </Group>
                  ))}
                </Stack>
              }
            >
              <Box style={{ flex: 1 }} onMouseEnter={() => setEncima(i)} onMouseLeave={() => setEncima(null)} />
            </Tooltip>
          ))}
        </Box>
      </Box>
      <Group gap={0} wrap="nowrap" ml={28} mt={6} aria-hidden>
        {puntos.map((p, i) => (
          <Text key={p.clave} size="xs" c="dimmed" ta="center" style={{ flex: 1, minWidth: 0 }}>
            {i % cadaCuanto === 0 || i === puntos.length - 1 ? p.corta : ''}
          </Text>
        ))}
      </Group>

      <VisuallyHidden>
        <table>
          <caption>Actividad{conHistoria ? '' : ' (datos de ejemplo)'}</caption>
          <thead>
            <tr>
              <th>Periodo</th>
              {SERIES.map((s) => (
                <th key={s.medida}>{s.nombre}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {puntos.map((p, i) => (
              <tr key={p.clave}>
                <th scope="row">{p.larga}</th>
                {SERIES.map((s) => (
                  <td key={s.medida}>{valores[i]![s.medida]}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </VisuallyHidden>
    </Paper>
  )
}
