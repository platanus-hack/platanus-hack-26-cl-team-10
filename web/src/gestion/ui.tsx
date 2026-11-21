// Piezas comunes de las pantallas de gestión.

import { Alert, Badge, Box, Button, Center, Container, Group, Loader, Paper, Stack, Text } from '@mantine/core'
import {
  IconArrowsExchange,
  IconCheck,
  IconCircleDashed,
  IconLogout,
  IconTool,
  IconUserCheck,
  IconWifiOff,
} from '@tabler/icons-react'
import type { ReactNode } from 'react'
import { useNavigate } from 'react-router'
import type { EstadoGeneral } from '../api/tipos'
import { cerrarSesion } from '../sesion/sesion'
import type { Usuario } from '../sesion/usuarios'
import { ESTADOS } from './estados'

const ICONOS: Record<EstadoGeneral, typeof IconCheck> = {
  sin_asignar: IconCircleDashed,
  asignada: IconUserCheck,
  en_ejecucion: IconTool,
  entregada: IconArrowsExchange,
  completa: IconCheck,
}

/** El color nunca va solo: siempre con ícono y texto. */
export function EstadoBadge({ estado, size = 'md' }: { estado: EstadoGeneral; size?: 'sm' | 'md' | 'lg' }) {
  const { etiqueta, color } = ESTADOS[estado]
  const Icono = ICONOS[estado]
  return (
    <Badge color={color} size={size} radius="sm" leftSection={<Icono size={14} stroke={2.5} />}>
      {etiqueta}
    </Badge>
  )
}

export function Encabezado({ usuario, seccion }: { usuario: Usuario; seccion: string }) {
  const navigate = useNavigate()
  const salir = () => {
    cerrarSesion()
    navigate('/login', { replace: true })
  }
  return (
    <Paper component="header" radius={0} shadow="xs" px="md" py="sm">
      <Group justify="space-between" wrap="nowrap" maw={1200} mx="auto">
        <Group gap="sm" wrap="nowrap">
          <Text fw={900} size="lg" c="accion">
            Factum
          </Text>
          <Text c="roca.6" fw={600} visibleFrom="xs">
            {seccion}
          </Text>
        </Group>
        <Group gap="sm" wrap="nowrap">
          <Text fw={700}>{usuario.nombre}</Text>
          <Button variant="default" size="xs" leftSection={<IconLogout size={16} />} onClick={salir}>
            Salir
          </Button>
        </Group>
      </Group>
    </Paper>
  )
}

/** Carga, error sin datos o lista vacía. Devuelve null cuando hay algo que mostrar. */
export function EstadoLista({
  cargando,
  error,
  vacia,
  textoVacia,
  onReintentar,
}: {
  cargando: boolean
  error: string | null
  vacia: boolean
  textoVacia: ReactNode
  onReintentar: () => void
}) {
  if (cargando && !error) {
    return (
      <Center py="xl">
        <Loader aria-label="Cargando las OT" />
      </Center>
    )
  }
  if (cargando && error) {
    return (
      <Alert color="peligro" variant="light" icon={<IconWifiOff />} title="No se pudieron cargar las OT">
        <Stack gap="sm" align="flex-start">
          <Text size="sm">{error}</Text>
          <Button size="xs" onClick={onReintentar}>
            Reintentar
          </Button>
        </Stack>
      </Alert>
    )
  }
  if (vacia) {
    return (
      <Paper withBorder p="xl" radius="md">
        <Text ta="center" c="roca.6">
          {textoVacia}
        </Text>
      </Paper>
    )
  }
  return null
}

/** Una recarga falló pero hay datos: se siguen mostrando, con aviso. */
export function FranjaDesactualizada({ error }: { error: string | null }) {
  if (!error) return null
  return (
    <Box bg="precaucion.6" px="md" py={6} role="status">
      <Group gap="xs" justify="center" wrap="nowrap">
        <IconWifiOff size={16} />
        <Text size="sm" fw={600}>
          {error}. Mostrando lo último que llegó.
        </Text>
      </Group>
    </Box>
  )
}

export function Pagina({ children }: { children: ReactNode }) {
  return (
    <Container size={1200} px="md" py="lg">
      {children}
    </Container>
  )
}
