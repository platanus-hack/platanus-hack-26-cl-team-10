// Piezas comunes de las pantallas de gestión.

import { Alert, Badge, Box, Button, Center, Container, Group, Loader, Paper, Stack, Text, UnstyledButton } from '@mantine/core'
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
import { useCallback, useEffect, useState, type ReactNode } from 'react'
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

const ANCHO_MENU = 240

/** El nombre de quien entró y «Salir». En el supervisor va al pie del menú; en el operario, en la banda. */
function Cuenta({ usuario, salir, abajo = false }: { usuario: Usuario; salir: () => void; abajo?: boolean }) {
  return (
    <Group gap="sm" wrap="nowrap" miw={0} justify={abajo ? 'space-between' : undefined}>
      <Stack gap={0} align={abajo ? 'flex-start' : 'flex-end'} miw={0}>
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
  )
}

/**
 * El menú del supervisor: un panel a la izquierda que abre el logo y empuja la página (no la tapa). La cruz del logo
 * gira hasta ser una ×. Cerrado queda fuera de la pantalla e `inert`, para que el teclado no llegue a él.
 */
function Menu({ abierto, cerrar, seccion, usuario, salir }: { abierto: boolean; cerrar: () => void; seccion: string; usuario: Usuario; salir: () => void }) {
  useEffect(() => {
    const raiz = document.documentElement
    if (abierto) raiz.dataset.menu = 'abierto'
    else delete raiz.dataset.menu
    const escape = (e: KeyboardEvent) => e.key === 'Escape' && cerrar()
    if (abierto) window.addEventListener('keydown', escape)
    return () => {
      window.removeEventListener('keydown', escape)
      delete raiz.dataset.menu
    }
  }, [abierto, cerrar])
  return (
    <Box
      component="aside"
      aria-label="Menú"
      inert={!abierto}
      style={{
        ...SOBRE_TINTA,
        position: 'fixed',
        inset: '0 auto 0 0',
        width: ANCHO_MENU,
        zIndex: 200,
        display: 'flex',
        flexDirection: 'column',
        borderRight: '1px solid var(--f-linea)',
        transform: abierto ? 'none' : 'translateX(-100%)',
        transition: 'transform 300ms ease',
      }}
    >
      <Box h={56} px="md" style={{ display: 'flex', alignItems: 'center', borderBottom: '1px solid var(--f-linea)', flexShrink: 0 }}>
        <UnstyledButton aria-label="Cerrar el menú" onClick={cerrar} py={6} style={{ borderRadius: 4 }}>
          <Marca alto={20} girada={abierto} />
        </UnstyledButton>
      </Box>
      <Stack component="nav" aria-label="Secciones" gap={2} p="sm" style={{ flex: 1 }}>
        {SECCIONES_SUPERVISOR.map(({ a, nombre }) => {
          const aqui = nombre === seccion
          return (
            <UnstyledButton
              key={a}
              component={Link}
              to={a}
              onClick={cerrar}
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
      <Box p="md" style={{ borderTop: '1px solid var(--f-linea)' }}>
        <Cuenta usuario={usuario} salir={salir} abajo />
      </Box>
    </Box>
  )
}

export function Encabezado({ usuario, seccion }: { usuario: Usuario; seccion: string }) {
  const navigate = useNavigate()
  const [menu, setMenu] = useState(false)
  const cerrar = useCallback(() => setMenu(false), [])
  const salir = () => {
    // El token se lee al llamar: primero se avisa al servidor, después se borra la sesión local.
    api.salir().catch(() => {})
    cerrarSesion()
    navigate('/login', { replace: true })
  }
  const supervisor = usuario.rol === 'supervisor'
  return (
    // La banda de la marca: tinta arriba, y todo lo de trabajo sigue claro debajo.
    <Box component="header" style={{ ...SOBRE_TINTA, borderBottom: '1px solid var(--f-linea, transparent)' }}>
      {/* El mismo ancho que <Pagina>: la marca cae sobre el título y «Salir» sobre el borde derecho. */}
      <Container size={1360} px="md">
        <Group justify="space-between" wrap="nowrap" gap="sm" h={56}>
          {supervisor ? (
            // Al abrir, este logo no salta: se queda donde está mientras la página se corre (vuelve 240 px), gira su cruz
            // y se funde con el del menú, que entra por debajo (index.css, .logo-banda).
            <UnstyledButton
              className="logo-banda"
              aria-label="Abrir el menú"
              aria-expanded={menu}
              onClick={() => setMenu(true)}
              py={6}
              style={{ borderRadius: 4, pointerEvents: menu ? 'none' : undefined }}
            >
              <Marca alto={20} girada={menu} />
            </UnstyledButton>
          ) : (
            <Group gap="md" wrap="nowrap">
              <UnstyledButton component={Link} to={inicioDe(usuario.rol)} aria-label="Factum, ir al inicio" py={6} style={{ borderRadius: 4 }}>
                <Marca alto={20} />
              </UnstyledButton>
              <Text c={MARCA.tenue} fw={600} visibleFrom="xs">
                {seccion}
              </Text>
            </Group>
          )}
          {!supervisor && <Cuenta usuario={usuario} salir={salir} />}
        </Group>
      </Container>
      {supervisor && <Menu abierto={menu} cerrar={cerrar} seccion={seccion} usuario={usuario} salir={salir} />}
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
