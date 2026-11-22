import { CASOS } from './casos.js';
import { Visor, CALMO } from './escenas.js';
import { REPORTE } from './reporte.js';

const $ = (id) => document.getElementById(id);
const ESTADO_OT = { ok: 'todo bien', warning: 'atención', error: 'detente' };

// Lo que el visor muestra encima del 3D: el estado de la OT y los avisos abiertos.
function pintarEstado(visor, pill, avisos) {
  const E = visor.estado;
  const pasos = CASOS[visor.caso].pauta.pasos;
  const cerrados = pasos.filter((p) => E.estados[p.id] === 'verificado').length;
  pill.className = `pill ${E.completa ? 'ok' : E.nivel}`;
  pill.textContent = `${E.completa ? 'OT completa' : ESTADO_OT[E.nivel]} · ${cerrados} de ${pasos.length} pasos`;
  if (avisos) avisos.replaceChildren(...E.avisos.slice(0, 2).map((a) => {
    const d = document.createElement('div'); d.className = a.nivel;
    const b = document.createElement('b'); b.textContent = a.titulo;
    const s = document.createElement('small'); s.textContent = a.como;
    d.append(b, s); return d;
  }));
}

// La línea de tramos: uno por acción del operario, en rojo los que Factum detuvo.
function armarLinea(caja, visor, alElegir) {
  caja.replaceChildren(...visor.tramos.map((t, i) => {
    const b = document.createElement('button');
    b.className = t.nivel; b.title = t.t; b.setAttribute('aria-label', `Tramo ${i + 1}: ${t.t}`);
    if (alElegir) b.addEventListener('click', () => alElegir(i)); else b.tabIndex = -1;
    return b;
  }));
}
// Una lista que se lee bajando: el paso activo es el que cruza una franja de la pantalla. En pantallas angostas
// la escena va pegada arriba y tapa el medio, así que la franja baja.
const FRANJA = matchMedia('(max-width: 1000px)').matches ? '-68% 0px -22% 0px' : '-45% 0px -45% 0px';
function seguirPasos(pasos, alElegir) {
  const elegir = (li) => { pasos.forEach((p) => p.toggleAttribute('data-activa', p === li)); alElegir(li); };
  const mira = new IntersectionObserver((es) => { const e = es.filter((x) => x.isIntersecting).at(-1); if (e) elegir(e.target); }, { rootMargin: FRANJA });
  pasos.forEach((li) => { mira.observe(li); li.addEventListener('click', () => elegir(li)); });
  elegir(pasos[0]);
}
const marcarLinea = (caja, pos) => [...caja.children].forEach((b, i) => { b.toggleAttribute('data-actual', i === pos); b.toggleAttribute('data-hecho', i < pos); });

// Reproduce los tramos de un visor mientras su lienzo se ve y la pestaña está al frente.
function reproductor(visor, duracion, alTerminar) {
  let reloj = 0, andando = false, visible = false;
  const programar = () => {
    clearTimeout(reloj);
    if (!andando || !visible || document.hidden) return;
    reloj = setTimeout(() => {
      if (visor.pos === visor.tramos.length - 1) { if (alTerminar && alTerminar() === false) return; visor.ir(0, true); }
      else visor.ir(visor.pos + 1);
      programar();
    }, duracion(visor.tramos[visor.pos]));
  };
  new IntersectionObserver(([e]) => { visible = e.isIntersecting; programar(); }, { threshold: 0.3 }).observe(visor.cv);
  document.addEventListener('visibilitychange', programar);
  return { get andando() { return andando; }, partir() { andando = true; programar(); }, parar() { andando = false; clearTimeout(reloj); }, programar };
}

