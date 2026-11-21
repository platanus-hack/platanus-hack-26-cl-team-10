// El aviso sonoro del supervisor cuando aparece un incidente: dos notas cortas con Web Audio,
// sin archivos. El navegador deja sonar después de un toque en la página (el de «Entrar» sirve);
// `preparar()` en el primer toque cubre el caso de entrar recargando la página.

type ConAudio = typeof window & { webkitAudioContext?: typeof AudioContext }

let ctx: AudioContext | null = null

function contexto(): AudioContext | null {
  const AC = window.AudioContext ?? (window as ConAudio).webkitAudioContext
  if (!AC) return null
  ctx ??= new AC()
  if (ctx.state === 'suspended') void ctx.resume().catch(() => {})
  return ctx
}

export const campana = {
  /** Deja el audio listo dentro de un toque. */
  preparar(): void {
    try {
      contexto()
    } catch {
      // Sin audio: la barra roja basta.
    }
  },

  sonar(): void {
    try {
      const c = contexto()
      if (!c) return
      const t0 = c.currentTime
      ;[880, 660].forEach((frecuencia, i) => {
        const o = c.createOscillator()
        const g = c.createGain()
        const t = t0 + i * 0.22
        o.type = 'sine'
        o.frequency.value = frecuencia
        g.gain.setValueAtTime(0.0001, t)
        g.gain.exponentialRampToValueAtTime(0.3, t + 0.02)
        g.gain.exponentialRampToValueAtTime(0.0001, t + 0.6)
        o.connect(g).connect(c.destination)
        o.start(t)
        o.stop(t + 0.65)
      })
    } catch {
      // Sin audio: la barra roja basta.
    }
  },
}
