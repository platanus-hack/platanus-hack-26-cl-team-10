// El 3D de las estaciones de Factum. La geometría y las cinco escenas vienen tal cual del simulador del equipo
// (/simulador en la VM del demo): si una estación cambia allá, se vuelve a copiar este bloque. Lo propio de la
// landing es `Visor`, al final: dibuja una escena en un lienzo a partir de los tramos de `casos.js`.

// ─── Del simulador ──────────────────────────────────────────────────────────
const DIST_MAX = 60;
const m4 = {
  mul(a, b) { const o = new Array(16); for (let r = 0; r < 4; r++) for (let c = 0; c < 4; c++) o[r * 4 + c] = a[r * 4] * b[c] + a[r * 4 + 1] * b[4 + c] + a[r * 4 + 2] * b[8 + c] + a[r * 4 + 3] * b[12 + c]; return o; },
  t: (x, y, z) => [1, 0, 0, x, 0, 1, 0, y, 0, 0, 1, z, 0, 0, 0, 1],
  s: k => [k, 0, 0, 0, 0, k, 0, 0, 0, 0, k, 0, 0, 0, 0, 1],
  ry: a => { const c = Math.cos(a), s = Math.sin(a); return [c, 0, s, 0, 0, 1, 0, 0, -s, 0, c, 0, 0, 0, 0, 1]; },
  rz: a => { const c = Math.cos(a), s = Math.sin(a); return [c, -s, 0, 0, s, c, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]; },
  rx: a => { const c = Math.cos(a), s = Math.sin(a); return [1, 0, 0, 0, 0, c, -s, 0, 0, s, c, 0, 0, 0, 0, 1]; },
  ap: (m, p) => [m[0] * p[0] + m[1] * p[1] + m[2] * p[2] + m[3], m[4] * p[0] + m[5] * p[1] + m[6] * p[2] + m[7], m[8] * p[0] + m[9] * p[1] + m[10] * p[2] + m[11]],
  de: (...ms) => ms.reduce((a, b) => m4.mul(a, b)),
};
const v3 = {
  sub: (a, b) => [a[0] - b[0], a[1] - b[1], a[2] - b[2]], dot: (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2],
  cross: (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]],
  norm: a => { const l = Math.hypot(a[0], a[1], a[2]) || 1; return [a[0] / l, a[1] / l, a[2] / l]; },
};
function caja(w, h, d) {   // apoyada en y = 0, centrada en x y z
  const x = w / 2, z = d / 2;
  return {v: [[-x, 0, -z], [x, 0, -z], [x, h, -z], [-x, h, -z], [-x, 0, z], [x, 0, z], [x, h, z], [-x, h, z]],
    f: [[0, 1, 2, 3], [4, 5, 6, 7], [0, 4, 7, 3], [1, 5, 6, 2], [3, 2, 6, 7], [0, 1, 5, 4]]};
}
function prisma(r, h, n = 14) {
  const v = [], f = [];
  for (let i = 0; i < n; i++) { const a = i / n * 2 * Math.PI; v.push([r * Math.cos(a), 0, r * Math.sin(a)]); }
  for (let i = 0; i < n; i++) v.push([v[i][0], h, v[i][2]]);
  for (let i = 0; i < n; i++) f.push([i, (i + 1) % n, n + (i + 1) % n, n + i]);
  f.push([...Array(n).keys()], [...Array(n).keys()].map(i => n + i));
  return {v, f};
}
const COL = {blanco: [244, 244, 238], servo: [44, 44, 56], mesa: [128, 140, 158], piso: [246, 247, 249], pcb: [38, 92, 150], plata: [196, 200, 206],
  piel: [224, 168, 120], azul: [47, 95, 158], bandeja: [242, 200, 60], pieza: [200, 70, 50], negro: [30, 34, 40], oro: [214, 170, 60], verde: [63, 191, 133],
  gris: [150, 158, 170], rojo: [220, 70, 60], fantasma: [150, 158, 170]};


Object.assign(COL, {jean: [52, 72, 112], chaleco: [240, 130, 40], casco: [250, 212, 60], cobre: [205, 125, 62], gabinete: [158, 168, 180], tierraC: [58, 172, 92],
  goma: [52, 54, 60], mineral: [168, 132, 98], acero: [176, 184, 194], caliente: [232, 96, 44], amarillo: [240, 188, 40], suelo: [150, 132, 106], oruga: [42, 44, 50], vidrio: [96, 136, 166], humo: [208, 208, 214], cinta: [228, 62, 50], hormigon: [128, 140, 158], naranja: [236, 140, 40]});

// Cada operario lleva otro color de chaleco, para que se note que la ejecución es de otra persona.
const CHALECOS = [[240, 130, 40], [92, 176, 84], [64, 128, 204], [204, 82, 160], [222, 192, 40], [150, 104, 214]];
const MANGAS = [[47, 95, 158], [60, 130, 70], [150, 60, 60], [120, 70, 150], [170, 120, 40], [40, 120, 130]];
const colorOperario = paleta => paleta[0];
function persona(pon, x, z, k = 1.8, giro = 0) {
  const M = m4.de(m4.t(x, 0, z), m4.ry(giro));
  pon("persona", caja(2.2 * k, 4.2 * k, 1.3 * k), M, COL.jean);
  pon("persona", caja(2.6 * k, 3.4 * k, 1.5 * k), m4.de(M, m4.t(0, 4.2 * k, 0)), colorOperario(CHALECOS));
  pon("persona", prisma(0.85 * k, 1.5 * k, 10), m4.de(M, m4.t(0, 7.7 * k, 0)), COL.piel);
  pon("persona", prisma(1.05 * k, 0.6 * k, 10), m4.de(M, m4.t(0, 9.1 * k, 0)), COL.casco);
}
const candado = (pon, M) => {
  pon("candado", caja(1.5, 1.4, 0.7), M, COL.oro);
  pon("candado", caja(0.22, 1, 0.22), m4.de(M, m4.t(-0.45, 1.4, 0)), COL.plata); pon("candado", caja(0.22, 1, 0.22), m4.de(M, m4.t(0.45, 1.4, 0)), COL.plata);
  pon("candado", caja(1.12, 0.22, 0.22), m4.de(M, m4.t(0, 2.4, 0)), COL.plata);
};

