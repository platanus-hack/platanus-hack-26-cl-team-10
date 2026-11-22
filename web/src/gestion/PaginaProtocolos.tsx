import { Alert, Button, Group, Paper, Stack, Table, Text, TextInput, Title, VisuallyHidden } from '@mantine/core'
import { IconListDetails, IconSearch } from '@tabler/icons-react'
import { useEffect, useState } from 'react'
import { Link } from 'react-router'
import { api } from '../api/cliente'
import type { PautaResumen } from '../api/tipos'
import { useSesion } from '../sesion/sesion'
import { avisoDe } from './estados'
import industrial from './industrial.module.css'
import { Encabezado, Pagina } from './ui'
import { mensajeDe, useOts, type OtVista } from './useOts'

type Protocolo = { id: string; nombre: string; pautas: PautaResumen[] }

/** Las pautas habilitadas, agrupadas por los protocolos de los que salen. Una pauta de dos protocolos va en los dos. */
function porProtocolo(pautas: PautaResumen[]): Protocolo[] {
  const grupos = new Map<string, Protocolo>()
  for (const p of pautas) {
    for (const pr of p.protocolos) {
      const g = grupos.get(pr.id) ?? { id: pr.id, nombre: pr.nombre, pautas: [] }
      g.pautas.push(p)
      grupos.set(pr.id, g)
    }
  }
  return [...grupos.values()].sort((a, b) => a.nombre.localeCompare(b.nombre))
}

/** Cómo van las OT de una pauta, en pocas palabras. */
function comoVan(ots: OtVista[]): string {
  if (ots.length === 0) return 'Sin OT todavía'
  const enCurso = ots.filter((o) => o.estado === 'en_ejecucion')
  const conAlerta = enCurso.filter((o) => avisoDe(o)).length
  const completas = ots.filter((o) => o.estado === 'completa').length
  const pendientes = ots.length - enCurso.length - completas
  return [
    enCurso.length ? `${enCurso.length} en curso` : null,
    conAlerta ? `${conAlerta} con alerta` : null,
    pendientes ? `${pendientes} por empezar` : null,
    completas ? `${completas} ${completas === 1 ? 'completa' : 'completas'}` : null,
  ]
    .filter(Boolean)
    .join(' · ')
}

function TablaDePautas({ pautas, ots }: { pautas: PautaResumen[]; ots: OtVista[] }) {
  return (
    <Table.ScrollContainer minWidth={640}>
      <Table verticalSpacing="sm">
        <Table.Thead>
          <Table.Tr>
            <Table.Th className={industrial.rotulo}>Pauta</Table.Th>
            <Table.Th className={industrial.rotulo}>Equipo</Table.Th>
            <Table.Th className={industrial.rotulo}>Sus OT</Table.Th>
            <Table.Th />
          </Table.Tr>
        </Table.Thead>
        <Table.Tbody>
          {pautas.map((p) => {
            const deEsta = ots.filter((o) => o.pauta === p.id)
            return (
              <Table.Tr key={p.id}>
                <Table.Td>
                  <Text fw={600}>{p.nombre}</Text>
                  <Text size="xs" c="dimmed">
                    Versión {p.version} · {p.pasos} pasos
                  </Text>
                </Table.Td>
                <Table.Td>
                  <Text size="sm">{p.equipo}</Text>
                </Table.Td>
                <Table.Td>
                  <Text size="sm" c={deEsta.some((o) => o.estado === 'en_ejecucion' && avisoDe(o)) ? 'peligro.7' : undefined}>
                    {comoVan(deEsta)}
                  </Text>
                </Table.Td>
                <Table.Td w={150}>
                  <Button
                    component={Link}
                    to={`/supervisor?pauta=${encodeURIComponent(p.id)}`}
                    variant="default"
                    size="xs"
                    leftSection={<IconListDetails size={16} />}
                    aria-label={`Ver las OT de ${p.nombre}`}
                  >
                    Ver sus OT
                  </Button>
                </Table.Td>
              </Table.Tr>
            )
          })}
        </Table.Tbody>
      </Table>
    </Table.ScrollContainer>
  )
}

/** /supervisor/protocolos — cada protocolo de la empresa con sus pautas, y de cada pauta, cómo van sus OT. */
export function PaginaProtocolos() {
  const usuario = useSesion()
  const { ots } = useOts()
  const [pautas, setPautas] = useState<PautaResumen[] | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [busca, setBusca] = useState('')

  useEffect(() => {
    api.listarPautas().then(setPautas, (e: unknown) => setError(mensajeDe(e)))
  }, [])
  if (!usuario) return null

  const q = busca.trim().toLowerCase()
  const protocolos = porProtocolo(pautas ?? [])
    .map((pr) => ({
      ...pr,
      pautas: pr.nombre.toLowerCase().includes(q) ? pr.pautas : pr.pautas.filter((p) => [p.nombre, p.equipo].some((t) => t.toLowerCase().includes(q))),
    }))
    .filter((pr) => pr.pautas.length > 0)

  return (
    <>
      <Encabezado usuario={usuario} seccion="Protocolos" />
      <Pagina>
        <Stack gap="lg">
          <Group justify="space-between" align="center">
            <VisuallyHidden>
              <Title order={2}>Protocolos</Title>
            </VisuallyHidden>
            <span />
            <TextInput
              aria-label="Buscar protocolo, pauta o equipo"
              placeholder="Buscar protocolo, pauta o equipo"
              leftSection={<IconSearch size={16} />}
              value={busca}
              onChange={(e) => setBusca(e.currentTarget.value)}
              w={{ base: '100%', sm: 300 }}
            />
          </Group>
          {error && (
            <Alert color="peligro" variant="light">
              {error}
            </Alert>
          )}
          {pautas && protocolos.length === 0 && (
            <Text c="dimmed">{q ? 'Nada coincide con la búsqueda.' : 'Tu empresa todavía no tiene pautas habilitadas.'}</Text>
          )}
          {protocolos.map((pr) => (
            <Paper key={pr.id} component="section" aria-label={pr.nombre} withBorder radius="md" p="md">
              <Group justify="space-between" mb="xs">
                <Text fw={800}>{pr.nombre}</Text>
                <Text size="sm" c="dimmed">
                  {pr.pautas.length === 1 ? '1 pauta' : `${pr.pautas.length} pautas`}
                </Text>
              </Group>
              <TablaDePautas pautas={pr.pautas} ots={ots ?? []} />
            </Paper>
          ))}
        </Stack>
      </Pagina>
    </>
  )
}
