/* documento.js · comportamiento de la plantilla DOCUMENTO. Sin dependencias ni colores: el estilo
   de lo que dibuja (líneas del diagrama) sale de documento.css.
   1. Resalta en el índice la sección visible.
   2. Cierra el índice del teléfono al elegir una sección.
   3. Agrega «Copiar» a cada bloque de código (.codigo pre).
   4. Selector de caso: body[data-caso] y botones [data-elige].
   5. Dibuja las líneas del diagrama de carriles entre nodos (data-a="id-destino"). */
(function () {
  'use strict';

  var enlaces = [].slice.call(document.querySelectorAll('.indice a'));
  var secciones = [].slice.call(document.querySelectorAll('article [id]')).filter(function (s) {
    return enlaces.some(function (a) { return a.hash === '#' + s.id; });
  });
  if ('IntersectionObserver' in window && secciones.length) {
    var io = new IntersectionObserver(function (entradas) {
      entradas.forEach(function (e) {
        if (!e.isIntersecting) return;
        enlaces.forEach(function (a) { a.classList.toggle('on', a.hash === '#' + e.target.id); });
      });
    }, { rootMargin: '-15% 0px -75% 0px' });
    secciones.forEach(function (s) { io.observe(s); });
  }

  [].forEach.call(document.querySelectorAll('details.indice-m'), function (d) {
    d.addEventListener('click', function (e) {
      if (e.target.closest('a')) d.open = false;
    });
  });

  function copiarTexto(texto) {
    if (navigator.clipboard && window.isSecureContext) return navigator.clipboard.writeText(texto);
    return new Promise(function (ok, falla) {
      var t = document.createElement('textarea');
      t.value = texto;
      t.setAttribute('readonly', '');
      t.style.position = 'fixed';
      t.style.opacity = '0';
      document.body.appendChild(t);
      t.select();
      var hecho = false;
      try { hecho = document.execCommand('copy'); } catch (err) { hecho = false; }
      document.body.removeChild(t);
      if (hecho) ok(); else falla(new Error('No se pudo copiar'));
    });
  }

  [].forEach.call(document.querySelectorAll('.codigo'), function (bloque) {
    var pre = bloque.querySelector('pre');
    if (!pre) return;
    var boton = document.createElement('button');
    boton.type = 'button';
    boton.className = 'copiar';
    boton.textContent = 'Copiar';
    boton.setAttribute('aria-label', 'Copiar el código');
    boton.addEventListener('click', function () {
      copiarTexto(pre.innerText.replace(/\n$/, '')).then(function () {
        boton.textContent = 'Copiado';
        boton.classList.add('ok');
      }, function () {
        boton.textContent = 'Selecciónalo y copia';
      });
      setTimeout(function () { boton.textContent = 'Copiar'; boton.classList.remove('ok'); }, 2000);
    });
    bloque.appendChild(boton);
  });

  var botonesCaso = [].slice.call(document.querySelectorAll('[data-elige]'));
  botonesCaso.forEach(function (boton) {
    boton.addEventListener('click', function () {
      document.body.dataset.caso = boton.dataset.elige;
      botonesCaso.forEach(function (otro) { otro.setAttribute('aria-pressed', String(otro === boton)); });
      dibujarTodos();
    });
  });

  var SVG = 'http://www.w3.org/2000/svg';

  function dibujar(grilla) {
    var svg = grilla.querySelector('svg.lineas');
    if (!svg) {
      svg = document.createElementNS(SVG, 'svg');
      svg.setAttribute('class', 'lineas');
      svg.setAttribute('aria-hidden', 'true');
      grilla.insertBefore(svg, grilla.firstChild);
    }
    while (svg.firstChild) svg.removeChild(svg.firstChild);
    if (getComputedStyle(svg).display === 'none') return;

    var base = grilla.getBoundingClientRect();
    svg.setAttribute('viewBox', '0 0 ' + base.width + ' ' + base.height);

    function caja(el) {
      var r = el.getBoundingClientRect();
      return { x: r.left - base.left, y: r.top - base.top, w: r.width, h: r.height };
    }
    function visible(el) { return el && el.getClientRects().length > 0; }

    [].forEach.call(grilla.querySelectorAll('.nodo[data-a]'), function (desde) {
      if (!visible(desde)) return;
      desde.getAttribute('data-a').split(/\s+/).forEach(function (id) {
        var hasta = document.getElementById(id);
        if (!visible(hasta)) return;
        var a = caja(desde), b = caja(hasta), d;
        var aCx = a.x + a.w / 2, bCx = b.x + b.w / 2;
        if (Math.abs(aCx - bCx) < 4) {
          var abajo = b.y > a.y;
          var y1 = abajo ? a.y + a.h : a.y, y2 = abajo ? b.y - 4 : b.y + b.h + 4;
          d = 'M' + aCx + ' ' + y1 + 'V' + y2;
        } else {
          var adelante = b.x > a.x;
          var x1 = adelante ? a.x + a.w : a.x, x2 = adelante ? b.x - 4 : b.x + b.w + 4;
          var y1h = a.y + a.h / 2, y2h = b.y + b.h / 2;
          var xm = (x1 + x2) / 2;
          d = Math.abs(y1h - y2h) < 2
            ? 'M' + x1 + ' ' + y1h + 'H' + x2
            : 'M' + x1 + ' ' + y1h + 'H' + xm + 'V' + y2h + 'H' + x2;
        }
        var p = document.createElementNS(SVG, 'path');
        p.setAttribute('d', d);
        p.setAttribute('marker-end', 'url(#punta-' + grilla.dataset.svgId + ')');
        if (hasta.classList.contains('despues') || desde.hasAttribute('data-luego')) p.setAttribute('class', 'luego');
        svg.appendChild(p);
      });
    });

    var defs = document.createElementNS(SVG, 'defs');
    var m = document.createElementNS(SVG, 'marker');
    m.setAttribute('id', 'punta-' + grilla.dataset.svgId);
    m.setAttribute('viewBox', '0 0 8 8');
    m.setAttribute('refX', '7');
    m.setAttribute('refY', '4');
    m.setAttribute('markerWidth', '7');
    m.setAttribute('markerHeight', '7');
    m.setAttribute('orient', 'auto');
    var punta = document.createElementNS(SVG, 'path');
    punta.setAttribute('d', 'M1 1 7 4 1 7');
    m.appendChild(punta);
    defs.appendChild(m);
    svg.insertBefore(defs, svg.firstChild);
  }

  var grillas = [].slice.call(document.querySelectorAll('.carriles__g'));
  grillas.forEach(function (g, i) { g.dataset.svgId = String(i); });
  function dibujarTodos() { grillas.forEach(dibujar); }

  if (grillas.length) {
    var pendiente = 0;
    window.addEventListener('resize', function () {
      cancelAnimationFrame(pendiente);
      pendiente = requestAnimationFrame(dibujarTodos);
    });
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(dibujarTodos);
    window.addEventListener('load', dibujarTodos);
    dibujarTodos();
  }
})();
