import { Anchor, Box, Button, Center, Container, Group, Loader, Stack, Text } from '@mantine/core'
import { IconVolume } from '@tabler/icons-react'
import { useEffect, useRef, useState, type ReactNode } from 'react'
import { Link, useNavigate, useParams } from 'react-router'
import type { EstadoOt } from '../api/tipos'
import { useSesion } from '../sesion/sesion'
import type { Usuario } from '../sesion/usuarios'
import { FranjaSinConexion, MensajeError } from './Avisos'
import { Briefing } from './Briefing'
import { avance, relevoPendiente } from './estado'
import { OtCompleta } from './OtCompleta'
import { PantallaEjecucion } from './PantallaEjecucion'
import { useEjecucion } from './useEjecucion'

/** /ot/:id — la ejecución de la OT para el operador con sesión. */
export function PaginaOt() {
  const { id = '' } = useParams()
  const usuario = useSesion()
  if (!usuario) return null
  return <Ejecucion key={`${id}:${usuario.id}`} otId={id} usuario={usuario} />
}

/** El primer toque: desbloquea el audio y abre la sesión. */
function Puerta({ otId, ot, onEntrar }: { otId: string; ot: EstadoOt; onEntrar(): void }) {
  return (
    <Center mih="100vh" p="md">
      <Stack align="center" gap="lg" w="100%" maw={420}>
        <Text fw={900} size="2.5rem" lh={1}>
          {otId.toUpperCase()}
        </Text>
        <Stack gap={2} align="center">
          <Text fw={600} ta="center">
            {ot.pauta}
          </Text>
          <Text c="roca.6">{ot.equipo}</Text>
        </Stack>
        <Button size="xl" h={72} fullWidth leftSection={<IconVolume size={26} />} onClick={onEntrar}>
          {avance(ot).hechos === 0 ? 'Comenzar' : 'Continuar'}
        </Button>
        <Text size="sm" c="roca.6">
          Activa el audio para escuchar los avisos
        </Text>
      </Stack>
    </Center>
  )
}

/** «Entregar turno» pide confirmación en la misma pantalla, sin diálogos del navegador. */
function EntregarTurno({ onConfirmar }: { onConfirmar(): void }) {
  const [preguntando, setPreguntando] = useState(false)
  if (!preguntando)
    return (
      <Button variant="subtle" color="roca" onClick={() => setPreguntando(true)}>
        Entregar turno
      </Button>
    )
  return (
    <Group justify="space-between" wrap="nowrap">
      <Text fw={700}>¿Entregar el turno?</Text>
      <Group gap="xs" wrap="nowrap">
        <Button onClick={onConfirmar}>Confirmar</Button>
        <Button variant="default" onClick={() => setPreguntando(false)}>
          Cancelar
        </Button>
      </Group>
    </Group>
  )
}

function Ejecucion({ otId, usuario }: { otId: string; usuario: Usuario }) {
  const e = useEjecucion(otId, usuario)
  const navigate = useNavigate()
  const { s } = e
  const relevo = relevoPendiente(s.bitacora)
  const intentado = useRef(false)

  const vista =
    s.conexion === 'no_existe'
      ? 'no_existe'
      : !s.ot
        ? 'cargando'
        : s.ot.completa
          ? 'completa'
          : relevo && relevo.entregado_por !== usuario.id
            ? 'briefing'
            : !e.sesionAbierta && e.audio !== 'activo'
              ? 'puerta'
              : 'ejecucion'

  // Si el audio ya estaba desbloqueado (el toque de «Comenzar» en la lista), se entra sin otro toque.
  const { comenzar, sesionAbierta } = e
  useEffect(() => {
    if (vista === 'ejecucion' && !sesionAbierta && !intentado.current) {
      intentado.current = true
      void comenzar()
    }
  }, [vista, sesionAbierta, comenzar])

  const entrar = () => {
    intentado.current = true
    void comenzar()
  }

  /** La franja de conexión y el último error, también fuera de la pantalla de ejecución. */
  const conAvisos = (pantalla: ReactNode) => (
    <Box>
      {s.conexion === 'reconectando' && <FranjaSinConexion />}
      {s.mensaje && (
        <Container size={560} px="md" pt="md">
          <MensajeError mensaje={s.mensaje} onVisto={e.verMensaje} />
        </Container>
      )}
      {pantalla}
    </Box>
  )

  switch (vista) {
    case 'no_existe':
      return (
        <Center mih="100vh" p="md">
          <Stack align="center">
            <Text fw={800} size="xl">
              Esta OT no existe
            </Text>
            <Anchor component={Link} to="/operador">
              Volver a mis OT
            </Anchor>
          </Stack>
        </Center>
      )
    case 'cargando':
      return (
        <Center mih="100vh">
          <Loader />
        </Center>
      )
    case 'completa':
      return <OtCompleta ot={s.ot!} bitacora={s.bitacora} />
    case 'briefing':
      return conAvisos(
        <Briefing
          ot={s.ot!}
          bitacora={s.bitacora}
          alertas={s.alertas}
          relevo={relevo!}
          onRecibido={() => {
            intentado.current = true
            void e.recibirTurno()
          }}
        />,
      )
    case 'puerta':
      return conAvisos(<Puerta otId={otId} ot={s.ot!} onEntrar={entrar} />)
    case 'ejecucion':
      return (
        <PantallaEjecucion
          otId={otId}
          e={e}
          pie={
            <EntregarTurno
              onConfirmar={async () => {
                if (await e.entregarTurno()) navigate('/operador')
              }}
            />
          }
        />
      )
  }
}