// ─── Las cinco estaciones ────────────────────────────────────────────────────
// Cada estación tiene dos funciones. `OBJETIVO` dice dónde tiene que quedar cada cosa según los sensores y el
// paso de la pauta; el dibujo sigue esa pose de a poco, para que el movimiento sea continuo. `e.hecho(paso)`
// dice si ese paso ya está verificado, y `e.donde`, dónde trabaja la persona en este tramo.
const mez = (a, b, t) => a.map((x, i) => x + (b[i] - x) * t);
const OBJETIVO = {
  brazo: e => { const viva = e.s.energia === "viva", falla = e.ot && !e.hecho("p5");
    return {mano: e.s.zona === "ocupada" ? (e.donde === "pinza" ? 9 : 26) : 100, candado: +(e.s.bloqueo === "puesto"), viva: +viva, abre: !viva || falla ? 1.5 : (e.fase < 0.5 ? 0.7 : 1.7)}; },
  demo: e => { const L = {lejos: [-4, 6, 40], cerca: [0, 9.5, 15], polin: [0, 6.6, 10.5], boton: [31, 8.6, 18], "boton-cerca": [2, 8.2, 12]}[e.donde || "lejos"], viva = e.s.energia === "viva";
    return {marcha: +viva, viva: +viva, traba: +(e.s.bloqueo === "puesto"), viejo: +e.hecho("p4"), nuevo: +e.hecho("p5"), hx: L[0], hy: L[1], hz: L[2]}; },
  mineria: e => { const L = {lejos: [-34, 24, 0.4], botonera: [19.5, 20, 0.2], guarda: [-8.5, 17, 0], polin: [-7, 13.4, 0], tablero: [35.5, 27.5, -0.5], caja: [31.5, 24, 0.2]}[e.donde || "lejos"];
    return {marcha: +(e.s.correa === "en_marcha"), carga: +(e.s.correa === "en_marcha" && !e.hecho("p1")), viva: +(e.s.energia === "viva"), candado: +(e.s.bloqueo === "puesto"),
      guarda: +(e.s.guarda === "abierta"), polin: +e.hecho("p6"), alza: +(e.donde === "polin"), px: L[0], pz: L[1], giro: L[2]}; },
  electrica: e => { const L = {lejos: [17, 5, -1.4], mando: [11.6, 5.4, -1.5], frente: [2.5, 13, 0], tierra: [-2.4, 12.4, 0.25], fuera: [15, 24, -0.6]}[e.donde || "lejos"], ab = e.s.seccionador === "abierto";
    return {secc: ab ? 1.05 : 0, mando: ab ? 2.1 : 0.5, candado: +(e.s.candado_mando === "cerrado"), tension: +(e.s.tension === "presente"), tierra: +(e.s.tierra === "puesta"), barrera: +e.hecho("p5"), px: L[0], pz: L[1], giro: L[2]}; },
  construccion: e => { const arriba = e.s.implementos === "levantados", L = e.s.zona === "ocupada" ? [26, 3.6, -1.2] : ({fuera: [31, 25, 0.3], cabina: [9, 15.5, 2.7]}[e.donde || "fuera"]);
    return {e1: arriba ? 0.96 : 0.38, baja: arriba ? 2.0 : 1.7, humo: +(e.s.motor === "encendido"), palanca: e.s.palanca_seguridad === "bloqueada" ? 0 : -0.95, candado: +(e.s.palanca_seguridad === "bloqueada"),
      presion: +(e.s.presion_hidraulica === "con_presion"), manguera: +e.hecho("p5"), px: L[0], pz: L[1], giro: L[2]}; },
};
const conCandado = (pon, q, x, y, z, k, giro = 0) => { if (q.candado > 0.03) candado(pon, m4.de(m4.t(x, y + (1 - q.candado) * 7, z), m4.ry(giro), m4.s(k * q.candado))); };

function escenaBrazo(e, q) {
  const o = [], pon = (id, malla, M, c, fantasma) => o.push({id, malla, M, c, fantasma}), dentro = e.s.zona === "ocupada";
  pon("tablero", caja(190, 1.2, 96), m4.t(34, -1.2, 0), COL.hormigon);
  const giro = 0.9 * Math.cos(2 * Math.PI * e.fase), baja = Math.abs(Math.cos(2 * Math.PI * e.fase)), a1 = -(0.34 + 0.22 * baja), a2 = -(1.1 + 0.42 * baja);
  const lleva = e.fase < 0.5, falla = e.ot && !e.hecho("p5"), E = m4.s(1.5);
  pon("brazo", prisma(8.5, 1.6), E, COL.blanco);
  const Mcol = m4.de(E, m4.t(0, 1.6, 0), m4.ry(giro));
  pon("brazo", caja(5.4, 7, 5.4), Mcol, COL.blanco); pon("brazo", caja(2.6, 2.6, 6.2), m4.de(Mcol, m4.t(0, 5.6, 0)), COL.servo);
  const M1 = m4.de(Mcol, m4.t(0, 7, 0), m4.rz(a1));
  pon("brazo", caja(3, 13, 3.6), M1, COL.blanco); pon("brazo", caja(2.6, 2.6, 5.6), m4.de(M1, m4.t(0, 11.4, 0)), COL.servo);
  const M2 = m4.de(M1, m4.t(0, 13, 0), m4.rz(a2));
  pon("brazo", caja(2.6, 12, 3.2), M2, COL.blanco);
  const Mg = m4.de(M2, m4.t(0, 12, 0));
  pon("brazo", caja(3.6, 2.6, 5), Mg, COL.blanco); pon("brazo", caja(2.4, 2.4, 2.4), m4.de(Mg, m4.t(-2.6, 0.2, 0)), COL.servo);
  pon("brazo", caja(1, 5.4, 1.1), m4.de(Mg, m4.t(0, 2.6, q.abre)), COL.blanco); pon("brazo", caja(1, 5.4, 1.1), m4.de(Mg, m4.t(0, 2.6, -q.abre)), COL.blanco);
  const punta = m4.ap(Mg, [0, 6.4, 0]), R = 23.2, zA = R * Math.sin(-0.9), xA = R * Math.cos(0.9);
  pon("util", caja(9, 0.6, 9), m4.t(xA, 0, -zA), COL.bandeja); pon("util", caja(9, 0.6, 9), m4.t(xA, 0, zA), COL.bandeja);
  pon("util", caja(3.4, 3.4, 3.4), falla ? m4.de(m4.t(19, 0, 3), m4.ry(0.5)) : (q.viva > 0.5 && lleva ? m4.t(punta[0], punta[1] - 3.4, punta[2]) : m4.t(xA, 0.6, zA)), COL.pieza);
  [[-24, -24], [24, -24], [-24, 24], [24, 24]].forEach(([x, z]) => pon("celda", caja(1, 46, 1), m4.t(x, 0, z), COL.fantasma, true));
  pon("celda", caja(49, 1, 1), m4.t(0, 46, -24), COL.fantasma, true); pon("celda", caja(49, 1, 1), m4.t(0, 46, 24), COL.fantasma, true);
  pon("celda", caja(1, 1, 49), m4.t(-24, 46, 0), COL.fantasma, true); pon("celda", caja(1, 1, 49), m4.t(24, 46, 0), COL.fantasma, true);
  pon("celda", caja(1, 46, 49), m4.t(-24, 0, 0), COL.fantasma, true);
  const Mu = m4.t(24.6, 9, -19);
  pon("us", caja(0.5, 2.6, 5.4), Mu, COL.pcb); pon("us", caja(0.6, 9, 0.6), m4.t(24.6, 0, -19), COL.gris);
  pon("us", prisma(1.05, 1.5, 10), m4.de(Mu, m4.t(0.25, 1.3, -1.4), m4.rz(-Math.PI / 2)), COL.plata); pon("us", prisma(1.05, 1.5, 10), m4.de(Mu, m4.t(0.25, 1.3, 1.4), m4.rz(-Math.PI / 2)), COL.plata);
  pon("rele", caja(9, 5, 7), m4.t(-40, 0, -8), COL.fantasma, true); pon("rele", caja(2, 1, 2), m4.t(-42.6, 5, -8), mez(COL.negro, COL.verde, q.viva));
  pon("puls", caja(1.6, 1.1, 1.6), m4.t(-37.8, 5, -8), COL.negro);
  conCandado(pon, q, -37.8, 6.1, -8, 2.6);
  pon("esp", caja(17, 1, 5.6), m4.t(-40, 0, -32), COL.blanco); pon("esp", caja(5.2, 0.7, 2.7), m4.t(-43, 1, -32), COL.negro);
  pon("cam", caja(0.8, 60, 0.8), m4.t(-27, 0, -27), COL.gris); pon("cam", caja(27, 0.8, 0.8), m4.t(-13.5, 60, -27), COL.gris);
  pon("cam", caja(0.8, 0.8, 27), m4.t(0, 60, -13.5), COL.gris); pon("cam", caja(8, 0.9, 15.5), m4.t(0, 59, 0), COL.negro);
  const x0 = 24 + q.mano;
  pon("operario", caja(34, 4.6, 5.4), m4.t(x0 + 22, 8, 2), colorOperario(MANGAS)); pon("operario", caja(6.5, 2, 6), m4.t(x0 + 2, 9.4, 2), COL.piel);
  [3.6, 2, 0.4].forEach(z => pon("operario", caja(3.6, 1.1, 1.3), m4.t(x0 - 2.7, 10, z), COL.piel));
  return {objetos: o, zonas: [{pts: [[24, 0.05, -22], [24 + DIST_MAX, 0.05, -34], [24 + DIST_MAX, 0.05, 34], [24, 0.05, 22]], roja: dentro}],
    lineas: [[0, 59, 0], [[-22, 0, -22], [22, 0, -22], [22, 0, 22], [-22, 0, 22]]],
    rotulos: [[[-5, 41, 0], "brazo"], [[24.6, 15, -19], "zona"], [[-47, 9, -4], "energia"], [[-26, 27, -8], "bloqueo"], [[0, 64, 0], "cámara"]]
      .concat(e.marca === "esp" ? [[[8, 52, 0], "el ESP32 cortó los servos", true]] : [])};
}

