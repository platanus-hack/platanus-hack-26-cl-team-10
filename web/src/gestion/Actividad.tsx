import { Box, Group, Paper, SegmentedControl, SimpleGrid, Stack, Text, Tooltip, VisuallyHidden } from '@mantine/core'
import { useEffect, useState } from 'react'
import { api } from '../api/cliente'
import type { PuntoSerie } from '../api/tipos'

type Rango = 'semana' | 'mes' | 'año'
type Punto = { clave: string; corta: string; larga: string }
const ALTO = 140

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
 * Una sola serie en barras, sobre una línea base: el máximo marcado arriba, el valor exacto al pasar el cursor por la
 * columna (que es más ancha que la barra), y una tabla para lectores de pantalla. Sin leyenda: el título la nombra.
 */
function Barras({ titulo, puntos, valores }: { titulo: string; puntos: Punto[]; valores: number[] }) {
  const max = Math.max(1, ...valores)
  const total = valores.reduce((a, b) => a + b, 0)
  const cadaCuanto = puntos.length > 12 ? 5 : 1
  return (
    <Stack gap={6}>
      <Group justify="space-between">
        <Text size="sm" fw={700}>
          {titulo}
        </Text>
        <Text size="sm" c="dimmed">
          {total} en el periodo
        </Text>
      </Group>
      <Box pos="relative" h={ALTO} style={{ display: 'flex', alignItems: 'flex-end', gap: 2, borderBottom: '1px solid var(--f-linea-2)' }} aria-hidden>
        <Box pos="absolute" top={0} left={0} right={0} style={{ borderTop: '1px dashed var(--f-linea)' }} />
        <Text pos="absolute" top={2} left={4} size="xs" c="dimmed" lh={1}>
          {max}
        </Text>
        {puntos.map((p, i) => (
          <Tooltip key={p.clave} label={`${p.larga}: ${valores[i]}`} withArrow openDelay={50}>
            <Box h="100%" style={{ flex: 1, display: 'flex', alignItems: 'flex-end', cursor: 'default' }}>
              <Box
                w="100%"
                h={`${(valores[i]! / max) * 100}%`}
                mih={valores[i] ? 2 : 0}
                style={{ background: 'var(--f-accion)', borderRadius: '4px 4px 0 0' }}
              />
            </Box>
          </Tooltip>
        ))}
      </Box>
      <Group gap={2} wrap="nowrap" aria-hidden>
        {puntos.map((p, i) => (
          <Text key={p.clave} size="xs" c="dimmed" ta="center" style={{ flex: 1, minWidth: 0 }}>
            {i % cadaCuanto === 0 || i === puntos.length - 1 ? p.corta : ''}
          </Text>
        ))}
      </Group>
      <VisuallyHidden>
        <table>
          <caption>{titulo}</caption>
          <tbody>
            {puntos.map((p, i) => (
              <tr key={p.clave}>
                <th scope="row">{p.larga}</th>
                <td>{valores[i]}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </VisuallyHidden>
    </Stack>
  )
}

/** La actividad de la empresa en el tiempo: OT completas y desviaciones, por semana, mes o año. */
export function Actividad() {
  const [rango, setRango] = useState<Rango>('semana')
  const [serie, setSerie] = useState<PuntoSerie[] | null>(null)
  const puntos = periodos(rango)

  useEffect(() => {
    let vivo = true
    const intervalo = rango === 'año' ? 'mes' : 'dia'
    api.leerSerie(intervalo, periodos(rango)[0]!.clave).then(
      (s) => vivo && setSerie(s),
      () => vivo && setSerie([]),
    )
    return () => {
      vivo = false
    }
  }, [rango])

  const de = new Map((serie ?? []).map((s) => [s.periodo, s]))
  return (
    <Paper component="section" aria-label="Actividad" withBorder radius="md" p="md">
      <Group justify="space-between" mb="md">
        <Text fw={800}>Actividad</Text>
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
      <SimpleGrid cols={{ base: 1, sm: 2 }} spacing="xl">
        <Barras titulo="OT completas" puntos={puntos} valores={puntos.map((p) => de.get(p.clave)?.ots_completas ?? 0)} />
        <Barras titulo="Desviaciones" puntos={puntos} valores={puntos.map((p) => de.get(p.clave)?.desviaciones ?? 0)} />
      </SimpleGrid>
    </Paper>
  )
}
