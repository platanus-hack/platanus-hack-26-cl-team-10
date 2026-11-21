import { Box, Button, Center, Container, Group, Loader, Paper, Stack, Text, Title } from '@mantine/core'
import { IconArrowsExchange, IconVolume } from '@tabler/icons-react'
import { useEffect, useRef, useState, type ReactNode } from 'react'
import { Link, useNavigate, useParams } from 'react-router'
import type { EstadoOt } from '../api/tipos'
import { useSesion } from '../sesion/sesion'
import type { Usuario } from '../sesion/usuarios'
import { FranjaSinConexion, MensajeError } from './Avisos'
import { BarraOt } from './BarraOt'
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
    <Container size={420} px="md" py={48}>
      <Stack align="center" gap="lg">
        <Text fw={900} size="2.5rem" lh={1}>
          {otId.toUpperCase()}
        </Text>
        <Stack gap={2} align="center">
          <Text fw={600} ta="center">
            {ot.pauta}
          </Text>
          <Text c="roca.6">Equipo {ot.equipo}</Text>
        </Stack>
        <Button size="xl" h={72} fullWidth leftSection={<IconVolume size={26} />} onClick={onEntrar}>
          {avance(ot).hechos === 0 ? 'Comenzar' : 'Continuar'}
        </Button>
        <Text size="sm" c="roca.6" ta="center">
          Activa el audio para escuchar los avisos
        </Text>
      </Stack>
    </Container>
  )
}

/** «Entregar turno» pide confirmación en la misma pantalla, sin diálogos del navegador. */
function EntregarTurno({ onConfirmar, habilitado }: { onConfirmar(): void; habilitado: boolean }) {
  const [preguntando, setPreguntando] = useState(false)
  if (!preguntando)
    return (
      <Button variant="default" size="md" fullWidth leftSection={<IconArrowsExchange size={18} />} disabled={!habilitado} onClick={() => setPreguntando(true)}>
        Entregar turno
      </Button>
    )
  return (
    <Paper withBorder p="sm" bg="white">
      <Stack gap="xs">
        <Text fw={700}>¿Entregar el turno?</Text>
        <Text size="sm" c="roca.7">
          La OT queda esperando que el supervisor la reasigne. Quien la reciba sigue desde el paso actual.
        </Text>
        <Group grow>
          <Button disabled={!habilitado} onClick={onConfirmar}>
            Confirmar
          </Button>
          <Button variant="default" onClick={() => setPreguntando(false)}>
            Cancelar
          </Button>
        </Group>
      </Stack>
    </Paper>
  )
}

function Ejecucion({ otId, usuario }: { otId: string; usuario: Usuario }) {
  const e = useEjecucion(otId, usuario)
  const navigate = useNavigate()
  const { s } = e
  const relevo = relevoPendiente(s.bitacora)
  const intentado = useRef(false)

  const vista =
    s.conexion === 'no_existe' || e.acceso === 'denegado'
      ? 'no_existe'
      : !s.ot || e.acceso === 'verificando'
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

  /** La barra, la franja de conexión y el último error, en todas las pantallas de la OT. */
  const conBarra = (pantalla: ReactNode) => (
    <Box>
      <BarraOt usuario={usuario} />
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
      return conBarra(
        <Center py={64} px="md">
          <Stack align="center" gap="sm">
            <Title order={2}>Esta OT no está en tu lista</Title>
            <Text c="roca.6" ta="center">
              No existe o no está asignada a ti. Revisa el enlace o vuelve a tu lista.
            </Text>
            <Button component={Link} to="/operador" variant="default">
              Volver a mis OT
            </Button>
          </Stack>
        </Center>,
      )
    case 'cargando':
      return conBarra(
        <Center py={64}>
          <Stack align="center" gap="xs">
            <Loader />
            <Text c="roca.6">{s.conexion === 'reconectando' ? 'Esperando a la API…' : 'Cargando la OT…'}</Text>
          </Stack>
        </Center>,
      )
    case 'completa':
      return conBarra(<OtCompleta ot={s.ot!} bitacora={s.bitacora} />)
    case 'briefing':
      return conBarra(
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
      return conBarra(<Puerta otId={otId} ot={s.ot!} onEntrar={entrar} />)
    case 'ejecucion':
      return (
        <PantallaEjecucion
          otId={otId}
          usuario={usuario}
          e={e}
          pie={
            <EntregarTurno
              habilitado={s.conexion === 'en_vivo'}
              onConfirmar={async () => {
                if (await e.entregarTurno()) navigate('/operador')
              }}
            />
          }
        />
      )
  }
}