function escenaDemo(e, q) {
  const o = [], pon = (id, malla, M, c, fantasma) => o.push({id, malla, M, c, fantasma});
  const Y = 7, X = [-18, -9, 0, 9, 18];
  const plumon = (id, x, z, color) => { pon(id, prisma(0.85, 13.5, 10), m4.de(m4.t(x, Y, z), m4.rx(Math.PI / 2)), COL.blanco); pon(id, prisma(0.95, 3, 10), m4.de(m4.t(x, Y, z + 10.5), m4.rx(Math.PI / 2)), color); };
  pon("tablero", caja(96, 1, 60), m4.t(4, -1, 10), COL.hormigon);
  // las dos paredes de cartón pluma, con un agujero por polín para sacarlo de lado
  [-5.4, 5.4].forEach(z => pon("paredes", caja(48, 9.4, 0.7), m4.t(0, 0, z), COL.blanco));
  // los plumones-polín sobresalen hacia la cámara; el rojo es el malo, el verde espera en la mesa
  X.forEach((x, i) => { if (i !== 2) plumon("polines", x, -6.6, COL.negro); });
  if (q.viejo < 0.98) plumon("polin-rojo", 0 + q.viejo * -9, -6.6 + q.viejo * 18, COL.rojo);
  else plumon("polin-rojo", -9, 11.4, COL.rojo);
  plumon("polin-verde", 9 - q.nuevo * 9, 11.4 - q.nuevo * 18, COL.verde);
  // la correa: un elástico ancho sobre los plumones, con marcas que avanzan mientras el motor gira
  for (let x = -22; x < 22; x += 4) { pon("correa", caja(4, 0.35, 9.4), m4.t(x + 2, Y + 0.85, 0), COL.goma); pon("correa", caja(4, 0.3, 9.4), m4.t(x + 2, Y - 3.4, 0), COL.goma); }
  for (let i = 0; i < 4; i++) { const x = ((i * 11 + e.cinta) % 44) - 22; pon("marcas", caja(0.6, 0.1, 8.6), m4.t(x, Y + 1.22, 0), COL.amarillo); }
  // el motor DC mueve la polea grande (una tapa de frasco) con un elástico de billetes
  const giro = e.cinta * 0.6;
  pon("polea", prisma(3, 0.8, 16), m4.de(m4.t(23, Y - 1, 5.8), m4.rx(Math.PI / 2)), COL.plata);
  [0, Math.PI / 2].forEach(a => pon("polea", caja(5.6, 0.5, 0.3), m4.de(m4.t(23, Y - 1, 6.7), m4.rz(giro + a), m4.t(0, -0.25, 0)), COL.gris));
  pon("motor", caja(4, 3.4, 3.4), m4.t(31, 0, 7), mez(COL.gris, COL.azul, 0.3 + 0.7 * q.viva)); pon("motor", prisma(0.35, 3, 8), m4.de(m4.t(29, 1.7, 7), m4.rz(Math.PI / 2)), COL.plata);
  pon("motor", caja(9, 0.25, 0.5), m4.de(m4.t(26.5, Y / 2, 6.6), m4.rz(0.62)), COL.cinta);
  // la electrónica: placa, L298N y el botón de parada, que queda trabado
  pon("placa", caja(9, 0.8, 4.4), m4.t(-30, 0, 14), COL.pcb); pon("placa", caja(3.6, 0.6, 2), m4.t(-31.5, 0.8, 14), COL.negro);
  pon("l298n", caja(4.4, 1.4, 4.4), m4.t(31, 0, 1), COL.rojo);
  pon("boton", caja(5, 2.4, 5), m4.t(31, 0, 18), COL.amarillo); pon("boton", prisma(1.4, 1.3 - 0.8 * q.traba, 12), m4.t(31, 2.4, 18), COL.rojo);
  pon("boton", caja(0.9, 0.9, 0.4), m4.t(33, 1, 20.6), mez(COL.negro, COL.rojo, q.traba));
  // el sensor de distancia mira hacia donde llega la mano; la cámara del celular, a las puntas de los plumones
  pon("us", caja(0.5, 6, 0.5), m4.t(-12, 0, 9), COL.gris); pon("us", caja(4.6, 2.2, 0.5), m4.t(-12, 6, 9), COL.pcb);
  [-1.2, 1.2].forEach(dx => pon("us", prisma(0.9, 1.1, 10), m4.de(m4.t(-12 + dx, 7.1, 9.3), m4.rx(Math.PI / 2)), COL.plata));
  pon("cam", caja(0.5, 15, 0.5), m4.t(-30, 0, 24), COL.gris); pon("cam", caja(7, 3.6, 0.7), m4.de(m4.t(-30, 15, 24), m4.ry(-0.8)), COL.negro);
  // la mano del operario
  const M = m4.t(q.hx, q.hy, q.hz);
  pon("mano", caja(2.8, 2.2, 16), m4.de(M, m4.t(0, 0, 9)), colorOperario(MANGAS)); pon("mano", caja(3, 1.6, 3.4), M, COL.piel);
  [-0.9, 0, 0.9].forEach(dx => pon("mano", caja(0.6, 0.6, 2), m4.de(M, m4.t(dx, 0.4, -2.6)), COL.piel));
  const peligro = e.s.operario === "presente" && e.s.energia === "viva";
  return {objetos: o, zonas: [{pts: [[-15, 0.05, 6.5], [15, 0.05, 6.5], [15, 0.05, 22], [-15, 0.05, 22]], roja: peligro, tenue: !peligro}], lineas: null,
    rotulos: [[[31, 7, 7], "energia"], [[31, 6.6, 18], "bloqueo"], [[-12, 11.5, 9], "operario"], [[-30, 20.5, 24], "cámara"]]
      .concat(e.marca === "esp" ? [[[8, 20, 0], "la placa no deja partir el motor", true]] : [])};
}

