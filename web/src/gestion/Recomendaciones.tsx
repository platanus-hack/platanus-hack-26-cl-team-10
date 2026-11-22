import { Anchor, Box, Button, CloseButton, Group, Paper, Stack, Text } from '@mantine/core'
import { IconBulb, IconEye } from '@tabler/icons-react'
import { useState } from 'react'
import { Link } from 'react-router'
import type { Mejora } from '../api/tipos'
import { Decidir, VistaBorrador } from './PaginaMejoras'

const rutaDe = (ot: string) => `/supervisor/ot/${encodeURIComponent(ot)}`
const lista = (xs: string[]) => xs.map((x) => `«${x}»`).join(' y ')

/** Qué le pasa a la pauta y por qué importa, en las palabras del supervisor: sin ids de protocolo ni de control. */
function enPalabras(m: Mejora): { que: string; porque: string } {
  const c = m.conformidad
  const nombres = c?.nombres ?? []
  if (c && c.tipo === 'falta' && nombres.length)
    return { que: `Falta el paso ${lista(nombres)}`, porque: 'El protocolo lo exige y hoy ningún paso de la pauta lo hace.' }
  if (c && c.tipo === 'juntos' && nombres.length)
    return {
      que: `${lista(nombres)} van en un mismo paso`,
      porque: 'Separados, la evidencia comprueba que se hizo cada uno y en su orden.',
    }
  if (c && c.tipo === 'orden' && nombres.length === 2)
    return { que: `«${nombres[1]}» va antes que «${nombres[0]}»`, porque: 'El protocolo los pide en el orden contrario.' }
  if (c) return { que: m.titulo, porque: m.sugerencia }
  const r = m.recurrencia
  const operarios = m.operarios_distintos === 1 ? '1 operario' : `${m.operarios_distintos} operarios distintos`
  return {
    que: `«${m.titulo}» se está desviando`,
    porque: `Se desvió en ${r?.ots_con_senal ?? m.ots_con_senal} de ${r?.ots ?? m.ejecuciones} OT, con ${operarios}${
      m.control_critico ? '. Es un control crítico' : ''
    }.`,
  }
}

function Fila({ m, onRevisada, onPosponer }: { m: Mejora; onRevisada: () => void; onPosponer: () => void }) {
  const [abierta, setAbierta] = useState(false)
  const { que, porque } = enPalabras(m)
  return (
    <Box py="sm" style={{ borderTop: '1px solid var(--mantine-color-default-border)' }} aria-label={que} role="group">
      <Group justify="space-between" align="flex-start" wrap="nowrap" gap="sm">
        <Box style={{ minWidth: 0 }}>
          <Text fw={700}>{que}</Text>
          <Text size="sm" c="dimmed">
            {porque}
          </Text>
        </Box>
        <Group gap={4} wrap="nowrap">
          <Button size="xs" variant={abierta ? 'default' : 'light'} onClick={() => setAbierta((a) => !a)} aria-expanded={abierta}>
            {abierta ? 'Cerrar' : 'Revisar'}
          </Button>
          <CloseButton aria-label={`Más tarde: ${que}`} title="Más tarde" onClick={onPosponer} />
        </Group>
      </Group>
      {abierta && (
        <Stack gap="sm" mt="sm">
          {m.aplicable ? (
            <VistaBorrador propuesta={m.id} />
          ) : (
            <Text size="sm">{m.por_que_no ?? m.sugerencia}</Text>
          )}
          <Group gap="sm" align="flex-start" justify="space-between">
            <Decidir p={m} alDecidir={onRevisada} />
            {m.detectada?.ot && (
              <Button
                component={Link}
                to={rutaDe(m.detectada.ot)}
                variant="subtle"
                size="xs"
                leftSection={<IconEye size={16} />}
                aria-label={`Ver ${m.detectada.ot}`}
              >
                Ver la OT donde se vio
              </Button>
            )}
          </Group>
        </Stack>
      )}
    </Box>
  )
}

/**
 * Lo que Factum sugiere cambiar en las pautas: las faltas frente a su protocolo y los pasos que se desvían seguido.
 * Agrupadas por pauta; cada una se revisa con su cambio a la vista antes de aplicarla. Aplicar la manda a Factum.
 */
export function Recomendaciones({ recomendaciones, quitar }: { recomendaciones: Mejora[]; quitar: (id: string) => void }) {
  const [pospuestas, setPospuestas] = useState<Set<string>>(new Set())
  const [abierta, setAbierta] = useState(true)
  const visibles = recomendaciones.filter((m) => !pospuestas.has(m.id))
  if (visibles.length === 0) return null

  const grupos = new Map<string, Mejora[]>()
  for (const m of visibles) {
    const clave = `${m.nombre} · v${m.version}`
    grupos.set(clave, [...(grupos.get(clave) ?? []), m])
  }
  const n = visibles.length
  return (
    <Paper
      withBorder
      radius="md"
      p="md"
      role="region"
      aria-label="Recomendaciones de Factum"
      style={{ borderLeft: '4px solid var(--mantine-color-precaucion-6)' }}
    >
      <Group justify="space-between" wrap="nowrap" align="flex-start">
        <Group gap="sm" wrap="nowrap" align="flex-start">
          <IconBulb size={24} color="var(--mantine-color-precaucion-5)" style={{ flexShrink: 0 }} />
          <Box>
            <Text fw={800} size="lg">
              {n === 1 ? 'Factum sugiere una mejora a tus pautas' : `Factum sugiere ${n} mejoras a tus pautas`}
            </Text>
            <Text size="sm" c="dimmed">
              Ninguna cambia la pauta sola: revisa el cambio y, si lo aplicas, Factum arma la versión nueva.
            </Text>
          </Box>
        </Group>
        <Group gap="xs" wrap="nowrap">
          <Anchor component={Link} to="/supervisor/mejoras" size="sm">
            Ver todas
          </Anchor>
          <Button variant="subtle" size="xs" onClick={() => setAbierta((a) => !a)} aria-expanded={abierta}>
            {abierta ? 'Ocultar' : 'Mostrar'}
          </Button>
        </Group>
      </Group>
      {abierta &&
        [...grupos].map(([pauta, ms]) => (
          <Box key={pauta} mt="md">
            <Text size="xs" fw={700} c="dimmed" tt="uppercase" mb={4}>
              {pauta}
            </Text>
            {ms.map((m) => (
              <Fila
                key={m.id}
                m={m}
                onRevisada={() => quitar(m.id)}
                onPosponer={() => setPospuestas((s) => new Set(s).add(m.id))}
              />
            ))}
          </Box>
        ))}
    </Paper>
  )
}
