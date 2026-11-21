import { Button, Group, Paper, Text } from '@mantine/core'
import { IconArrowLeft } from '@tabler/icons-react'
import { Link } from 'react-router'
import type { Usuario } from '../sesion/usuarios'

/** La barra de arriba en las pantallas de una OT: volver a la lista sin entregar el turno. */
export function BarraOt({ usuario }: { usuario: Usuario }) {
  return (
    <Paper component="header" radius={0} shadow="xs" px="md" py={6}>
      <Group justify="space-between" wrap="nowrap" maw={560} mx="auto">
        <Button component={Link} to="/operador" variant="subtle" color="roca" px={6} leftSection={<IconArrowLeft size={18} />}>
          Mis OT
        </Button>
        <Group gap="xs" wrap="nowrap">
          <Text fw={900} c="accion">
            Factum
          </Text>
          <Text fw={700}>{usuario.nombre}</Text>
        </Group>
      </Group>
    </Paper>
  )
}
