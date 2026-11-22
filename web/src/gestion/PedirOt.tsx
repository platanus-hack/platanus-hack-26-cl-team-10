import { Button, Group, Modal, Radio, Stack, Text } from '@mantine/core'
import { IconPlus } from '@tabler/icons-react'
import { useState } from 'react'
import { useNavigate } from 'react-router'
import { api } from '../api/cliente'
import type { PautaResumen } from '../api/tipos'
import { mensajeDe } from './useOts'

/** El supervisor pide una OT de una de las pautas de su empresa; nace sin operador. */
export function PedirOt() {
  const navigate = useNavigate()
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
      // Desde cualquier sección: a la lista de OT, donde la nueva queda por asignar y se dice que se pidió.
      void navigate('/supervisor', { state: { pedida: o } })
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