function escenaCorrea(e, q) {
  const o = [], pon = (id, malla, M, c, fantasma) => o.push({id, malla, M, c, fantasma});
  const ALA = 0.61, Y = 12, EST = [-28, -14, 0, 14, 28], rodillo = (x, y, z, giro, largo, r, color) => pon("polines", prisma(r, largo, 10), m4.de(m4.t(x, y, z), m4.rx(giro)), color);
  const alza = x => Math.max(0, 1 - Math.abs(x) / 13) * 1.9 * q.alza;
  pon("tablero", caja(104, 1, 58), m4.t(3, -1, 9), COL.suelo);
  // el bastidor: dos largueros, patas y los marcos de las estaciones de polines
  for (let x = -30; x <= 30; x += 12) [-9.4, 9.4].forEach(z => pon("bastidor", caja(12, 1, 0.8), m4.t(x, 9.2, z), COL.gris));
  [-33, -11, 11, 33].forEach(x => [-9.4, 9.4].forEach(z => pon("bastidor", caja(0.9, 9.2, 0.9), m4.t(x, 0, z), COL.gris)));
  EST.forEach((x, i) => {
    const mio = i === 2;
    pon("bastidor", caja(1, 0.9, 19.6), m4.t(x, 10.2, 0), COL.gris);
    [-1, 1].forEach(s => pon("bastidor", caja(0.8, 5.6, 0.7), m4.t(x, 10.2, s * 9.3), COL.gris));
    rodillo(x, Y, -2.5, Math.PI / 2, 5, 1.05, COL.acero);
    // los rodillos de ala sobresalen de la correa; el del frente de la estación 14 es el trabado
    [-1, 1].forEach(s => rodillo(x, Y, s * 2.7, s * (Math.PI / 2 - ALA), 7.6, 1.05, mio && s === 1 ? mez(COL.caliente, COL.acero, q.polin) : COL.acero));
  });
  // la correa de carga, por tramos para que el orden de dibujo no la corte; sobre la estación intervenida se levanta
  for (let xc = -35; xc <= 35; xc += 7) {
    const y = Y + 1.05 + alza(xc);
    pon("correa", caja(7, 0.35, 5.2), m4.t(xc, y, 0), COL.goma);
    [-1, 1].forEach(s => pon("correa", caja(7, 0.35, 5.4), m4.de(m4.t(xc, y, s * 2.6), m4.rx(-s * ALA), m4.t(0, 0, s * 2.7)), COL.goma));
  }
  // retorno, polines de retorno y las poleas de cabeza y de cola
  for (let x = -30; x <= 30; x += 12) pon("retorno", caja(12, 0.3, 13), m4.t(x, 6.3, 0), COL.goma);
  [-21, 7, 21].forEach(x => rodillo(x, 5.4, -8.4, Math.PI / 2, 16.8, 0.85, COL.acero));
  [-38.5, 38.5].forEach(x => pon("polea", prisma(3.4, 13.6, 14), m4.de(m4.t(x, 9.8, -6.8), m4.rx(Math.PI / 2)), COL.plata));
  // la carga viaja con la correa y se va cuando se detiene; las marcas de empalme muestran que corre aunque vaya vacía
  for (let i = 0; i < 6; i++) { const x = ((i * 12.5 + e.cinta) % 75) - 37.5; pon("carga", caja(0.5, 0.12, 4.6), m4.t(x, Y + 1.42 + alza(x), 0), COL.gris);
    if (q.carga > 0.04) { const k = q.carga * (0.8 + 0.4 * ((i * 7) % 3) / 2); pon("carga", caja(5 * k, 2 * k, 4.2 * k), m4.t(((i * 12.5 + 6 + e.cinta) % 75) - 37.5, Y + 1.4, 0), COL.mineral); } }
  // el accionamiento: motor y reductor junto a la polea de cabeza
  pon("motor", caja(5.2, 7.9, 4), m4.t(38.5, 0, 10.6), COL.gris); pon("motor", caja(6.4, 3.8, 4.6), m4.t(38.5, 7.9, 10.8), mez(COL.gris, COL.azul, 0.35 + 0.65 * q.viva));
  // las guardas son de malla: un marco amarillo que deja ver los polines. La de la estación 14 se saca y queda en el suelo
  const guarda = (id, M) => { pon(id, caja(11, 6, 0.2), M, COL.fantasma, true); [0, 5.5].forEach(y => pon(id, caja(11.4, 0.5, 0.5), m4.de(M, m4.t(0, y, 0)), COL.amarillo)); [-5.5, 5.5].forEach(x => pon(id, caja(0.5, 6, 0.5), m4.de(M, m4.t(x, 0, 0)), COL.amarillo)); };
  EST.forEach((x, i) => { if (i !== 2) guarda("guardaF", m4.t(x, 9.6, 10.4)); });
  guarda("guarda", m4.de(m4.t(q.guarda * 11, 9.6 * (1 - q.guarda) + 0.3 * q.guarda, 10.4 + q.guarda * 11), m4.rx(q.guarda * 1.45)));
  // el polín de repuesto, en el suelo: nuevo antes del cambio, el trabado después
  pon("repuesto", prisma(1.05, 7.6, 10), m4.de(m4.t(-12, 1.05, 16), m4.rx(Math.PI / 2)), mez(COL.acero, COL.caliente, q.polin));
  // parada de emergencia a lo largo, tablero del desconectador, caja de bloqueo y botonera local
  for (let x = -30; x <= 30; x += 12) pon("pullcord", caja(12, 0.16, 0.16), m4.t(x, 16.6, 10.9), COL.cinta);
  [-36, 36].forEach(x => pon("pullcord", caja(0.3, 7.6, 0.3), m4.t(x, 9.2, 10.9), COL.gris));
  pon("tablero-e", caja(6, 11, 2.2), m4.t(42, 0, 22), COL.gabinete); pon("tablero-e", caja(1.2, 1.2, 0.5), m4.t(40.6, 8.6, 23.2), mez(COL.verde, COL.rojo, q.viva));
  pon("tablero-e", caja(0.6, 3.4, 0.6), m4.de(m4.t(43, 6.6, 23.3), m4.rz((1 - q.viva) * 1.5 - 0.75)), COL.negro);
  pon("caja-b", caja(0.6, 8, 0.6), m4.t(28, 0, 20), COL.gris); pon("caja-b", caja(4.4, 3.6, 1.6), m4.t(28, 6.4, 20), COL.rojo);
  conCandado(pon, q, 28, 7.2, 21.1, 1.2);
  pon("botonera", caja(0.5, 7.6, 0.5), m4.t(16, 0, 16), COL.gris); pon("botonera", caja(2.2, 2.8, 1.2), m4.t(16, 6.6, 16), COL.amarillo);
  pon("botonera", caja(0.7, 0.7, 0.4), m4.t(16, 8.2, 16.7), COL.verde); pon("botonera", caja(0.7, 0.7, 0.4), m4.t(16, 7.1, 16.7), COL.rojo);
  pon("cam", prisma(0.3, 24, 6), m4.t(-27, 0, 26), COL.gris); pon("cam", caja(1.8, 3, 0.7), m4.t(-27, 24, 26), COL.negro);
  persona(pon, q.px, q.pz, 1.75, q.giro);
  const peligro = e.s.guarda === "abierta" && e.s.energia === "viva";
  return {objetos: o, zonas: [{pts: [[-8, 0.05, 11], [8, 0.05, 11], [8, 0.05, 23], [-8, 0.05, 23]], roja: peligro, tenue: !peligro}], lineas: null,
    rotulos: [[[-20, 24, -6], "correa"], [[43, 17.5, 22], "energia"], [[28, 14, 20], "bloqueo"], [q.guarda > 0.5 ? [11, 4.6, 23] : [0, 20.6, 10.4], "guarda"], [[-27, 29, 26], "cámara"]]};
}

