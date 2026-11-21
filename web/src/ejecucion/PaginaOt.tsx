import { Anchor, Button, Center, Loader, Stack, Text } from '@mantine/core'
import { IconVolume } from '@tabler/icons-react'
import { useEffect, useRef } from 'react'
import { Link, useParams } from 'react-router'
import type { EstadoOt } from '../api/tipos'
import { useSesion } from '../sesion/sesion'
import type { Usuario } from '../sesion/usuarios'
import { avance, relevoPendiente } from './estado'
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

function Ejecucion({ otId, usuario }: { otId: string; usuario: Usuario }) {
  const e = useEjecucion(otId, usuario)
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
      return (
        <Center mih="100vh">
          <Text fw={800} size="xl">
            OT completa
          </Text>
        </Center>
      )
    case 'briefing':
    case 'puerta':
      return <Puerta otId={otId} ot={s.ot!} onEntrar={entrar} />
    case 'ejecucion':
      return <PantallaEjecucion otId={otId} e={e} />
  }
}
