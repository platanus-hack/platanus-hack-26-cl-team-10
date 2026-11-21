const env = import.meta.env

function texto(valor: string | undefined): string | null {
  return valor && valor.trim() ? valor.trim().replace(/\/$/, '') : null
}

const MOCK = env.VITE_MOCK === '1'
const API_URL = texto(env.VITE_API_URL) ?? (MOCK ? 'https://api.mock' : 'https://34-176-44-192.sslip.io')

export const config = {
  MOCK,
  API_URL,
  EDGE_ID: texto(env.VITE_EDGE_ID) ?? 'edge-1',
  /** Sin URL de voz, el aviso se dice con la voz del navegador (así corre el mock). */
  VOZ_URL: texto(env.VITE_VOZ_URL) ?? (MOCK ? null : `${API_URL}/voz`),
}