function escenaElectrica(e, q) {
  const o = [], pon = (id, malla, M, c, fantasma) => o.push({id, malla, M, c, fantasma}), cerrado = 1 - q.secc / 1.05;
  pon("tablero", caja(76, 1, 66), m4.t(4, -1, 8), COL.hormigon);
  // el gabinete de la celda, con el frente abierto para ver adentro
  pon("celda", caja(11.2, 22, 0.5), m4.t(0, 0, -6), COL.gabinete); pon("celda", caja(0.5, 22, 12), m4.t(-5.6, 0, 0), COL.gabinete);
  pon("celda", caja(0.5, 22, 12), m4.t(5.6, 0, 0), COL.gabinete); pon("celda", caja(11.7, 0.6, 12.4), m4.t(0, 22, 0), COL.gabinete);
  pon("celda", caja(11.2, 1.4, 12), m4.t(0, 0, 0), COL.gris); pon("celda", caja(10.6, 21, 0.4), m4.t(-11.2, 0.6, 6.2), COL.fantasma, true);
  const kit = [-13, 0, 14], t = q.tierra;
  [-3.2, 0, 3.2].forEach((x, i) => {
    pon("barras", prisma(0.42, 6.6, 8), m4.t(x, 15, -1), COL.cobre); pon("barras", prisma(0.42, 6.4, 8), m4.t(x, 1.6, -1), COL.cobre);
    pon("barras", caja(1.1, 0.8, 1.1), m4.t(x, 14.2, -1), COL.plata); pon("barras", caja(1.1, 0.8, 1.1), m4.t(x, 8, -1), COL.plata);
    pon("secc", caja(0.7, 6.2, 0.45), m4.de(m4.t(x, 8.8, -1), m4.rx(q.secc)), mez(COL.plata, COL.rojo, q.tension * cerrado));
    pon("lamp", caja(1.3, 1.3, 0.5), m4.t(x, 20.2, 6), mez(COL.negro, COL.rojo, q.tension));
    // las pinzas de tierra viajan desde el equipo en el suelo hasta su barra
    pon("tierra", caja(1.4, 1, 1.4), m4.t(kit[0] + i * 1.8 + (x - kit[0] - i * 1.8) * t, 0.9 + 4.5 * t + 5 * Math.sin(Math.PI * t), kit[2] + (-1 - kit[2]) * t), COL.tierraC);
  });
  if (t > 0.92) { pon("tierra", caja(8.2, 0.5, 0.5), m4.t(0, 5.7, 0.2), COL.tierraC); pon("tierra", caja(0.5, 5.7, 0.5), m4.t(4.3, 0, 0.6), COL.tierraC); pon("tierra", caja(3, 0.6, 3), m4.t(4.3, 0, 2.4), COL.tierraC); }
  pon("tierra", caja(6, 0.9, 2.2), m4.t(kit[0] + 1.8, 0, kit[2]), mez(COL.tierraC, COL.gris, t));
  // el mando del seccionador, por fuera, con su candado
  pon("mando", caja(0.8, 2.4, 2.4), m4.t(6.2, 9.6, 3), COL.negro);
  pon("mando", caja(0.5, 4.4, 0.6), m4.de(m4.t(6.8, 10.8, 3), m4.rx(q.mando)), COL.rojo);
  conCandado(pon, q, 7.2, 7.4, 3, 1.25, Math.PI / 2);
  // la zona delimitada: los postes suben y la cinta se tiende cuando la cámara ya lo confirmó
  if (q.barrera > 0.03) {
    [[-11, 10], [11, 10], [11, 24], [-11, 24]].forEach(([x, z]) => pon("barrera", prisma(0.4, 7.4 * q.barrera, 8), m4.t(x, 0, z), COL.amarillo));
    if (q.barrera > 0.85) { pon("barrera", caja(22, 0.9, 0.2), m4.t(0, 5.8, 24), COL.cinta); pon("barrera", caja(0.2, 0.9, 14), m4.t(-11, 5.8, 17), COL.cinta); pon("barrera", caja(0.2, 0.9, 14), m4.t(11, 5.8, 17), COL.cinta); pon("barrera", caja(5, 3.2, 0.3), m4.t(-5.5, 2, 24.2), COL.amarillo); }
  }
  pon("cam", prisma(0.25, 13, 6), m4.t(-15, 0, 20), COL.gris); pon("cam", caja(1.5, 2.8, 0.5), m4.t(-15, 13, 20), COL.negro);
  persona(pon, q.px, q.pz, 1.8, q.giro);
  return {objetos: o, zonas: [], lineas: null,
    rotulos: [[[-1, 12.2, 3], "seccionador"], [[9, 15.5, 3], "candado_mando"], [[0, 24.6, 6], "tension"], [t > 0.5 ? [0, 3.4, 4] : [-11, 3.8, 14], "tierra"], [[-15, 17.6, 20], "cámara"]]};
}

function escenaExcavadora(e, q) {
  const o = [], pon = (id, malla, M, c, fantasma) => o.push({id, malla, M, c, fantasma}), dentro = e.s.zona === "ocupada", arriba = e.s.implementos === "levantados";
  pon("tablero", caja(150, 1, 100), m4.t(14, -1, 4), COL.suelo);
  [-9, 9].forEach(z => { pon("orugas", caja(36, 4.2, 6), m4.t(0, 0, z), COL.oruga); pon("orugas", caja(32, 1, 6.6), m4.t(0, 4.2, z), COL.negro); });
  pon("cuerpo", caja(24, 7, 17), m4.t(-2, 5.2, 0), COL.amarillo); pon("cuerpo", caja(7, 7.4, 17.4), m4.t(-14.5, 5, 0), COL.gris);
  pon("cuerpo", caja(8.4, 9.6, 7.4), m4.t(4.4, 12.2, -4.6), COL.amarillo); pon("cuerpo", caja(0.3, 5.6, 5.6), m4.t(8.7, 14.6, -4.6), COL.vidrio);
  pon("cuerpo", caja(6, 5.6, 0.3), m4.t(4.4, 14.6, -0.8), COL.vidrio);
  pon("motor", prisma(0.7, 4.6, 8), m4.t(-9, 12.2, 5), COL.negro);
  if (q.humo > 0.04) [[0, 17.4, 1.5], [0.8, 20, 2], [1.9, 23, 2.6]].forEach(([dx, y, k], i) => { const s = k * q.humo, sube = (e.reloj * 1.4 + i * 0.33) % 1; pon("motor", caja(s, s, s), m4.t(-9 + dx + sube, y + sube * 2.4, 5), COL.humo); });
  // la pluma, el brazo y el balde
  const M1 = m4.de(m4.t(8, 10, 3.6), m4.rz(-(Math.PI / 2 - q.e1)));
  pon("pluma", caja(2.6, 26, 2.8), M1, COL.amarillo);
  pon("manguera", caja(0.8, 17, 0.8), m4.de(M1, m4.t(-1.9, 4, 0)), mez(COL.naranja, COL.tierraC, q.manguera));
  const M2 = m4.de(M1, m4.t(0, 26, 0), m4.rz(-q.baja));
  pon("pluma", caja(2.2, 16, 2.4), M2, COL.amarillo);
  pon("pluma", caja(5, 4.4, 5.6), m4.de(M2, m4.t(0, 15, 0), m4.rz(0.9)), COL.oruga);
  const balde = m4.ap(M2, [0, 17, 0]);
  // la palanca de seguridad y el manómetro, a la vista en el costado
  pon("palanca", caja(1.4, 1, 1.4), m4.t(2, 12.2, 3), COL.negro);
  pon("palanca", caja(0.5, 4, 0.5), m4.de(m4.t(2, 13, 3), m4.rz(q.palanca)), COL.rojo);
  conCandado(pon, q, 2, 13.6, 4.4, 1.15);
  pon("presion", prisma(1.7, 0.6, 14), m4.de(m4.t(-5, 9, 8.6), m4.rx(Math.PI / 2)), mez(COL.verde, COL.rojo, q.presion));
  pon("cam", prisma(0.3, 20, 6), m4.t(46, 0, -26), COL.gris); pon("cam", caja(0.6, 3, 1.6), m4.t(46, 20, -26), COL.negro);
  persona(pon, q.px, q.pz, 1.8, q.giro);
  return {objetos: o, zonas: [{pts: [[13, 0.05, -6], [42, 0.05, -6], [42, 0.05, 13], [13, 0.05, 13]], roja: dentro && arriba, tenue: !arriba}], lineas: null,
    rotulos: [[[balde[0] + 4, balde[1] + 9, 3.6], "implementos"], [[-17, 21, 10], "motor"], [[6, 27, -6], "palanca_seguridad"], [[-9, 2.2, 15], "presion_hidraulica"],
      [[30, 1.2, 19], "zona"], [[46, 25, -26], "cámara"]]};
}
const ESCENAS = {demo: [escenaDemo, {az: 0.42, el: 0.5, dist: 72, obj: [3, 3, 9]}], brazo: [escenaBrazo, {az: -0.62, el: 0.4, dist: 142, obj: [8, 21, 0]}], mineria: [escenaCorrea, {az: 0.4, el: 0.3, dist: 88, obj: [7, 9, 8]}], electrica: [escenaElectrica, {az: 0.42, el: 0.22, dist: 50, obj: [1.5, 11.5, 4]}],
  construccion: [escenaExcavadora, {az: 0.5, el: 0.27, dist: 92, obj: [14, 13, 3]}]};

