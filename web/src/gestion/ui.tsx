// Piezas comunes de las pantallas de gestión.

import { Alert, Badge, Box, Button, Center, Container, Drawer, Group, Loader, Paper, Stack, Text, UnstyledButton } from '@mantine/core'
import {
  IconAlertTriangle,
  IconArrowsExchange,
  IconCheck,
  IconHandStop,
  IconCircleDashed,
  IconLogout,
  IconShieldCheck,
  IconTool,
  IconUserCheck,
  IconWifiOff,
} from '@tabler/icons-react'
import { useState, type ReactNode } from 'react'
import { Link, useNavigate } from 'react-router'
import { api } from '../api/cliente'
import type { EstadoGeneral, Nivel } from '../api/tipos'
import { cerrarSesion } from '../sesion/sesion'
import type { Usuario } from '../sesion/usuarios'
import { Marca } from '../Marca'
import { MARCA, SOBRE_TINTA } from '../tema'
import { ESTADOS, inicioDe, VERIFICACION } from './estados'

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
    // Nunca más angosto que su texto: con pautas de nombre largo, la tabla lo cortaba («EN EJECU…»).
    <Badge color={color} size={size} radius="sm" miw="max-content" leftSection={<Icono size={14} stroke={2.5} />}>
      {etiqueta}
    </Badge>
  )
}

const ICONOS_VERIFICACION: Record<Nivel, typeof IconCheck> = {
  ok: IconShieldCheck,
  warning: IconAlertTriangle,
  error: IconHandStop,
}

/** Cómo va lo que Factum verifica en la OT: todo bien, atención o detente. */
export function VerificacionBadge({ nivel, size = 'md' }: { nivel: Nivel; size?: 'sm' | 'md' | 'lg' }) {
  const { etiqueta, color } = VERIFICACION[nivel]
  const Icono = ICONOS_VERIFICACION[nivel]
  return (
    <Badge color={color} variant={nivel === 'ok' ? 'light' : 'filled'} size={size} radius="sm" miw="max-content" leftSection={<Icono size={14} stroke={2.5} />}>
      {etiqueta}
    </Badge>
  )
}

const SECCIONES_SUPERVISOR = [
  { a: '/supervisor', nombre: 'Supervisión' },
  { a: '/supervisor/mejoras', nombre: 'Mejoras' },
]

export function Encabezado({ usuario, seccion }: { usuario: Usuario; seccion: string }) {
  const navigate = useNavigate()
  const [menu, setMenu] = useState(false)
  const salir = () => {
    // El token se lee al llamar: primero se avisa al servidor, después se borra la sesión local.
    api.salir().catch(() => {})
    cerrarSesion()
    navigate('/login', { replace: true })
  }
  return (
    // La banda de la marca: tinta arriba, y todo lo de trabajo sigue claro debajo.
    <Box component="header" style={{ ...SOBRE_TINTA, borderBottom: '1px solid var(--f-linea, transparent)' }}>
      {/* El mismo ancho que <Pagina>: la marca cae sobre el título y «Salir» sobre el borde derecho. */}
      <Container size={1360} px="md">
        <Group justify="space-between" wrap="nowrap" gap="sm" h={56}>
          <Group gap="md" wrap="nowrap">
            {usuario.rol === 'supervisor' ? (
              // El supervisor tiene dos lugares, en un menú a la izquierda que abre el logo: la cruz gira y se vuelve ×.
              <UnstyledButton
                aria-label={menu ? 'Cerrar el menú' : 'Abrir el menú'}
                aria-expanded={menu}
                onClick={() => setMenu((m) => !m)}
                py={6}
                style={{ borderRadius: 4 }}
              >
                <Marca alto={20} girada={menu} />
              </UnstyledButton>
            ) : (
              <UnstyledButton component={Link} to={inicioDe(usuario.rol)} aria-label="Factum, ir al inicio" py={6} style={{ borderRadius: 4 }}>
                <Marca alto={20} />
              </UnstyledButton>
            )}
            <Text c={MARCA.tenue} fw={600} visibleFrom="xs">
              {seccion}
            </Text>
          </Group>
          <Group gap="sm" wrap="nowrap" miw={0}>
            <Stack gap={0} align="flex-end" miw={0}>
              <Text fw={700} lh={1.2} maw="100%" truncate>
                {usuario.nombre}
              </Text>
              {usuario.cliente && (
                <Text size="xs" c={MARCA.tenue} lh={1.2} maw="100%" truncate>
                  {usuario.cliente.nombre}
                </Text>
              )}
            </Stack>
            {/* En el celular queda solo el ícono, para que quepa el nombre completo. */}
            <Button variant="outline" color={MARCA.hueso} size="xs" px={8} aria-label="Salir" onClick={salir} style={{ flexShrink: 0 }}>
              <IconLogout size={16} />
              <Text span inherit ml={6} visibleFrom="xs">
                Salir
              </Text>
            </Button>
          </Group>
        </Group>
      </Container>
      {usuario.rol === 'supervisor' && (
        <Drawer
          opened={menu}
          onClose={() => setMenu(false)}
          position="left"
          size={240}
          withCloseButton={false}
          transitionProps={{ transition: 'slide-right', duration: 300, timingFunction: 'ease' }}
          overlayProps={{ backgroundOpacity: 0.4, blur: 2 }}
          styles={{ content: { ...SOBRE_TINTA, borderRight: '1px solid var(--f-linea)' }, body: { padding: 0 } }}
        >
          <Box h={56} px="md" style={{ display: 'flex', alignItems: 'center', borderBottom: '1px solid var(--f-linea)' }}>
            <UnstyledButton aria-label="Cerrar el menú" onClick={() => setMenu(false)} py={6}>
              <Marca alto={20} girada />
            </UnstyledButton>
          </Box>
          <Stack component="nav" aria-label="Secciones" gap={2} p="sm">
            {SECCIONES_SUPERVISOR.map(({ a, nombre }) => {
              const aqui = nombre === seccion
              return (
                <UnstyledButton
                  key={a}
                  component={Link}
                  to={a}
                  onClick={() => setMenu(false)}
                  aria-current={aqui ? 'page' : undefined}
                  px="md"
                  py={10}
                  fz={15}
                  fw={600}
                  c={aqui ? MARCA.hueso : MARCA.tenue}
                  style={{ borderRadius: 4, background: aqui ? 'var(--f-alto)' : undefined, boxShadow: aqui ? `inset 3px 0 ${MARCA.lima}` : undefined }}
                >
                  {nombre}
                </UnstyledButton>
              )
            })}
          </Stack>
        </Drawer>
      )}
    </Box>
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
    <Container size={1360} px="md" py="lg">
      {children}
    </Container>
  )
}
