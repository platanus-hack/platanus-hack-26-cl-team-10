import { Alert, Button, Card, Group, Modal, Paper, Progress, Radio, SimpleGrid, Stack, Table, Text, Title } from '@mantine/core'
import { useMediaQuery } from '@mantine/hooks'
import { IconPlus, IconRefresh } from '@tabler/icons-react'
import { useCallback, useEffect, useState } from 'react'
import { api } from '../api/cliente'
import type { EstadoGeneral, OtPedida, PautaResumen, Persona } from '../api/tipos'
import { useSesion } from '../sesion/sesion'
import { nombreDe, recordarNombres } from '../sesion/usuarios'
import { ESTADOS, porPrioridad, puedeAsignarse } from './estados'
import { EstadoBadge, Encabezado, EstadoLista, FranjaDesactualizada, Pagina } from './ui'
import { mensajeDe, useOts, type OtVista } from './useOts'

/** Los operadores de la empresa (`GET /cliente/operadores`), con sus nombres para toda la pantalla. */
function useOperadores() {
  const [operadores, setOperadores] = useState<Persona[] | null>(null)
  const [error, setError] = useState<string | null>(null)
  const recargar = useCallback(async () => {
    try {
      const ps = await api.listarOperadores()
      recordarNombres(ps)
      setOperadores(ps)
      setError(null)
    } catch (e) {
      setError(mensajeDe(e))
    }
  }, [])
  useEffect(() => {
    void Promise.resolve().then(recargar)
  }, [recargar])
  return { operadores, error, recargar }
}

type Operadores = { lista: Persona[] | null; error: string | null }

const CONTADORES: { titulo: string; estados: EstadoGeneral[]; color: string }[] = [
  { titulo: 'Por asignar', estados: ['sin_asignar'], color: 'roca' },
  { titulo: 'Entregadas', estados: ['entregada'], color: 'precaucion' },
  { titulo: 'En curso', estados: ['asignada', 'en_ejecucion'], color: 'accion' },
  { titulo: 'Completas', estados: ['completa'], color: 'verificado' },
]

function Contadores({ ots }: { ots: OtVista[] }) {
  return (
    <SimpleGrid cols={{ base: 2, sm: 4 }} spacing="sm">
      {CONTADORES.map((c) => {
        const n = ots.filter((o) => c.estados.includes(o.estado)).length
        return (
          <Paper
            key={c.titulo}
            withBorder
            radius="md"
            p="md"
            style={{ borderLeft: `4px solid var(--mantine-color-${c.color}-6)` }}
          >
            <Text size="sm" c="roca.7" fw={600}>
              {c.titulo}
            </Text>
            <Text fw={900} size="xl" aria-label={`${c.titulo}: ${n}`}>
              {n}
            </Text>
          </Paper>
        )
      })}
    </SimpleGrid>
  )
}

function Avance({ ot }: { ot: OtVista }) {
  const a = ot.avance
  if (!a) return <Text c="roca.6">—</Text>
  return (
    <Stack gap={4} miw={110}>
      <Text size="sm" fw={700}>
        {a.cerrados}/{a.total} pasos
      </Text>
      <Progress
        value={a.total ? (a.cerrados / a.total) * 100 : 0}
        color={ESTADOS[ot.estado].color}
        size="sm"
        aria-label={`Avance de ${ot.ot}: ${a.cerrados} de ${a.total}`}
      />
    </Stack>
  )
}

function Operador({ ot }: { ot: OtVista }) {
  if (ot.operador) return <Text fw={600}>{nombreDe(ot.operador)}</Text>
  const entregado = ot.entregada_por ? `Turno entregado por ${nombreDe(ot.entregada_por)}` : 'Turno entregado'
  return (
    <Text c="roca.6" fs="italic">
      {ot.estado === 'entregada' ? entregado : 'Nadie'}
    </Text>
  )
}