// ─── El visor de la landing ─────────────────────────────────────────────────
const P = {fantasma: ["rgba(212,255,158,.035)", "rgba(156,166,150,.42)"], cara: "rgba(0,0,0,.35)",
  zonaRoja: ["rgba(255,68,51,.26)", "#ff4433"], zonaTenue: ["rgba(238,242,233,.025)", "rgba(156,166,150,.32)"], zonaOk: ["rgba(212,255,158,.1)", "#d4ff9e"], linea: "rgba(212,255,158,.4)",
  rotRojo: "#ff4433", rotCambio: "#d4ff9e", rotNeutro: "rgba(5,6,5,.82)", rotTexto: "#0a0c0a", rotTextoNeutro: "#eef2e9", rotBorde: "#3d4439", marca: "#ffc24d", pov: "rgba(212,255,158,.75)", povTexto: "#eef2e9", povPunto: "#ff4433",
  fuente: '500 12px "IBM Plex Mono", ui-monospace, "SF Mono", Menlo, monospace', radio: 2};
const HUECOS = [-4, -3, -2, -1, 0, 1, 2, 3, 4].flatMap(i => [-5, -4, -3, -2, -1, 0, 1, 2, 3, 4, 5].map(j => [i * 70, j * 27])).sort((a, b) => Math.hypot(a[0], a[1] * 2) - Math.hypot(b[0], b[1] * 2));
const CAPA = {cam: "factum", us: "factum", esp: "factum", rele: "factum", puls: "factum", placa: "factum", l298n: "factum", persona: "persona", mano: "persona", operario: "persona", tablero: "piso"};
const nombre = (c, s) => (c.nombres[s] || [s])[0];
const valor = (c, s, v) => { const n = c.nombres[s]; return n && n[2] ? `${String(v).replace(".", ",")} ${n[2]}` : (n && n[1][v]) || v; };
const dicho = (c, s, v) => `${nombre(c, s)}: ${valor(c, s, v)}`;
export const CALMO = matchMedia("(prefers-reduced-motion: reduce)").matches;

export class Visor {
  static todos = new Set();
  static andando = false;
  // Un solo reloj para todos los lienzos: cada uno dibuja solo mientras se ve.
  static arrancar() {
    if (Visor.andando) return; Visor.andando = true;
    let antes = 0;
    const paso = t => { const dt = Math.min(0.1, (t - antes) / 1000 || 0); antes = t; Visor.todos.forEach(v => { if (v.visible) v.cuadro(dt); }); requestAnimationFrame(paso); };
    requestAnimationFrame(paso);
  }

  // op: rotulos · centro [x, y] del lienzo donde cae el objetivo · escala · techo y suelo (px sin rótulos)
  //     vaiven (rad que oscila la vista general) · orbita (rad/s) · arrastre (girar con el puntero)
  //     foco (px): fija la distancia focal en vez de sacarla del tamaño del lienzo
  constructor(lienzo, casos, caso, op = {}) {
    this.cv = lienzo; this.casos = casos;
    this.op = {rotulos: true, centro: [0.5, 0.5], escala: 1, techo: 16, suelo: 16, vaiven: 0, orbita: 0, arrastre: false, ...op};
    this.capas = {rotulos: this.op.rotulos, zonas: true, factum: true, persona: true, maquina: true, piso: true};
    this.vista = {az: 0, el: 0.4, dist: 100, obj: [0, 0, 0]}; this.meta = {az: 0, el: 0.4, dist: 100, obj: [0, 0, 0]};
    this.fase = 0.25; this.reloj = 0; this.cinta = 0; this.visible = false; this.sucio = true; this.alCambiar = null;
    this.elegir(caso);
    new IntersectionObserver(([e]) => { this.visible = e.isIntersecting; this.sucio = true; }, {rootMargin: "120px"}).observe(lienzo);
    new ResizeObserver(() => { this.sucio = true; }).observe(lienzo);
    document.fonts?.ready.then(() => { this.sucio = true; });
    if (this.op.arrastre) this.escucharPuntero();
    Visor.todos.add(this); Visor.arrancar();
  }

  get tramos() { return this.casos[this.caso].tramos; }
  get estado() { return this.tramos[this.posVis]; }

  elegir(caso, tramo = 0) {
    clearTimeout(this.espera);
    this.caso = caso; this.pos = this.posVis = tramo; this.pose = null; this.rotOff = {}; this.rotVis = {};
    this.mirar("general", true);
  }

  // La escena va un poco detrás del relato: primero la persona llega a donde va a actuar (`pos`) y recién
  // después cambian los sensores y Factum responde (`posVis`). Así cada tramo se ve como una acción.
  ir(i, deUna) {
    const antes = this.pos; this.pos = Math.max(0, Math.min(this.tramos.length - 1, i | 0));
    clearTimeout(this.espera);
    if (!deUna && !CALMO && this.pos === antes + 1) {
      const camina = (this.tramos[this.pos].donde || "") !== (this.tramos[antes].donde || "");
      this.espera = setTimeout(() => { this.posVis = this.pos; this.sucio = true; this.alCambiar?.(); }, camina ? 1100 : 350);
    } else this.posVis = this.pos;
    this.sucio = true; this.alCambiar?.();
  }

