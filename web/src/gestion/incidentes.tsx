// Lo que comparten «Hoy» y la lista de OT: el id que abre una OT y los incidentes en curso, con su campana.

import { Anchor, Button, Group, Paper, Stack, Text } from '@mantine/core'
import { IconAlertTriangle, IconEye } from '@tabler/icons-react'
import { Link } from 'react-router'
import { useNombres } from '../sesion/usuarios'
import type { Incidente } from './estados'
import { rutaDe } from './rutaDeOt'
import { fraseCorta } from './sensores'


/** El id de la OT lleva a su vista en vivo: cámara, sensores y bitácora. */
export function IdOt({ ot }: { ot: string }) {
  return (
    <Anchor component={Link} to={rutaDe(ot)} fw={500} ff="var(--f-mono)" c="var(--f-accion-texto)" underline="hover" style={{ letterSpacing: '0.06em' }}>
      {ot.toUpperCase()}
    </Anchor>
  )
}

/** Lo que pide mirar ya: OT abiertas en «detente». Cada una lleva a su vista en vivo. */
export function BarraIncidentes({ incidentes }: { incidentes: Incidente[] }) {
  const nombreDe = useNombres()
  if (incidentes.length === 0) return null
  // Compacta: una línea por OT, con lo que pasa en pocas palabras. El detalle está en la vista en vivo.
  return (
    <Paper radius="md" p="sm" withBorder role="alert" aria-label="Incidentes en curso" style={{ borderLeft: '4px solid var(--mantine-color-peligro-6)' }} bg="peligro.0">
      <Group gap="xs" mb={6} c="peligro.7">
        <IconAlertTriangle size={18} />
        <Text fw={800} c="peligro.7">
          {incidentes.length === 1 ? 'Un incidente en curso' : `${incidentes.length} incidentes en curso`}
        </Text>
      </Group>
      <Stack gap={4}>
        {incidentes.map((i) => (
          <Group key={i.ot} justify="space-between" wrap="nowrap" gap="sm">
            <Text size="sm" truncate>
              <Text span fw={700}>
                {i.ot.toUpperCase()}
                {i.operador ? ` · ${nombreDe(i.operador)}` : ''}
              </Text>
              {' — '}
              {fraseCorta(i.que)}
            </Text>
            <Button component={Link} to={rutaDe(i.ot)} variant="subtle" color="peligro" size="compact-sm" leftSection={<IconEye size={16} />} style={{ flexShrink: 0 }} aria-label={`Ver ${i.ot} en vivo`}>
              Ver
            </Button>
          </Group>
        ))}
      </Stack>
    </Paper>
  )
}
