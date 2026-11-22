import { Alert, Anchor, Box, Button, Group, List, Paper, Stack, Text } from '@mantine/core'
import { IconBulb, IconCheck } from '@tabler/icons-react'
import { useState } from 'react'
import { Link } from 'react-router'
import { api } from '../api/cliente'
import type { ResumenMejoras } from '../api/tipos'
import { mensajeDe } from './useOts'

function Linea({ que, porque }: { que: string; porque: string | null }) {
  return (
    <List.Item>
      <Text size="sm" fw={600}>
        {que}
      </Text>
      {porque && (
        <Text size="sm" c="dimmed">
          {porque}
        </Text>
      )}
    </List.Item>
  )
}

/** Una pauta: la versión que Factum armaría, qué cambia y por qué, qué no y por qué no, y un solo botón. */
function Propuesta({ r, onAplicada, onPosponer }: { r: ResumenMejoras; onAplicada: (texto: string) => void; onPosponer: () => void }) {
  const [enviando, setEnviando] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const n = r.cambios.length

  const aplicar = async () => {
    setEnviando(true)
    setError(null)
    try {
      const a = await api.aplicarMejoras(r.pauta)
      onAplicada(
        a.version
          ? `Listo. Factum armó la versión ${a.version.version}; el equipo la revisa y la aprueba antes de que llegue a las OT.`
          : `Quedó en manos de Factum. ${a.aviso ?? ''}`.trim(),
      )
    } catch (e) {
      setError(mensajeDe(e))
    } finally {
      setEnviando(false)
    }
  }

  return (
    <Paper
      withBorder
      radius="md"
      p="md"
      aria-label={`Mejoras para ${r.nombre}`}
      style={{ borderLeft: '4px solid var(--mantine-color-precaucion-6)' }}
    >
      <Group gap="sm" wrap="nowrap" align="flex-start">
        <IconBulb size={24} color="var(--mantine-color-precaucion-5)" style={{ flexShrink: 0 }} />
        <Stack gap="sm" style={{ flex: 1, minWidth: 0 }}>
          <Text fw={800}>
            {n
              ? `Factum propone la versión ${r.version} de «${r.nombre}»`
              : `Factum vio algo en «${r.nombre}» que no se arregla cambiando la pauta`}
          </Text>
          {n > 0 && (
            <Box>
              <Text size="xs" fw={700} c="dimmed" tt="uppercase" mb={4}>
                Qué cambia y por qué
              </Text>
              <List spacing={6}>
                {r.cambios.map((c) => (
                  <Linea key={`${c.propuesta}:${c.que}`} que={c.que} porque={c.porque} />
                ))}
              </List>
            </Box>
          )}
          {r.sin_cambio.length > 0 && (
            <Box>
              <Text size="xs" fw={700} c="dimmed" tt="uppercase" mb={4}>
                Qué no cambia y por qué no
              </Text>
              <List spacing={6}>
                {r.sin_cambio.map((c) => (
                  <Linea key={c.propuesta} que={c.que} porque={c.por_que_no} />
                ))}
              </List>
            </Box>
          )}
          {error && (
            <Text size="sm" c="peligro" role="alert">
              {error}
            </Text>
          )}
          <Group gap="sm">
            <Button loading={enviando} leftSection={<IconCheck size={18} />} onClick={() => void aplicar()}>
              {n === 0 ? 'Entendido' : n === 1 ? 'Aplicar el cambio' : `Aplicar los ${n} cambios`}
            </Button>
            <Button variant="subtle" onClick={onPosponer}>
              Ahora no
            </Button>
            <Anchor component={Link} to="/supervisor/mejoras" size="sm" ml="auto">
              Ver el detalle
            </Anchor>
          </Group>
        </Stack>
      </Group>
    </Paper>
  )
}

/** Lo que Factum propone cambiar en las pautas, resumido: una tarjeta por pauta, con un solo toque para aplicarlo. */
export function Recomendaciones({ recomendaciones, quitar }: { recomendaciones: ResumenMejoras[]; quitar: (pauta: string) => void }) {
  const [pospuestas, setPospuestas] = useState<Set<string>>(new Set())
  const [hechos, setHechos] = useState<{ pauta: string; texto: string }[]>([])
  const visibles = recomendaciones.filter((r) => !pospuestas.has(r.pauta))
  if (visibles.length === 0 && hechos.length === 0) return null
  return (
    <Stack gap="sm" role="region" aria-label="Recomendaciones de Factum">
      {hechos.map((h) => (
        <Alert
          key={h.pauta}
          color="verificado"
          variant="light"
          icon={<IconCheck size={18} />}
          withCloseButton
          onClose={() => setHechos((hs) => hs.filter((x) => x.pauta !== h.pauta))}
          closeButtonLabel="Cerrar aviso"
        >
          {h.texto}
        </Alert>
      ))}
      {visibles.map((r) => (
        <Propuesta
          key={r.pauta}
          r={r}
          onAplicada={(texto) => {
            quitar(r.pauta)
            setHechos((hs) => [...hs.filter((x) => x.pauta !== r.pauta), { pauta: r.pauta, texto }])
          }}
          onPosponer={() => setPospuestas((s) => new Set(s).add(r.pauta))}
        />
      ))}
    </Stack>
  )
}