  entorno() {
    const E = this.tramos[this.posVis], t = this.tramos[this.pos];
    return {E, e: {s: E.sensores, hecho: p => E.estados[p] === "verificado", ot: true, completa: E.completa, fase: this.fase, reloj: this.reloj, cinta: this.cinta, marca: E.marca, donde: t.donde}};
  }

  // Acerca la pose a su objetivo. `dt` en segundos; sin `dt`, salta de una vez.
  seguir(e, dt) {
    const objetivo = OBJETIVO[this.caso](e), q = this.pose || (this.pose = {...objetivo}); this.enMovimiento = false;
    for (const k in objetivo) { const d = objetivo[k] - q[k]; if (dt === undefined || Math.abs(d) < 0.004) q[k] = objetivo[k]; else { q[k] += d * (1 - Math.exp(-dt * 4)); this.enMovimiento = true; } }
    return q;
  }
  escena() { const {e} = this.entorno(); return ESCENAS[this.caso][0](e, this.pose || this.seguir(e)); }

  vistaDe(nombreVista) {
    const b = ESCENAS[this.caso][1], obj = [...b.obj];
    if (nombreVista === "frontal") return {az: 0, el: 0.14, dist: b.dist, obj};
    if (nombreVista === "lateral") return {az: Math.PI / 2, el: 0.16, dist: b.dist, obj};
    if (nombreVista === "cenital") return {az: 0.001, el: 1.45, dist: b.dist * 1.15, obj};
    if (nombreVista === "camara") {
      const r = this.escena().rotulos.find(x => x[1] === "cámara"), d = v3.sub([r[0][0], r[0][1] - 4.5, r[0][2]], obj), dist = Math.hypot(...d);
      return {az: Math.atan2(d[0], d[2]), el: Math.asin(d[1] / dist), dist, obj};
    }
    return {az: b.az, el: b.el, dist: b.dist, obj};
  }
  mirar(nombreVista, deUna) {
    this.vistaActiva = nombreVista; Object.assign(this.meta, this.vistaDe(nombreVista));
    if (deUna || CALMO) Object.assign(this.vista, this.meta, {obj: [...this.meta.obj]});
    this.sucio = true;
  }
  acercarVista(dt) {
    const {vista, meta} = this, k = 1 - Math.exp(-dt * 5); let mov = false;
    ["az", "el", "dist"].forEach(c => { let d = meta[c] - vista[c]; if (c === "az") d = Math.atan2(Math.sin(d), Math.cos(d)); if (Math.abs(d) > (c === "dist" ? 0.02 : 0.0005)) { vista[c] += d * k; mov = true; } else vista[c] += d; });
    vista.obj = vista.obj.map((x, i) => { const d = meta.obj[i] - x; if (Math.abs(d) > 0.01) { mov = true; return x + d * k; } return meta.obj[i]; });
    return mov;
  }

  escucharPuntero() {
    const cv = this.cv; let a = null;
    cv.addEventListener("pointerdown", e => { a = [e.clientX, e.clientY, this.vista.az, this.vista.el]; try { cv.setPointerCapture(e.pointerId); } catch (_) { /* puntero sintético */ } });
    cv.addEventListener("pointermove", e => {
      if (!a) return;
      if (Math.hypot(e.clientX - a[0], e.clientY - a[1]) > 3) this.vistaActiva = "libre";
      this.vista.az = this.meta.az = a[2] - (e.clientX - a[0]) * 0.008; this.vista.el = this.meta.el = Math.min(1.5, Math.max(0.05, a[3] + (e.clientY - a[1]) * 0.008)); this.sucio = true;
    });
    ["pointerup", "pointercancel"].forEach(n => cv.addEventListener(n, () => { a = null; }));
    cv.addEventListener("dblclick", () => this.mirar("general"));
  }

  cuadro(dt) {
    const {e} = this.entorno();
    if (CALMO) { if (this.sucio) { this.pose = null; this.seguir(e); this.dibujar(); } return; }
    const q = this.seguir(e, dt), k = this.caso;
    const gira = k === "brazo" && q.viva > 0.01, humea = k === "construccion" && q.humo > 0.04, corre = (k === "mineria" || k === "demo") && q.marcha > 0.01;
    if (this.vistaActiva === "general") {
      if (this.op.orbita) this.meta.az += dt * this.op.orbita;
      else if (this.op.vaiven) this.meta.az = ESCENAS[k][1].az + Math.sin(this.reloj * 0.22) * this.op.vaiven;
    }
    const mueveVista = this.acercarVista(dt);
    if (gira) this.fase = (this.fase + dt / 7 * q.viva) % 1;
    if (corre) this.cinta = (this.cinta + dt * (k === "demo" ? 11 : 17) * q.marcha) % (k === "demo" ? 60 : 75);
    this.reloj += dt;
    if (this.sucio || this.enMovimiento || gira || humea || corre || mueveVista || this.rotulosMoviendo) this.dibujar();
  }

