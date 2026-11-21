import { Center, Group, Paper, Stack, Text, ThemeIcon, Title, UnstyledButton } from '@mantine/core'
import { IconChevronRight, IconClipboardList, IconTool } from '@tabler/icons-react'
import { Navigate, useNavigate } from 'react-router'
import { guardarSesion, useSesion } from '../sesion/sesion'
import { USUARIOS, type Usuario } from '../sesion/usuarios'
import { inicioDe } from './estados'

const ROL = { supervisor: 'Asigna y reasigna las OT', operador: 'Ejecuta las OT en terreno' } as const

function OpcionUsuario({ usuario, onElegir }: { usuario: Usuario; onElegir: () => void }) {
  const Icono = usuario.rol === 'supervisor' ? IconClipboardList : IconTool
  return (
    <UnstyledButton onClick={onElegir} aria-label={`Entrar como ${usuario.nombre}`}>
      <Paper withBorder radius="md" p="md">
        <Group wrap="nowrap" gap="md">
          <ThemeIcon size={44} radius="md" color={usuario.rol === 'supervisor' ? 'roca' : 'accion'}>
            <Icono size={24} />
          </ThemeIcon>
          <Stack gap={0} style={{ flex: 1 }}>
            <Text fw={800} size="lg">
              {usuario.nombre}
            </Text>
            <Text size="sm" c="roca.6">
              {ROL[usuario.rol]}
            </Text>
          </Stack>
          <IconChevronRight size={20} />
        </Group>
      </Paper>
    </UnstyledButton>
  )
}

/** Login falso (FRONTEND.md §2): se elige un usuario del demo, sin contraseña. */
export function PaginaLogin() {
  const usuario = useSesion()
  const navigate = useNavigate()
  if (usuario) return <Navigate to={inicioDe(usuario.rol)} replace />

  const elegir = (u: Usuario) => {
    guardarSesion(u)
    navigate(inicioDe(u.rol), { replace: true })
  }

  return (
    <Center mih="100vh" p="md">
      <Stack w="100%" maw={420} gap="lg">
        <Stack gap={4}>
          <Text fw={900} size="xl" c="accion">
            Factum
          </Text>
          <Title order={1}>¿Quién eres?</Title>
          <Text c="roca.6">Mantenimiento verificado. Elige tu usuario para entrar.</Text>
        </Stack>
        <Stack gap="sm">
          {USUARIOS.map((u) => (
            <OpcionUsuario key={u.id} usuario={u} onElegir={() => elegir(u)} />
          ))}
        </Stack>
      </Stack>
    </Center>
  )
}
