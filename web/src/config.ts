const env = import.meta.env

function texto(valor: string | undefined): string | null {
  return valor && valor.trim() ? valor.trim().replace(/\/$/, '') : null
}

const MOCK = env.VITE_MOCK === '1'
const API_URL = texto(env.VITE_API_URL) ?? (MOCK ? 'https://api.mock' : 'https://34-176-44-192.sslip.io')

/** En qué pantalla suenan los avisos en voz. */
export type DondeSuenaLaVoz = 'operario' | 'supervisor'

export const config = {
  MOCK,
  API_URL,
  EDGE_ID: texto(env.VITE_EDGE_ID) ?? 'edge-1',
  /**
   * La voz de ElevenLabs la sirve el mismo servidor del front (web/servidor/voz.ts), con mock o
   * sin él. Si no responde (sin llave, sin red), el aviso lo dice la voz del navegador.
   */
  VOZ_URL: texto(env.VITE_VOZ_URL) ?? '/api/voz',
  /**
   * SOLO PARA EL DEMO: los avisos en voz suenan en la vista del supervisor y no en la del operario.
   * Así se ahorra tener abierta una ventana del operario solo para que suene.
   * Lo normal es 'operario': el aviso es para quien está junto a la máquina. Volver a eso después del demo.
   */
  VOZ_EN: 'supervisor' as DondeSuenaLaVoz,
}
