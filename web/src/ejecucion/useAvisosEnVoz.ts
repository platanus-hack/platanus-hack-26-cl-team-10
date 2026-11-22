// Los avisos en voz de una OT: lo que llega y tiene que sonar, dicho una vez, y sus frases pedidas
// de antemano. Lo usan la pantalla del operario y la del supervisor; `config.VOZ_EN` dice cuál habla.

import { useEffect, useRef, type Dispatch } from 'react'
import { esAlto, frasesDeLaOt, textoParaVoz, type Accion, type Ejecucion } from './estado'
import { voz } from './voz'

export function useAvisosEnVoz(s: Ejecucion, dispatch: Dispatch<Accion>, habla: boolean) {
  // Lo que lee el aviso sin que la OT sea una dependencia: cambia con cada evento.
  const ot = useRef(s.ot)
  useEffect(() => {
    ot.current = s.ot
  }, [s.ot])

  // Cada evento que tiene que sonar (ver debeSonar) suena una vez, en orden, dicho como frase;
  // un «Alto» pasa adelante. La pantalla que no habla igual los da por dichos.
  useEffect(() => {
    if (s.porSonar.length === 0) return
    if (habla) for (const ev of s.porSonar) voz.decir(textoParaVoz(ev, ot.current), { alto: esAlto(ev) })
    dispatch({ tipo: 'sonado', ids: s.porSonar.map((e) => e.id) })
  }, [s.porSonar, habla, dispatch])

  // Las frases que esta OT puede decir se generan al abrirla, así su aviso suena sin esperar a
  // ElevenLabs. El texto como dependencia: la OT cambia con cada evento, sus frases casi nunca.
  const frases = JSON.stringify(habla && s.ot ? frasesDeLaOt(s.ot) : [])
  useEffect(() => {
    const textos = JSON.parse(frases) as string[]
    if (textos.length === 0) return
    const corte = new AbortController()
    void voz.precalentar(textos, corte.signal)
    return () => corte.abort()
  }, [frases])
}
