import { Alert, Button, Flex, Group, Paper, PasswordInput, Stack, Text, TextInput, ThemeIcon, Title, UnstyledButton } from '@mantine/core'
import { IconChevronRight, IconClipboardList, IconTool } from '@tabler/icons-react'
import { useState, type FormEvent } from 'react'
import { Navigate, useNavigate } from 'react-router'
import { ApiError, api } from '../api/cliente'
import type { Persona } from '../api/tipos'
import { config } from '../config'
import { Marca } from '../Marca'
import { CLAVE_MOCK, PERSONAS } from '../mocks/personas'
import { guardarSesion, motivoDeSalida, useSesion } from '../sesion/sesion'
import { usuarioDe } from '../sesion/usuarios'
import { SOBRE_TINTA, TITULAR } from '../tema'
import { inicioDe } from './estados'

const ROL = { supervisor: 'Pide y asigna las OT', operador: 'Ejecuta las OT en terreno' } as const

function mensajeDeLogin(e: unknown): string {
  if (e instanceof ApiError && e.tipo === 'credenciales') return e.message
  if (e instanceof ApiError && (e.tipo === 'red' || e.tipo === 'timeout')) {
    return 'No pudimos conectar con el servidor. Revisa tu conexión y vuelve a intentar.'
  }
  return 'No pudimos entrar. Vuelve a intentar en un momento.'
}

function OpcionPersona({ persona, onElegir, disabled }: { persona: Persona; onElegir: () => void; disabled: boolean }) {
  const Icono = persona.rol === 'supervisor' ? IconClipboardList : IconTool
  return (
    <UnstyledButton onClick={onElegir} disabled={disabled} aria-label={`Entrar como ${persona.nombre}`}>
      <Paper withBorder radius="md" p="sm">
        <Group wrap="nowrap" gap="md">
          <ThemeIcon size={40} radius="md" color={persona.rol === 'supervisor' ? 'roca' : 'accion'}>
            <Icono size={22} />
          </ThemeIcon>
          <Stack gap={0} style={{ flex: 1 }}>
            <Text fw={800}>{persona.nombre}</Text>
            <Text size="sm" c="roca.6">
              {ROL[persona.rol]}
            </Text>
          </Stack>
          <IconChevronRight size={20} />
        </Group>
      </Paper>
    </UnstyledButton>
  )
}

/** Login con correo y clave (`POST /auth/entrar`). Con mock, también con un toque por persona. */
export function PaginaLogin() {
  const usuario = useSesion()
  const navigate = useNavigate()
  const [vencida] = useState(() => motivoDeSalida() === 'vencida')
  const [correo, setCorreo] = useState('')
  const [clave, setClave] = useState('')
  const [enviando, setEnviando] = useState(false)
  const [error, setError] = useState<string | null>(null)
  if (usuario) return <Navigate to={inicioDe(usuario.rol)} replace />

  const entrar = async (u: string, c: string) => {
    setEnviando(true)
    setError(null)
    try {
      const { token, expira, persona } = await api.entrar(u.trim(), c)
      guardarSesion({ usuario: usuarioDe(persona), token, expira })
      navigate(inicioDe(persona.rol), { replace: true })
    } catch (e) {
      setError(mensajeDeLogin(e))
      setEnviando(false)
    }
  }

  const enviar = (ev: FormEvent) => {
    ev.preventDefault()
    void entrar(correo, clave)
  }

  return (
    // La marca a un lado (arriba en el celular), sobre tinta; el formulario, claro como el resto de la app.
    <Flex mih="100vh" direction={{ base: 'column', md: 'row' }}>
      <Flex direction="column" justify="space-between" gap={32} w={{ base: '100%', md: '42%' }} p={{ base: 'lg', md: 48 }} style={SOBRE_TINTA}>
        <Marca alto={26} />
        <Text component="p" m={0} maw={460} ff={TITULAR} fw={400} fz={{ base: 26, md: 44 }} lh={1.15}>
          Cada paso verificado queda como un hecho.
        </Text>
      </Flex>
      <Flex flex={1} justify="center" align={{ base: 'flex-start', md: 'center' }} px="md" py="xl">
        <Stack w="100%" maw={420} gap="lg">
          <Stack gap={4}>
            <Title order={1}>Entrar</Title>
            <Text c="roca.6">Con el correo y la clave que te dio tu empresa.</Text>
          </Stack>
          {vencida && !error && (
            <Alert color="precaucion" variant="light">
              Tu sesión venció. Vuelve a entrar.
            </Alert>
          )}
          <form onSubmit={enviar} noValidate>
            <Stack gap="md">
              <TextInput
                label="Correo"
                type="email"
                size="lg"
                autoComplete="username"
                placeholder="nombre@empresa.cl"
                value={correo}
                onChange={(e) => setCorreo(e.currentTarget.value)}
                required
              />
              <PasswordInput
                label="Clave"
                size="lg"
                autoComplete="current-password"
                value={clave}
                onChange={(e) => setClave(e.currentTarget.value)}
                required
              />
              {error && (
                <Text c="peligro" fw={600} role="alert">
                  {error}
                </Text>
              )}
              <Button type="submit" size="lg" fullWidth loading={enviando} disabled={!correo.trim() || !clave}>
                Entrar
              </Button>
            </Stack>
          </form>
          {config.MOCK && (
            <Stack gap="xs">
              <Text size="sm" c="roca.7" fw={600}>
                Datos de prueba: entra con un toque, o con su correo y la clave «{CLAVE_MOCK}».
              </Text>
              {PERSONAS.map((p) => (
                <OpcionPersona key={p.id} persona={p} disabled={enviando} onElegir={() => void entrar(p.usuario, CLAVE_MOCK)} />
              ))}
            </Stack>
          )}
        </Stack>
      </Flex>
    </Flex>
  )
}