/** Un botón por operador de la empresa: con dos en el demo, asignar es un solo clic. */
function Asignar({ ot, operadores, onListo }: { ot: OtVista; operadores: Operadores; onListo: () => Promise<void> }) {
  const [enviando, setEnviando] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  if (!puedeAsignarse(ot.estado)) return <Text c="roca.6">—</Text>
  if (!operadores.lista) {
    return (
      <Text size="sm" c={operadores.error ? 'peligro' : 'roca.6'}>
        {operadores.error ? 'No se pudo cargar a los operadores' : 'Cargando operadores…'}
      </Text>
    )
  }

  const asignar = async (operador: string) => {
    setEnviando(operador)
    setError(null)
    try {
      // Quién asigna lo sabe la API por el token, y queda en la bitácora de la OT.
      await api.asignar(ot.ot, operador)
      await onListo()
    } catch (e) {
      setError(mensajeDe(e))
      // Un 409 suele decir que la OT cambió (otra pestaña u otro supervisor): se trae lo último.
      await onListo()
    } finally {
      setEnviando(null)
    }
  }

  const verbo = ot.estado === 'entregada' ? 'Reasignar' : 'Asignar'
  return (
    <Stack gap={4}>
      <Group gap={6}>
        <Text size="sm" fw={600} c="roca.7">
          {verbo} a
        </Text>
        {operadores.lista.map((u) => (
          <Button
            key={u.id}
            size="xs"
            loading={enviando === u.id}
            disabled={enviando !== null && enviando !== u.id}
            onClick={() => void asignar(u.id)}
            aria-label={`${verbo} ${ot.ot} a ${u.nombre}`}
          >
            {u.nombre}
          </Button>
        ))}
      </Group>
      {error && (
        <Text size="sm" c="peligro" role="alert">
          {error}
        </Text>
      )}
    </Stack>
  )
}

/** El id, el estado y el nombre se leen de un vistazo: no se parten en dos líneas. */
const SIN_CORTE = { whiteSpace: 'nowrap' } as const

function Tabla({ ots, operadores, onListo }: { ots: OtVista[]; operadores: Operadores; onListo: () => Promise<void> }) {
  return (
    <Paper withBorder radius="md">
      <Table verticalSpacing="sm" horizontalSpacing="md" highlightOnHover>
        <Table.Thead>
          <Table.Tr>
            <Table.Th>OT</Table.Th>
            <Table.Th>Pauta y equipo</Table.Th>
            <Table.Th>Estado</Table.Th>
            <Table.Th>Operador</Table.Th>
            <Table.Th>Avance</Table.Th>
            <Table.Th>Acción</Table.Th>
          </Table.Tr>
        </Table.Thead>
        <Table.Tbody>
          {ots.map((o) => (
            <Table.Tr key={o.ot}>
              <Table.Td style={SIN_CORTE}>
                <Text fw={800}>{o.ot.toUpperCase()}</Text>
              </Table.Td>
              <Table.Td>
                <Text fw={600}>{o.avance?.nombre ?? o.pauta}</Text>
                <Text size="sm" c="roca.6">
                  {o.equipo}
                </Text>
              </Table.Td>
              <Table.Td style={SIN_CORTE}>
                <EstadoBadge estado={o.estado} />
              </Table.Td>
              <Table.Td style={SIN_CORTE}>
                <Operador ot={o} />
              </Table.Td>
              <Table.Td>
                <Avance ot={o} />
              </Table.Td>
              <Table.Td>
                <Asignar ot={o} operadores={operadores} onListo={onListo} />
              </Table.Td>
            </Table.Tr>
          ))}
        </Table.Tbody>
      </Table>
    </Paper>
  )
}

function Tarjetas({ ots, operadores, onListo }: { ots: OtVista[]; operadores: Operadores; onListo: () => Promise<void> }) {
  return (
    <Stack gap="sm">
      {ots.map((o) => (
        <Card key={o.ot} withBorder radius="md" padding="md">
          <Stack gap="sm">
            <Group justify="space-between" wrap="nowrap">
              <Text fw={800}>{o.ot.toUpperCase()}</Text>
              <EstadoBadge estado={o.estado} />
            </Group>
            <div>
              <Text fw={600}>{o.avance?.nombre ?? o.pauta}</Text>
              <Text size="sm" c="roca.6">
                {o.equipo}
              </Text>
            </div>
            <Group justify="space-between" align="flex-start">
              <Operador ot={o} />
              <Avance ot={o} />
            </Group>
            {puedeAsignarse(o.estado) && <Asignar ot={o} operadores={operadores} onListo={onListo} />}
          </Stack>
        </Card>
      ))}
    </Stack>
  )
}

