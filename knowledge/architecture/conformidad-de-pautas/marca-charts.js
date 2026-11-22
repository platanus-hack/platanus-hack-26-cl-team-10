/* marca-charts.js · Chart.js con la marca del proyecto: la fuente y los colores de marca.css,
   textos de 15 px o más, sin grilla vertical. Expone window.MARCA (colores, sinGrilla y el plugin etiquetas). */
(function(){
  if(!window.Chart) return;
  // Los colores salen de las variables de marca.css: el gráfico sigue a la marca sin tocar este archivo.
  var css = getComputedStyle(document.documentElement);
  var v = function(n){ return css.getPropertyValue('--' + n).trim(); };
  var C = window.MARCA = { brand:v('brand'), accent:v('accent'), ink:v('ink'), muted:v('muted'), line:v('line'), gris:v('brand-soft'), warn:v('warn'), ok:v('ok'), deep:v('deep') };
  var fuente = v('fuente') || 'Inter, sans-serif';
  Chart.defaults.font.family = fuente;
  Chart.defaults.font.size = 15;
  Chart.defaults.color = C.muted;
  Chart.defaults.maintainAspectRatio = false;
  Chart.defaults.plugins.legend.position = 'bottom';
  Chart.defaults.plugins.legend.labels.boxWidth = 12;
  Chart.defaults.plugins.legend.labels.padding = 16;
  Chart.defaults.plugins.tooltip.titleFont = { size: 15, weight: '700' };
  Chart.defaults.plugins.tooltip.bodyFont = { size: 15 };
  Chart.defaults.plugins.tooltip.padding = 10;
  Chart.defaults.scale.grid.color = C.line;
  Chart.defaults.elements.bar.borderRadius = 5;
  C.sinGrilla = { grid: { display: false } };
  C.etiquetas = { id:'etiquetas', afterDatasetsDraw: function(chart, _a, o){
    if(!o || !o.on) return; var ctx = chart.ctx; var h = chart.options.indexAxis === 'y';
    chart.data.datasets.forEach(function(ds,i){ if(ds.type==='line') return;
      chart.getDatasetMeta(i).data.forEach(function(el,j){ var v = ds.data[j]; ctx.save();
        ctx.fillStyle = C.ink; ctx.font = '700 15px ' + fuente;
        if(h){ ctx.textBaseline='middle'; ctx.fillText((o.fmt||String)(v), el.x+8, el.y); }
        else { ctx.textAlign='center'; ctx.fillText((o.fmt||String)(v), el.x, el.y-8); }
        ctx.restore(); }); }); } };
  Chart.register(C.etiquetas);
})();
