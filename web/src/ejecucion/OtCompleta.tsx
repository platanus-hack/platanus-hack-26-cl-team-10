import { Button, Center, Stack, Text, ThemeIcon, Title } from '@mantine/core'
import { IconCheck } from '@tabler/icons-react'
import { Link } from 'react-router'
import type { EstadoOt, Evento } from '../api/tipos'
import { contarCierre } from './estado'

/** El cierre de la OT. El reporte con KPIs de desempeño es P1. */
export function OtCompleta({ ot, bitacora }: { ot: EstadoOt; bitacora: Evento[] }) {
  const verificados = ot.pasos.filter((p) => p.estado === 'verificado').length
  const { sobrescritos, avisos } = contarCierre(bitacora)

  return (
    <Center mih="100vh" p="md">
      <Stack align="center" gap="md" w="100%" maw={420}>
        <ThemeIcon color="verificado" radius="xl" size={88}>
          <IconCheck size={56} />
        </ThemeIcon>
        <Title order={1}>OT completa</Title>
        <Text fw={600} c="roca.7" ta="center">
          {ot.pauta}
        </Text>
        <Stack gap={4} align="center">
          <Text size="lg" fw={700}>
            {verificados} de {ot.pasos.length} pasos verificados
          </Text>
          {sobrescritos > 0 && (
            <Text c="precaucion.9" fw={600}>
              {sobrescritos === 1 ? '1 cerrado' : `${sobrescritos} cerrados`} a la palabra del operario
            </Text>
          )}
          {avisos > 0 && (
            <Text c="roca.7">{avisos === 1 ? '1 aviso' : `${avisos} avisos`} durante el trabajo</Text>
          )}
        </Stack>
        <Button component={Link} to="/operador" size="lg" variant="default" fullWidth>
          Volver a mis OT
        </Button>
      </Stack>
    </Center>
  )
}
