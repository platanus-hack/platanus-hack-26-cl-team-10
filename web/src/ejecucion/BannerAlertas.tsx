import { Box, Group, Paper, Stack, Text } from '@mantine/core'
import { IconAlertTriangle } from '@tabler/icons-react'
import type { EstadoOt, Evento } from '../api/tipos'
import { tipoDeAlerta, type TipoAlerta } from './estado'

const TITULO: Record<TipoAlerta, string> = {
  seguridad: 'Peligro',
  orden: 'Paso saltado',
  control: 'Control perdido',
  senal: 'Precaución',
  otra: 'Peligro',
}

/** Qué pasó, en palabras del operario. Si la alerta no trae lo que hace falta, su detalle tal cual. */
function queDice(a: Evento, ot: EstadoOt | null): { texto: string; ayuda: string | null } {
  const paso = (id: unknown) => ot?.pasos.find((p) => p.id === id)
  switch (tipoDeAlerta(a)) {
    case 'orden': {
      const pendiente = paso(a.evidencia?.pendiente)
      const adelantado = paso(a.evidencia?.adelantado)
      if (pendiente && adelantado)
        return {
          texto: `Hiciste «${adelantado.titulo}» antes de «${pendiente.titulo}».`,
          ayuda: `Haz el paso ${pendiente.orden} o, si ya lo hiciste, confírmalo en el paso.`,
        }
      return { texto: a.detalle, ayuda: null }
    }
    case 'control': {
      const p = paso(a.evidencia?.paso)
      return { texto: p ? `«${p.titulo}» se deshizo. Vuelve a dejarlo como estaba.` : a.detalle, ayuda: 'Se apaga sola cuando el sensor lo vea de vuelta.' }
    }
    case 'seguridad':
      return { texto: a.detalle, ayuda: 'Se apaga sola cuando el sensor lo vea corregido.' }
    default:
      return { texto: a.detalle, ayuda: null }
  }
}

/**
 * Las alertas activas. Informan; no se apagan desde acá: la de seguridad y la de control se
 * resuelven con el sensor, y la de un paso saltado se arregla en ese paso (hacerlo o confirmarlo).
 * Una de nivel error se ve como una tarjeta de bloqueo (LOTO); una de nivel warning, en amarillo.
 */
export function BannerAlertas({ alertas, ot }: { alertas: Evento[]; ot: EstadoOt | null }) {
  if (alertas.length === 0) return null
  return (
    <Stack gap="sm" role="alert">
      {alertas.map((a) => {
        const { texto, ayuda } = queDice(a, ot)
        const titulo = TITULO[tipoDeAlerta(a)]
        const error = (a.calificacion?.nivel ?? (a.capa === 1 ? 'error' : 'warning')) === 'error'
        return error ? (
          <Paper key={a.id} withBorder bg="white" style={{ overflow: 'hidden', borderColor: 'var(--mantine-color-peligro-6)', borderWidth: 3 }}>
            <Box bg="peligro.6" px="md" py={8}>
              <Group gap={8}>
                <IconAlertTriangle size={26} color="white" />
                <Text c="white" fw={900} size="xl">
                  {titulo}
                </Text>
              </Group>
            </Box>
            <Stack p="md" gap={4}>
              <Text fw={700} size="lg">
                {texto}
              </Text>
              {ayuda && (
                <Text size="sm" c="roca.7">
                  {ayuda}
                </Text>
              )}
            </Stack>
          </Paper>
        ) : (
          <Paper key={a.id} bg="precaucion.6" p="md">
            <Group gap={8} wrap="nowrap" align="flex-start">
              <IconAlertTriangle size={22} />
              <Stack gap={2}>
                <Text fw={800}>{titulo}</Text>
                <Text fw={600}>{texto}</Text>
              </Stack>
            </Group>
          </Paper>
        )
      })}
    </Stack>
  )
}