  dibujar() {
    const cv = this.cv; if (!cv.clientWidth) return;
    this.sucio = false;
    const dpr = Math.min(2, window.devicePixelRatio || 1), W = cv.clientWidth, H = cv.clientHeight, {vista, op, capas} = this;
    if (cv.width !== Math.round(W * dpr) || cv.height !== Math.round(H * dpr)) { cv.width = Math.round(W * dpr); cv.height = Math.round(H * dpr); }
    const g = cv.getContext("2d"); g.setTransform(dpr, 0, 0, dpr, 0, 0); g.clearRect(0, 0, W, H);
    const T0 = vista.obj, cam = [T0[0] + vista.dist * Math.cos(vista.el) * Math.sin(vista.az), T0[1] + vista.dist * Math.sin(vista.el), T0[2] + vista.dist * Math.cos(vista.el) * Math.cos(vista.az)];
    const fwd = v3.norm(v3.sub(T0, cam)), der = v3.norm(v3.cross(fwd, [0, 1, 0])), arr = v3.cross(der, fwd);
    const f = op.foco || Math.min(H * 1.25, W * 0.78) * op.escala, cx = W * op.centro[0], cy = H * op.centro[1];
    const proy = p => { const d = v3.sub(p, cam), z = v3.dot(d, fwd); return z < 1 ? null : [cx + f * v3.dot(d, der) / z, cy - f * v3.dot(d, arr) / z, z]; };
    const {E} = this.entorno(), escena = this.escena(), pov = this.vistaActiva === "camara";
    const luz = v3.norm([0.35, 0.85, 0.4]), caras = [];
    escena.objetos.forEach(o => {
      if (!capas[CAPA[o.id] || "maquina"] || (pov && o.id === "cam")) return;
      const vs = o.malla.v.map(p => m4.ap(o.M, p)), centro = vs.reduce((a, p) => [a[0] + p[0], a[1] + p[1], a[2] + p[2]], [0, 0, 0]).map(x => x / vs.length);
      o.malla.f.forEach(idx => {
        const pts = idx.map(i => vs[i]), c = pts.reduce((a, p) => [a[0] + p[0], a[1] + p[1], a[2] + p[2]], [0, 0, 0]).map(x => x / pts.length);
        let n = v3.norm(v3.cross(v3.sub(pts[1], pts[0]), v3.sub(pts[2], pts[0])));
        if (v3.dot(n, v3.sub(c, centro)) < 0) n = n.map(x => -x);
        if (!o.fantasma && v3.dot(n, v3.sub(cam, c)) <= 0) return;
        const p2 = pts.map(proy); if (p2.some(p => !p)) return;
        const k = 0.5 + 0.5 * Math.max(0, v3.dot(n, luz));
        caras.push({id: o.id, p2, z: p2.reduce((a, p) => a + p[2], 0) / p2.length, color: o.c.map(x => Math.round(x * k)), fantasma: o.fantasma});
      });
    });
    caras.sort((a, b) => (b.id === "tablero") - (a.id === "tablero") || b.z - a.z);
    const trazo = (p2, relleno, borde, dash) => { g.beginPath(); p2.forEach((p, i) => i ? g.lineTo(p[0], p[1]) : g.moveTo(p[0], p[1])); g.closePath(); if (relleno) { g.fillStyle = relleno; g.fill(); } if (borde) { g.setLineDash(dash || []); g.strokeStyle = borde; g.stroke(); g.setLineDash([]); } };
    let zonasPintadas = !capas.zonas;
    const pintarZonas = () => { if (zonasPintadas) return; zonasPintadas = true; escena.zonas.forEach(z => { const p2 = z.pts.map(proy); if (p2.some(p => !p)) return; g.lineWidth = 2; trazo(p2, z.roja ? P.zonaRoja[0] : z.tenue ? P.zonaTenue[0] : P.zonaOk[0], z.roja ? P.zonaRoja[1] : z.tenue ? P.zonaTenue[1] : P.zonaOk[1], [7, 5]); }); };
    g.lineWidth = 1;
    caras.forEach(c => {
      if (c.id !== "tablero") pintarZonas();
      g.lineWidth = 1;
      if (c.fantasma) trazo(c.p2, P.fantasma[0], P.fantasma[1]); else trazo(c.p2, `rgb(${c.color})`, P.cara);
    });
    pintarZonas();
    if (escena.lineas && capas.factum && !pov) { g.setLineDash([5, 6]); g.strokeStyle = P.linea; const a = proy(escena.lineas[0]); escena.lineas[1].forEach(p => { const q = proy(p); if (a && q) { g.beginPath(); g.moveTo(a[0], a[1]); g.lineTo(q[0], q[1]); g.stroke(); } }); g.setLineDash([]); }
    this.rotulosMoviendo = false;
    const techo = op.techo + 14, suelo = H - op.suelo - 14 - (pov ? 34 : 0);   // la vista de la cámara escribe su leyenda abajo
    if (capas.rotulos) {
      g.font = P.fuente; g.textBaseline = "middle"; g.textAlign = "center";
      const c0 = this.casos[this.caso], enCurso = E.actual, puestos = [];
      // Los rótulos más importantes se ubican primero. Cada uno conserva su lugar mientras siga libre y se desliza
      // cuando tiene que cambiarlo, para que no salten de un cuadro a otro.
      escena.rotulos.map(([p3, sensor, alarma]) => {
        if (pov && sensor === "cámara") return null;
        const p = proy(p3); if (!p) return null;
        const esSensor = sensor in E.sensores, espera = enCurso && enCurso.sensor && enCurso.sensor.id === sensor && E.sensores[sensor] !== enCurso.sensor.espera;
        const deCamara = enCurso && enCurso.tipo_evidencia === "camara" && sensor === "cámara";
        const texto = esSensor ? dicho(c0, sensor, E.sensores[sensor]) + (espera && W >= 480 ? ` → paso ${enCurso.orden}: ${valor(c0, sensor, enCurso.sensor.espera)}` : "")   /* en el celular no cabe: queda el borde ámbar */ : sensor + (deCamara ? ` → paso ${enCurso.orden}` : "");
        const rojo = alarma || (esSensor && E.enAlerta.includes(sensor)), cambio = esSensor && E.sensores[sensor] !== c0.reposo[sensor], marca = espera || deCamara;
        return {clave: this.caso + ":" + sensor, p, texto, rojo, cambio, marca, w: g.measureText(texto).width + 16, prio: (rojo ? 4 : 0) + (marca ? 2 : 0) + (cambio ? 1 : 0)};
      }).filter(Boolean).sort((a, b) => b.prio - a.prio).forEach(r => {
        const x0 = Math.min(Math.max(r.p[0], r.w / 2 + 8), W - r.w / 2 - 8), y0 = Math.min(Math.max(r.p[1], techo), suelo);
        const libre = ([dx, dy]) => { const x = x0 + dx, y = y0 + dy; return y >= techo && y <= suelo && x >= r.w / 2 + 8 && x <= W - r.w / 2 - 8 && !puestos.some(o => Math.abs(o.x - x) < (o.w + r.w) / 2 + 4 && Math.abs(o.y - y) < 26); };
        const off = [[0, 0], this.rotOff[r.clave], ...HUECOS].find(o => o && libre(o)) || [0, 0];
        this.rotOff[r.clave] = off;
        const x = x0 + off[0], y = y0 + off[1], v = this.rotVis[r.clave] && !CALMO ? this.rotVis[r.clave].map((a, i) => a + ([x, y][i] - a) * 0.25) : [x, y];
        this.rotVis[r.clave] = v; if (Math.hypot(v[0] - x, v[1] - y) > 0.6) this.rotulosMoviendo = true;
        puestos.push({x, y, w: r.w});
        const fondoR = r.rojo ? P.rotRojo : r.cambio ? P.rotCambio : P.rotNeutro, neutro = !r.rojo && !r.cambio;
        if (Math.hypot(v[0] - r.p[0], v[1] - r.p[1]) > 14) {
          g.strokeStyle = neutro ? P.rotBorde : fondoR; g.lineWidth = 1.5; g.beginPath(); g.moveTo(r.p[0], r.p[1]); g.lineTo(v[0], v[1]); g.stroke();
          g.fillStyle = neutro ? P.rotBorde : fondoR; g.beginPath(); g.arc(r.p[0], r.p[1], 3, 0, 2 * Math.PI); g.fill();
        }
        g.fillStyle = fondoR; g.beginPath(); g.roundRect(v[0] - r.w / 2, v[1] - 11, r.w, 22, P.radio); g.fill();
        if (neutro) { g.lineWidth = 1; g.strokeStyle = P.rotBorde; g.stroke(); }
        if (r.marca) { g.lineWidth = 2.5; g.strokeStyle = P.marca; g.beginPath(); g.roundRect(v[0] - r.w / 2, v[1] - 11, r.w, 22, P.radio); g.stroke(); }
        g.fillStyle = neutro ? P.rotTextoNeutro : P.rotTexto; g.fillText(r.texto, v[0], v[1] + 0.5);
      });
    }
    if (pov) {
      const m = 18, l = 26, y1 = op.techo + 4, y2 = H - op.suelo - 4;
      g.strokeStyle = P.pov; g.lineWidth = 2; g.beginPath();
      [[m, y1, 1, 1], [W - m, y1, -1, 1], [m, y2, 1, -1], [W - m, y2, -1, -1]].forEach(([x, y, sx, sy]) => { g.moveTo(x, y + sy * l); g.lineTo(x, y); g.lineTo(x + sx * l, y); });
      g.stroke();
      g.font = P.fuente; g.textAlign = "left"; g.textBaseline = "middle"; g.fillStyle = P.povPunto; g.beginPath(); g.arc(m + 12, y2 - 14, 4.5, 0, 2 * Math.PI); g.fill();
      g.fillStyle = P.povTexto; g.fillText(W < 520 ? "Lo que ve la cámara de Factum" : "Lo que ve la cámara de Factum · el juez responde sobre este cuadro", m + 24, y2 - 13.5);
    }
  }
}