// ─── Portada: la correa de la minera corre sola, como un film ───────────────
{
  const film = $('film'), marco = $('film-marco');
  const visor = new Visor($('film-lienzo'), CASOS, 'mineria', { vaiven: 0.1 });
  // El 3D cae dentro del marco, que en escritorio ocupa la derecha y en el celular todo el ancho.
  const encuadrar = () => {
    const f = film.getBoundingClientRect(), m = marco.getBoundingClientRect();
    if (!f.width || !m.width) return;
    const arriba = marco.querySelector('.visor-arriba').offsetHeight, pie = marco.querySelector('.film-pie').offsetHeight;
    visor.op.centro = [(m.left - f.left + m.width / 2) / f.width, (m.top - f.top + arriba + (m.height - arriba - pie) * 0.52) / f.height];
    visor.op.foco = Math.min(m.width * 0.72, (m.height - arriba - pie) * 1.25);
    visor.op.techo = m.top - f.top + arriba; visor.op.suelo = f.bottom - m.bottom + pie;
    visor.sucio = true;
  };
  new ResizeObserver(encuadrar).observe(marco);
  armarLinea($('film-linea'), visor);
  visor.alCambiar = () => {
    pintarEstado(visor, $('film-estado'), $('film-avisos'));
    $('film-tramo').textContent = visor.tramos[visor.pos].t;
    marcarLinea($('film-linea'), visor.pos);
    film.dataset.nivel = visor.estado.nivel;
    encuadrar();
  };
  visor.ir(CALMO ? 2 : 0, true);   // sin movimiento, queda en el tramo que Factum detiene
  if (!CALMO) reproductor(visor, (t) => 3400 + (t.nivel === 'error' ? 1800 : 0)).partir();
}

// ─── Producto: al leer cada capa, la celda del brazo se mira desde donde esa capa decide ───
{
  const visor = new Visor($('capas-lienzo'), CASOS, 'brazo', { techo: 44, suelo: 8 });
  seguirPasos([...$('capas').children], (li) => {
    visor.ir(+li.dataset.tramo, true); visor.mirar(li.dataset.vista);
    visor.cv.parentElement.dataset.vista = li.dataset.vista;
    visor.op.centro = [0.5, li.dataset.vista === 'frontal' ? 0.62 : 0.5];   // de frente, la celda queda arriba del lienzo
    pintarEstado(visor, $('capas-estado'));
    $('capas-pie').textContent = li.dataset.pie;
  });
}

