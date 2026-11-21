import { Button, Card, Group, Paper, Progress, SimpleGrid, Stack, Table, Text, Title } from '@mantine/core'
import { useMediaQuery } from '@mantine/hooks'
import { IconRefresh } from '@tabler/icons-react'
import { useState } from 'react'
import { api } from '../api/cliente'
import type { EstadoGeneral } from '../api/tipos'
import { useSesion } from '../sesion/sesion'
import { USUARIOS, nombreDe } from '../sesion/usuarios'
import { ESTADOS, porPrioridad, puedeAsignarse } from './estados'
import { EstadoBadge, Encabezado, EstadoLista, FranjaDesactualizada, Pagina } from './ui'
import { mensajeDe, useOts, type OtVista } from './useOts'

const OPERADORES = USUARIOS.filter((u) => u.rol === 'operador')

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
  return (
    <Text c="roca.6" fs="italic">
      {ot.estado === 'entregada' ? 'Turno entregado' : 'Nadie'}
    </Text>
  )
}

/** Un botón por operador: con dos en el demo, asignar es un solo clic. */
function Asignar({ ot, onListo }: { ot: OtVista; onListo: () => Promise<void> }) {
  const [enviando, setEnviando] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  if (!puedeAsignarse(ot.estado)) return <Text c="roca.6">—</Text>

  const asignar = async (operador: string) => {
    setEnviando(operador)
    setError(null)
    try {
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
      <Group gap={6} wrap="nowrap">
        <Text size="sm" fw={600} c="roca.7">
          {verbo} a
        </Text>
        {OPERADORES.map((u) => (
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

function Tabla({ ots, onListo }: { ots: OtVista[]; onListo: () => Promise<void> }) {
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
              <Table.Td>
                <Text fw={800}>{o.ot.toUpperCase()}</Text>
              </Table.Td>
              <Table.Td>
                <Text fw={600}>{o.avance?.nombre ?? o.pauta}</Text>
                <Text size="sm" c="roca.6">
                  {o.equipo}
                </Text>
              </Table.Td>
              <Table.Td>
                <EstadoBadge estado={o.estado} />
              </Table.Td>
              <Table.Td>
                <Operador ot={o} />
              </Table.Td>
              <Table.Td>
                <Avance ot={o} />
              </Table.Td>
              <Table.Td>
                <Asignar ot={o} onListo={onListo} />
              </Table.Td>
            </Table.Tr>
          ))}
        </Table.Tbody>
      </Table>
    </Paper>
  )
}

function Tarjetas({ ots, onListo }: { ots: OtVista[]; onListo: () => Promise<void> }) {
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
            {puedeAsignarse(o.estado) && <Asignar ot={o} onListo={onListo} />}
          </Stack>
        </Card>
      ))}
    </Stack>
  )
}

export function PaginaSupervisor() {
  const usuario = useSesion()
  const { ots, error, recargar } = useOts()
  const ancha = useMediaQuery('(min-width: 62em)', undefined, { getInitialValueInEffect: false })
  if (!usuario) return null

  const lista = porPrioridad(ots ?? [])
  return (
    <>
      <Encabezado usuario={usuario} seccion="Supervisión" />
      <FranjaDesactualizada error={ots ? error : null} />
      <Pagina>
        <Stack gap="lg">
          <Group justify="space-between">
            <Title order={2}>Órdenes de trabajo</Title>
            <Button variant="default" leftSection={<IconRefresh size={16} />} onClick={() => void recargar()}>
              Actualizar
            </Button>
          </Group>
          {ots && <Contadores ots={ots} />}
          <EstadoLista
            cargando={ots === null}
            error={error}
            vacia={lista.length === 0}
            textoVacia="No hay órdenes de trabajo abiertas."
            onReintentar={() => void recargar()}
          />
          {lista.length > 0 &&
            (ancha ? <Tabla ots={lista} onListo={recargar} /> : <Tarjetas ots={lista} onListo={recargar} />)}
        </Stack>
      </Pagina>
    </>
  )
}
