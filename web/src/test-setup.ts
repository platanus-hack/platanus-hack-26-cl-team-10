import '@testing-library/jest-dom/vitest'
import { cleanup } from '@testing-library/react'
import { afterEach } from 'vitest'

afterEach(() => {
  cleanup()
  localStorage.clear()
  sessionStorage.clear()
})

// Mantine pregunta por matchMedia y ResizeObserver, que jsdom no trae.
if (!window.matchMedia) {
  Object.defineProperty(window, 'matchMedia', {
    writable: true,
    // Como un equipo con «reducir movimiento»: Mantine abre y cierra sin animar, y jsdom no espera transiciones.
    value: (query: string) => ({
      matches: query.includes('prefers-reduced-motion: reduce'),
      media: query,
      onchange: null,
      addEventListener: () => {},
      removeEventListener: () => {},
      addListener: () => {},
      removeListener: () => {},
      dispatchEvent: () => false,
    }),
  })
}
if (!('ResizeObserver' in window)) {
  ;(window as unknown as { ResizeObserver: unknown }).ResizeObserver = class {
    observe() {}
    unobserve() {}
    disconnect() {}
  }
}

// jsdom no reproduce audio: play() resuelve sin sonar.
window.HTMLMediaElement.prototype.play = () => Promise.resolve()
