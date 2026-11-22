/* anotaciones.js · comentarios por sección para leer y anotar desde el teléfono. Sin dependencias ni
   servidor: cada comentario se guarda en el navegador de quien lee (localStorage, por página) hasta
   que lo envía. «Enviar» abre la hoja de compartir del teléfono con todos los comentarios en
   markdown, cada uno con el título y el id de su sección, para pegarlos en el thread del agente.
   El botón de comentario va en el título. Se puede comentar cada section[id] del artículo, cada .paso[id] y cada elemento con
   data-comentar e id. Si la página trae <meta name="fuente" content="ruta">, el envío la incluye
   para que el agente sepa qué archivo editar. Los estilos están en anotaciones.css. */
(function () {
  'use strict';

  var clave = 'notas:' + location.pathname;
  var notas = leer();
  var fuente = document.querySelector('meta[name="fuente"]');

  function leer() {
    try { return JSON.parse(localStorage.getItem(clave)) || {}; } catch (e) { return {}; }
  }
  function guardar() {
    try { localStorage.setItem(clave, JSON.stringify(notas)); } catch (e) { /* modo privado: queda en memoria */ }
    pintarBarra();
  }

  function titulo(el) {
    var h = el.querySelector('h2, h3');
    return h ? h.textContent.replace(/\s+/g, ' ').trim() : el.id;
  }
  function ancla(el) {
    return el.querySelector('.paso-h') || el.querySelector('h2, h3');
  }

  var objetivos = [].slice.call(document.querySelectorAll('article section[id], article .paso[id], article [data-comentar][id]'));
  var orden = objetivos.map(function (el) { return el.id; });

  var ICONO = '<svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true"><path d="M4 5.5A2.5 2.5 0 0 1 6.5 3h11A2.5 2.5 0 0 1 20 5.5v8a2.5 2.5 0 0 1-2.5 2.5H10l-4.2 3.6c-.5.4-1.3.1-1.3-.6V16A2.5 2.5 0 0 1 4 13.5z" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/><path d="M8.5 8.5h7M8.5 11.5h4.5" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>';

  // El botón va dentro del título, arriba a la derecha; el comentario y el formulario, debajo.
  objetivos.forEach(function (el) {
    var a = ancla(el);
    if (!a) return;
    var zona = document.createElement('div');
    zona.className = 'notas-zona';
    a.insertAdjacentElement('afterend', zona);
    var b = document.createElement('button');
    b.type = 'button';
    b.className = 'anotar';
    b.innerHTML = ICONO;
    b.addEventListener('click', function () { formulario(el, zona, notas[el.id] ? notas[el.id].texto : ''); });
    a.classList.add('nota-ancla');
    a.appendChild(b);
    el._anotar = b;
    pintar(el, zona);
  });

  function pintar(el, zona) {
    zona.innerHTML = '';
    var n = notas[el.id];
    var b = el._anotar;
    if (b) {
      b.classList.toggle('con-nota', !!n);
      b.setAttribute('aria-label', (n ? 'Editar tu comentario sobre ' : 'Comentar ') + titulo(el));
      b.title = n ? 'Editar comentario' : 'Comentar';
    }
    if (n) {
      var caja = document.createElement('div');
      caja.className = 'nota-c';
      var t = document.createElement('p');
      t.textContent = n.texto;
      var pie = document.createElement('div');
      pie.className = 'nota-c__pie';
      var f = document.createElement('span');
      f.textContent = 'Tu comentario · ' + new Date(n.fecha).toLocaleString('es-CL', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' });
      pie.appendChild(f);
      pie.appendChild(boton('Editar', function () { formulario(el, zona, n.texto); }));
      pie.appendChild(boton('Borrar', function () {
        if (!confirm('¿Borrar este comentario?')) return;
        delete notas[el.id]; guardar(); pintar(el, zona);
      }));
      caja.appendChild(t);
      caja.appendChild(pie);
      zona.appendChild(caja);
    }
  }

  function formulario(el, zona, texto) {
    zona.innerHTML = '';
    var f = document.createElement('div');
    f.className = 'nota-form';
    var area = document.createElement('textarea');
    area.value = texto;
    area.rows = 4;
    area.placeholder = 'Qué cambiarías, qué no entiendes o qué decides sobre «' + titulo(el) + '»';
    area.setAttribute('aria-label', 'Comentario sobre ' + titulo(el));
    var acciones = document.createElement('div');
    acciones.className = 'nota-form__acciones';
    acciones.appendChild(boton('Cancelar', function () { pintar(el, zona); }));
    var ok = boton('Guardar', function () {
      var v = area.value.trim();
      if (v) notas[el.id] = { texto: v, fecha: Date.now(), titulo: titulo(el) };
      else delete notas[el.id];
      guardar();
      pintar(el, zona);
    });
    ok.className = 'pri';
    acciones.appendChild(ok);
    f.appendChild(area);
    f.appendChild(acciones);
    zona.appendChild(f);
    area.focus();
  }

  function boton(texto, accion) {
    var b = document.createElement('button');
    b.type = 'button';
    b.textContent = texto;
    b.addEventListener('click', accion);
    return b;
  }

  function markdown() {
    var ids = Object.keys(notas).sort(function (a, b) { return orden.indexOf(a) - orden.indexOf(b); });
    var l = ['Comentarios sobre «' + document.title + '»', location.href.split('#')[0]];
    if (fuente) l.push('Fuente: ' + fuente.content);
    ids.forEach(function (id) {
      l.push('', '## ' + notas[id].titulo + ' (#' + id + ')', notas[id].texto);
    });
    return l.join('\n');
  }

  function copiar(texto) {
    if (navigator.clipboard && window.isSecureContext) return navigator.clipboard.writeText(texto);
    return new Promise(function (ok, falla) {
      var t = document.createElement('textarea');
      t.value = texto;
      t.style.position = 'fixed';
      t.style.opacity = '0';
      document.body.appendChild(t);
      t.select();
      var hecho = false;
      try { hecho = document.execCommand('copy'); } catch (e) { hecho = false; }
      document.body.removeChild(t);
      if (hecho) ok(); else falla(new Error('No se pudo copiar'));
    });
  }

  var barra = document.createElement('div');
  barra.className = 'notas-barra';
  barra.setAttribute('role', 'region');
  barra.setAttribute('aria-label', 'Tus comentarios');
  var cuenta = document.createElement('span');
  var enviar = boton('Enviar', function () {
    var texto = markdown();
    if (navigator.share) {
      navigator.share({ title: 'Comentarios · ' + document.title, text: texto }).catch(function () {});
    } else {
      copiar(texto).then(function () { aviso(enviar, 'Copiado'); }, function () { aviso(enviar, 'No se pudo copiar'); });
    }
  });
  enviar.className = 'pri';
  var copiarB = boton('Copiar', function () {
    copiar(markdown()).then(function () { aviso(copiarB, 'Copiado'); }, function () { aviso(copiarB, 'No se pudo'); });
  });
  var vaciar = boton('Vaciar', function () {
    if (!confirm('¿Borrar todos tus comentarios de esta página? Hazlo después de enviarlos.')) return;
    notas = {}; guardar();
    objetivos.forEach(function (el) {
      var z = el.querySelector('.notas-zona');
      if (z) pintar(el, z);
    });
  });
  barra.appendChild(cuenta);
  barra.appendChild(enviar);
  barra.appendChild(copiarB);
  barra.appendChild(vaciar);
  document.body.appendChild(barra);

  function aviso(b, texto) {
    var antes = b.textContent;
    b.textContent = texto;
    setTimeout(function () { b.textContent = antes; }, 1800);
  }

  function pintarBarra() {
    var n = Object.keys(notas).length;
    barra.hidden = n === 0;
    cuenta.textContent = n === 1 ? '1 comentario' : n + ' comentarios';
  }
  pintarBarra();
})();