// ─── Mejora continua: el reporte de seis ejecuciones, que avanza con cada paso del ciclo ───
{
  const R = REPORTE, caja = $('informe'), hacer = (tag, clase, texto) => { const e = document.createElement(tag); if (clase) e.className = clase; if (texto != null) e.textContent = texto; return e; };
  const conPropuesta = new Set(R.propuestas.map((g) => g.paso)), elegida = R.propuestas[0], pasoElegido = R.pasos.find((p) => p.id === elegida.paso);
  const cab = hacer('div', 'informe-cab'), titulo = hacer('div');
  titulo.append(hacer('b', '', 'Reporte'), hacer('span', '', R.pauta));
  const version = hacer('span', 'version'); version.append(hacer('i', '', `v${R.version}`), hacer('i', '', `v${R.version + 1}`));
  cab.append(titulo, version);
  const cifras = hacer('dl', 'informe-cifras');
  [[R.n, 'ejecuciones'], [R.verificados, 'pasos verificados'], [R.detenciones, 'veces que detuvo', 'r'], [R.conflictos, R.conflictos === 1 ? 'declaración contradicha' : 'declaraciones contradichas', 'c']]
    .forEach(([n, t, c]) => { const d = hacer('div', c); d.append(hacer('dd', '', n), hacer('dt', '', t)); cifras.append(d); });
  const tabla = hacer('table', 'grilla'), cabeza = hacer('tr'), cuerpo = hacer('tbody');
  cabeza.append(hacer('th'), ...R.filas.map((f) => hacer('th', '', f.r)), hacer('th', 'v2', `v${R.version + 1}`), hacer('th', 'v2', `v${R.version + 1}`));
  R.pasos.forEach((p, fila) => {
    const tr = hacer('tr'), th = hacer('th'); th.scope = 'row';
    if (conPropuesta.has(p.id)) tr.dataset.propuesta = '';
    th.append(hacer('span', '', p.orden), p.titulo);
    if (p.id === elegida.paso) th.append(hacer('em', 'cambia', `cambia en v${R.version + 1}`));
    tr.append(th, ...R.filas.map((f, c) => {
      const s = R.celdas[`${p.id}:${f.r}`] || [], td = hacer('td', s.includes('desvio') ? 'd' : s.includes('conflicto') ? 'w' : 'k', s.includes('desvio') ? '!' : s.includes('conflicto') ? '?' : '✓');
      td.style.setProperty('--c', c); td.style.setProperty('--f', fila); return td;
    }), hacer('td', 'v2'), hacer('td', 'v2'));
    cuerpo.append(tr);
  });
  const thead = hacer('thead'); thead.append(cabeza); tabla.append(thead, cuerpo);
  const propuesta = hacer('div', 'propuesta'), decision = hacer('p', 'decision');
  decision.append(hacer('span', 'pendiente', 'La acepta o la descarta el supervisor'), hacer('span', 'aceptada', `Aceptada por el supervisor: pasa a la versión ${R.version + 1}`));
  const mas = R.propuestas.length - 1;
  propuesta.append(
    hacer('b', '', `Propuesta · paso ${pasoElegido.orden}, ${pasoElegido.titulo.toLowerCase()}`),
    hacer('p', '', `En ${elegida.veces} de ${R.n} ejecuciones Factum detuvo a la persona: ${elegida.textos[0]}.`),
    hacer('p', 'nota', `Revisar la redacción del paso.${pasoElegido.critico ? ' Es un paso de seguridad: que se desvíe seguido no lo vuelve prescindible.' : ''}`),
    decision,
    hacer('p', 'nota', `${mas ? `Hay ${mas === 1 ? 'una propuesta más' : `${mas} propuestas más`}. ` : ''}${R.sueltas ? `${R.sueltas === 1 ? 'Una desviación suelta espera' : `${R.sueltas} desviaciones sueltas esperan`} repetirse.` : ''}`),
  );
  caja.setAttribute('role', 'img');
  caja.setAttribute('aria-label', `Reporte de ${R.n} ejecuciones de la pauta «${R.pauta}», paso por paso. El paso ${pasoElegido.orden}, ${pasoElegido.titulo}, se desvió en ${elegida.veces} de ellas y genera una propuesta que el supervisor acepta para la versión ${R.version + 1}.`);
  caja.append(cab, cifras, tabla, propuesta);
  new IntersectionObserver(([e], o) => { if (e.isIntersecting) { caja.classList.add('vivo'); o.disconnect(); } }, { threshold: 0.3 }).observe(caja);
  seguirPasos([...$('ciclo').children], (li) => {
    const fase = +li.dataset.fase; caja.dataset.fase = fase;
    [2, 3, 4, 5].forEach((n) => caja.classList.toggle(`desde-${n}`, fase >= n));
  });
}

