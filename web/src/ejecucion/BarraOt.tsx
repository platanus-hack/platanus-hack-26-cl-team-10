import { Box, Button, Group, Text } from '@mantine/core'
import { IconArrowLeft } from '@tabler/icons-react'
import { Link } from 'react-router'
import { Marca } from '../Marca'
import type { Usuario } from '../sesion/usuarios'
import { MARCA, SOBRE_TINTA } from '../tema'

/** La barra de arriba en las pantallas de una OT: volver a la lista sin entregar el turno. */
export function BarraOt({ usuario }: { usuario: Usuario }) {
  return (
    <Box component="header" px="md" style={SOBRE_TINTA}>
      <Group justify="space-between" wrap="nowrap" gap="md" maw={560} mx="auto" h={48}>
        <Button component={Link} to="/operador" variant="subtle" color={MARCA.hueso} px={6} leftSection={<IconArrowLeft size={18} />} style={{ flexShrink: 0 }}>
          Mis OT
        </Button>
        {/* La marca antes del nombre: al revés, la cruz se lee como un «más» entre los dos. */}
        <Group gap="sm" wrap="nowrap" miw={0}>
          <Marca alto={16} />
          <Text fw={700} truncate>
            {usuario.nombre}
          </Text>
        </Group>
      </Group>
    </Box>
  )
}
