import { Button, Paper, Stack, Text } from '@mantine/core'
import { IconPlugConnected } from '@tabler/icons-react'
import type { Sesion } from '../api/tipos'
import { useNombres } from '../sesion/usuarios'

const hora = (ts: string) => new Date(ts).toLocaleTimeString('es-CL', { hour: '2-digit', minute: '2-digit', hourCycle: 'h23' })

/**
 * La estación ejecuta otra OT abierta de la empresa. Se dice cuál y de quién, en vez de la regla de
 * la API. Tomarla es un toque de la persona, nunca un reintento: esa OT deja de recibir sus sensores.
 */
export function EstacionOcupada({ sesion, tomando, onTomar }: { sesion: Sesion; tomando: boolean; onTomar(): void }) {
  const nombreDe = useNombres()
  return (
    <Paper
      component="section"
      aria-label="La estación está ocupada"
      withBorder
      p="md"
      bg="white"
      style={{ borderColor: 'var(--mantine-color-precaucion-6)', borderWidth: 2 }}
    >
      <Stack gap="sm">
        <Text fw={800} size="lg">
          La estación está ocupada
        </Text>
        <Text>
          La estación {sesion.edge_id} está con la {sesion.ot_id.toUpperCase()} de {nombreDe(sesion.operario)} desde las{' '}
          {hora(sesion.desde)}.
        </Text>
        <Text size="sm" c="roca.7">
          Si la tomas, esa OT deja de recibir sus sensores. Si esperas, esta OT parte sola apenas la estación quede libre.
        </Text>
        <Button size="xl" h={64} fullWidth color="precaucion" leftSection={<IconPlugConnected size={24} />} loading={tomando} onClick={onTomar}>
          Tomar la estación
        </Button>
      </Stack>
    </Paper>
  )
}