// ─── Industrias: las otras estaciones, cada una con su pauta y sus desvíos ──
{
  const visor = new Visor($('estacion-lienzo'), CASOS, 'electrica', { arrastre: true, techo: 46, suelo: 30 });
  const lista = $('estacion-pasos'), linea = $('estacion-linea'), auto = $('estacion-auto');
  const cierra = (c, p) => p.sensor ? `${(c.nombres[p.sensor.id] || [p.sensor.id])[0]}: ${((c.nombres[p.sensor.id] || [])[1] || {})[p.sensor.espera] || p.sensor.espera}` : p.tipo_evidencia === 'camara' ? 'lo mira la cámara' : 'lo dice la persona';
  const duracion = (t) => Math.min(9000, Math.max(3600, 1400 + 40 * (t.t.length + t.x.length)));
  const rep = reproductor(visor, duracion);
  const marcarAuto = () => { auto.setAttribute('aria-pressed', rep.andando); auto.textContent = rep.andando ? 'Pausar' : 'Reproducir'; };

  const armar = () => {
    const c = CASOS[visor.caso];
    $('estacion-pauta').textContent = `${c.pauta.nombre} · ${c.pauta.equipo}`;
    lista.replaceChildren(...c.pauta.pasos.map((p) => {
      const li = document.createElement('li');
      const t = document.createElement('span'); t.className = 'paso-titulo'; t.textContent = p.titulo;
      const d = document.createElement('span'); d.className = 'paso-detalle'; d.textContent = cierra(c, p);
      const m = document.createElement('i'); m.className = 'paso-marca';
      li.append(t, d, m); return li;
    }));
    armarLinea(linea, visor, (i) => { rep.parar(); marcarAuto(); visor.ir(i, true); });
  };
  visor.alCambiar = () => {
    const c = CASOS[visor.caso], E = visor.estado, t = visor.tramos[visor.pos];
    pintarEstado(visor, $('estacion-estado'), $('estacion-avisos'));
    c.pauta.pasos.forEach((p, i) => {
      const actual = E.actual && E.actual.id === p.id;
      lista.children[i].dataset.estado = E.estados[p.id] === 'verificado' ? 'verificado' : actual ? (E.nivel === 'error' ? 'saltado' : 'actual') : 'pendiente';
    });
    $('estacion-t').textContent = t.t; $('estacion-x').textContent = t.x;
    $('estacion-cuenta').textContent = `Tramo ${visor.pos + 1} de ${visor.tramos.length}`;
    marcarLinea(linea, visor.pos);
    $('estacion-atras').disabled = visor.pos === 0; $('estacion-sigue').disabled = visor.pos === visor.tramos.length - 1;
  };
  const elegir = (caso) => {
    document.querySelectorAll('[data-caso]').forEach((b) => b.setAttribute('aria-pressed', b.dataset.caso === caso));
    visor.elegir(caso); armar(); visor.alCambiar(); rep.programar();
  };
  document.querySelector('.estacion-casos').addEventListener('click', (e) => { const b = e.target.closest('[data-caso]'); if (b) elegir(b.dataset.caso); });
  $('estacion-atras').addEventListener('click', () => { rep.parar(); marcarAuto(); visor.ir(visor.pos - 1, true); });
  $('estacion-sigue').addEventListener('click', () => { rep.parar(); marcarAuto(); visor.ir(visor.pos + 1); });
  auto.addEventListener('click', () => { if (rep.andando) rep.parar(); else { if (visor.pos === visor.tramos.length - 1) visor.ir(0, true); rep.partir(); } marcarAuto(); });
  visor.cv.addEventListener('pointerdown', () => $('estacion').setAttribute('data-girada', ''));
  elegir('electrica');
  if (!CALMO) { rep.partir(); marcarAuto(); }
}

// ─── Cierre: el brazo trabajando de fondo ───────────────────────────────────
new Visor($('cierre-lienzo'), CASOS, 'brazo', { rotulos: false, orbita: 0.07, centro: [0.72, 0.56], escala: 0.9 });

// ─── Lo demás de la página ──────────────────────────────────────────────────
// 19 de 26: un punto por incidente clasificado.
$('puntos').replaceChildren(...Array.from({ length: 26 }, (_, i) => { const p = document.createElement('i'); if (i < 19) p.dataset.si = ''; p.style.setProperty('--i', i); return p; }));

// Cada bloque aparece la primera vez que entra a la pantalla.
const aparece = new IntersectionObserver((es) => es.forEach((e) => { if (e.isIntersecting) { e.target.classList.add('visto'); aparece.unobserve(e.target); } }), { rootMargin: '0px 0px -12% 0px' });
document.querySelectorAll('[data-aparece]').forEach((el) => {
  if (el.dataset.aparece === 'hijos') [...el.children].forEach((h, i) => h.style.setProperty('--i', i));
  aparece.observe(el);
});

// La barra es transparente sobre la portada y se cierra al bajar.
const barra = $('barra');
const cerrarBarra = () => barra.toggleAttribute('data-solida', scrollY > 24);
addEventListener('scroll', cerrarBarra, { passive: true }); cerrarBarra();