/** El supervisor pide una OT de una de las pautas de su empresa; nace sin operador. */
function PedirOt({ onPedida }: { onPedida: (o: OtPedida) => Promise<void> }) {
  const [abierto, setAbierto] = useState(false)
  const [pautas, setPautas] = useState<PautaResumen[] | null>(null)
  const [elegida, setElegida] = useState<string | null>(null)
  const [enviando, setEnviando] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const abrir = () => {
    setAbierto(true)
    setElegida(null)
    setError(null)
    api.listarPautas().then(setPautas, (e: unknown) => setError(mensajeDe(e)))
  }

  const pedir = async () => {
    if (!elegida) return
    setEnviando(true)
    setError(null)
    try {
      const o = await api.pedirOt(elegida)
      setAbierto(false)
      await onPedida(o)
    } catch (e) {
      setError(mensajeDe(e))
    } finally {
      setEnviando(false)
    }
  }

  return (
    <>
      <Button leftSection={<IconPlus size={16} />} onClick={abrir}>
        Pedir OT
      </Button>
      <Modal opened={abierto} onClose={() => setAbierto(false)} title="Pedir una OT" centered size="lg">
        <Stack gap="md">
          <Text c="roca.7">Elige qué trabajo hay que hacer. La OT queda por asignar.</Text>
          {pautas === null && !error && <Text c="roca.6">Cargando pautas…</Text>}
          {pautas && pautas.length === 0 && <Text c="roca.6">Tu empresa no tiene pautas habilitadas.</Text>}
          {pautas && pautas.length > 0 && (
            <Radio.Group value={elegida} onChange={setElegida} label="Pauta" name="pauta">
              <Stack gap="sm" mt="xs">
                {pautas.map((p) => (
                  <Radio key={p.id} value={p.id} label={p.nombre} description={`${p.equipo}, ${p.pasos} pasos`} />
                ))}
              </Stack>
            </Radio.Group>
          )}
          {error && (
            <Text c="peligro" role="alert">
              {error}
            </Text>
          )}
          <Group justify="flex-end">
            <Button variant="default" onClick={() => setAbierto(false)}>
              Cancelar
            </Button>
            <Button onClick={() => void pedir()} loading={enviando} disabled={!elegida}>
              Pedir esta OT
            </Button>
          </Group>
        </Stack>
      </Modal>
    </>
  )
}

export function PaginaSupervisor() {
  const usuario = useSesion()
  const { ots, error, recargar } = useOts()
  const operadores = useOperadores()
  const [pedida, setPedida] = useState<OtPedida | null>(null)
  const ancha = useMediaQuery('(min-width: 62em)', undefined, { getInitialValueInEffect: false })
  if (!usuario) return null

  const lista = porPrioridad(ots ?? [])
  const deOperadores: Operadores = { lista: operadores.operadores, error: operadores.error }
  const actualizar = () => {
    void recargar()
    if (!operadores.operadores) void operadores.recargar()
  }
  const alPedir = async (o: OtPedida) => {
    setPedida(o)
    await recargar()
  }

  return (
    <>
      <Encabezado usuario={usuario} seccion="Supervisión" />
      <FranjaDesactualizada error={ots ? error : null} />
      <Pagina>
        <Stack gap="lg">
          <Group justify="space-between">
            <Title order={2}>Órdenes de trabajo</Title>
            <Group gap="sm">
              <Button variant="default" leftSection={<IconRefresh size={16} />} onClick={actualizar}>
                Actualizar
              </Button>
              <PedirOt onPedida={alPedir} />
            </Group>
          </Group>
          {pedida && (
            <Alert color="verificado" variant="light" withCloseButton onClose={() => setPedida(null)} closeButtonLabel="Cerrar aviso">
              Pediste la {pedida.ot.toUpperCase()}, {pedida.nombre}. Queda por asignar.
            </Alert>
          )}
          {ots && <Contadores ots={ots} />}
          <EstadoLista
            cargando={ots === null}
            error={error}
            vacia={lista.length === 0}
            textoVacia="No hay órdenes de trabajo abiertas."
            onReintentar={() => void recargar()}
          />
          {lista.length > 0 &&
            (ancha ? (
              <Tabla ots={lista} operadores={deOperadores} onListo={recargar} />
            ) : (
              <Tarjetas ots={lista} operadores={deOperadores} onListo={recargar} />
            ))}
        </Stack>
      </Pagina>
    </>
  )
}
