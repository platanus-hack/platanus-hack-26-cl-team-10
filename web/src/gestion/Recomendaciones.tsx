import { Alert, Button, Group, Paper, Stack, Text, TextInput } from '@mantine/core'
import { IconBulb, IconEye } from '@tabler/icons-react'
import { useState } from 'react'
import { Link } from 'react-router'
import { api } from '../api/cliente'
import type { Mejora } from '../api/tipos'
import { mensajeDe } from './useOts'

const rutaDe = (ot: string) => `/supervisor/ot/${encodeURIComponent(ot)}`

function Recomendacion({ m, onRevisada, onPosponer }: { m: Mejora; onRevisada: () => void; onPosponer: () => void }) {
  const [descartando, setDescartando] = useState(false)
  const [nota, setNota] = useState('')
  const [enviando, setEnviando] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const r = m.recurrencia
  const revisar = async (decision: 'aceptar' | 'descartar') => {
    setEnviando(true)
    setError(null)
    try {
      await api.revisarMejora(m.id, decision, decision === 'descartar' ? nota.trim() : '')
      onRevisada()
    } catch (e) {
      setError(mensajeDe(e))
    } finally {
      setEnviando(false)
    }
  }
  return (
    <Paper radius="sm" p="sm" aria-label={`Recomendación sobre ${m.titulo}`}>
      <Stack gap={6}>
        <Text fw={800}>
          «{m.titulo}» · {m.nombre} v{m.version}
        </Text>
        {m.tipo === 'conformidad' ? (
          <Text size="sm">{m.motivo}</Text>
        ) : (
          <Text size="sm">
            Se desvió en {r?.ots_con_senal ?? m.ots_con_senal} de {r?.ots ?? m.ejecuciones} OT, con {m.operarios_distintos}{' '}
            {m.operarios_distintos === 1 ? 'operario' : 'operarios distintos'}
            {m.control_critico ? '. Es un control crítico' : ''}. Factum lo detectó en la {m.detectada!.ot?.toUpperCase()}.
          </Text>
        )}
        <Text size="sm" c="roca.8">
          {m.sugerencia}
        </Text>
        {error && (
          <Alert color="peligro" variant="light" p="xs">
            {error}
          </Alert>
        )}
        {descartando ? (
          <Group align="flex-end" gap="sm">
            <TextInput
              label="Por qué la descartas"
              value={nota}
              onChange={(e) => setNota(e.currentTarget.value)}
              style={{ flex: 1 }}
              autoFocus
            />
            <Button color="roca" disabled={!nota.trim()} loading={enviando} onClick={() => void revisar('descartar')}>
              Descartar
            </Button>
            <Button variant="subtle" onClick={() => setDescartando(false)}>
              Volver
            </Button>
          </Group>
        ) : (
          <Group gap="sm">
            <Button color="accion" loading={enviando} onClick={() => void revisar('aceptar')}>
              {m.aplicable ? 'Aplicar la recomendación' : 'Aceptar la recomendación'}
            </Button>
            <Button variant="default" onClick={() => setDescartando(true)}>
              Descartar
            </Button>
            {m.detectada!.ot ? (
              <Button
                component={Link}
                to={rutaDe(m.detectada!.ot)}
                variant="default"
                leftSection={<IconEye size={16} />}
                aria-label={`Ver ${m.detectada!.ot}`}
              >
                Ver la OT
              </Button>
            ) : (
              <Button component={Link} to="/supervisor/mejoras" variant="default" leftSection={<IconEye size={16} />}>
                Ver en mejoras
              </Button>
            )}
            <Button variant="subtle" onClick={onPosponer}>
              Más tarde
            </Button>
          </Group>
        )}
      </Stack>
    </Paper>
  )
}

/** Lo que Factum recomienda cambiar en una pauta, apenas ve que un paso se repite. Aceptarla la manda al equipo de Factum. */
export function Recomendaciones({
  recomendaciones,
  quitar,
}: {
  recomendaciones: Mejora[]
  quitar: (id: string) => void
}) {
  const [pospuestas, setPospuestas] = useState<Set<string>>(new Set())
  const visibles = recomendaciones.filter((m) => !pospuestas.has(m.id))
  if (visibles.length === 0) return null
  return (
    <Paper
      radius="md"
      p="md"
      bg="precaucion.0"
      role="region"
      aria-label="Recomendaciones de Factum"
      style={{ borderLeft: '4px solid var(--mantine-color-precaucion-6)' }}
    >
      <Stack gap="sm">
        <Group gap="xs">
          <IconBulb size={24} />
          <Text fw={900} size="lg">
            {visibles.length === 1 ? 'Factum encontró un patrón' : `Factum encontró ${visibles.length} patrones`}
          </Text>
        </Group>
        {visibles.map((m) => (
          <Recomendacion
            key={m.id}
            m={m}
            onRevisada={() => quitar(m.id)}
            onPosponer={() => setPospuestas((s) => new Set(s).add(m.id))}
          />
        ))}
      </Stack>
    </Paper>
  )
}
