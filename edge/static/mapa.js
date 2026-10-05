// Paso Seguro 5G · mapa propio del cruce en SVG (sin teselas: funciona sin internet).
// Proyección equirectangular local; las coordenadas del cruce vienen de /api/cruce como [lat, lon].
"use strict";

PS.mapa = function (svg, cruce) {
  const NS = "http://www.w3.org/2000/svg";
  const W = 640, H = 420, M = 38;
  svg.setAttribute("viewBox", `0 0 ${W} ${H}`);
  svg.innerHTML = "";

  const tramo = cruce.polilinea || []; // vacío en un cruce peatonal
  const todos = [...tramo, ...(cruce.rio_linea || []), cruce.punto, ...(cruce.equipos || []).map((e) => e.punto)];
  const lat0 = todos.reduce((s, p) => s + p[0], 0) / todos.length;
  const kx = Math.cos((lat0 * Math.PI) / 180);
  const xs = todos.map((p) => p[1] * kx), ys = todos.map((p) => p[0]);
  const minX = Math.min(...xs), maxX = Math.max(...xs), minY = Math.min(...ys), maxY = Math.max(...ys);
  const escala = Math.min((W - 2 * M) / (maxX - minX || 1e-6), (H - 2 * M) / (maxY - minY || 1e-6));
  const cx = (minX + maxX) / 2, cy = (minY + maxY) / 2;
  const P = ([lat, lon]) => [W / 2 + (lon * kx - cx) * escala, H / 2 - (lat - cy) * escala];
  const metrosPorPx = 111320 / escala;

  function el(tag, attrs, padre = svg) {
    const n = document.createElementNS(NS, tag);
    for (const [k, v] of Object.entries(attrs)) n.setAttribute(k, v);
    padre.appendChild(n);
    return n;
  }
  const camino = (pts) => pts.map((p, i) => `${i ? "L" : "M"}${P(p)[0].toFixed(1)},${P(p)[1].toFixed(1)}`).join(" ");

  // Fondo y trama suave
  el("rect", { x: 0, y: 0, width: W, height: H, fill: "#12241a" });
  const defs = el("defs", {});
  const pat = el("pattern", { id: "trama", width: 14, height: 14, patternUnits: "userSpaceOnUse" }, defs);
  el("circle", { cx: 2, cy: 2, r: 1, fill: "#1b3325" }, pat);
  el("rect", { x: 0, y: 0, width: W, height: H, fill: "url(#trama)" });

  // Río
  if ((cruce.rio_linea || []).length > 1) {
    el("path", { d: camino(cruce.rio_linea), stroke: "#0d4f8b", "stroke-width": 22, fill: "none", "stroke-linecap": "round", "stroke-linejoin": "round", opacity: 0.55 });
    el("path", { d: camino(cruce.rio_linea), stroke: "#2b8ce6", "stroke-width": 9, fill: "none", "stroke-linecap": "round", "stroke-linejoin": "round" });
    const [rx, ry] = P(cruce.rio_linea[0]);
    el("text", { x: rx + 8, y: ry - 10, fill: "#8cc8ff", "font-size": 14, "font-style": "italic" }).textContent = cruce.rio;
  }

  // Vía (borde gris + color del estado) y sentido de la polilínea (inicio -> fin), como la lee Waze
  let via = null;
  if (tramo.length > 1) {
    el("path", { d: camino(tramo), stroke: "#d7dde3", "stroke-width": 16, fill: "none", "stroke-linecap": "round", "stroke-linejoin": "round" });
    via = el("path", { d: camino(tramo), stroke: "#7d8b97", "stroke-width": 9, fill: "none", "stroke-linecap": "round", "stroke-linejoin": "round" });
    const [vx, vy] = P(tramo[0]);
    const [fx, fy] = P(tramo[tramo.length - 1]);
    el("text", { x: vx + 10, y: vy + 4, fill: "#eef2f5", "font-size": 14, "font-weight": 700 }).textContent = cruce.calle;
    el("circle", { cx: vx, cy: vy, r: 4, fill: "#eef2f5" });
    el("circle", { cx: fx, cy: fy, r: 4, fill: "#eef2f5" });
  }

  // Equipos
  for (const e of cruce.equipos || []) {
    const [ex, ey] = P(e.punto);
    const g = el("g", {});
    if (e.tipo === "camara") {
      el("rect", { x: ex - 9, y: ey - 7, width: 18, height: 14, rx: 3, fill: "#202a33", stroke: "#e9eef3", "stroke-width": 1.5 }, g);
      el("circle", { cx: ex, cy: ey, r: 4, fill: "none", stroke: "#e9eef3", "stroke-width": 1.5 }, g);
    } else {
      el("rect", { x: ex - 7, y: ey - 7, width: 14, height: 14, rx: 7, fill: "#202a33", stroke: "#e9eef3", "stroke-width": 1.5 }, g);
      el("path", { d: `M${ex - 4},${ey + 2} q4,-6 8,0`, stroke: "#8cc8ff", fill: "none", "stroke-width": 1.6 }, g);
    }
    el("text", { x: ex + 13, y: ey + 4, fill: "#c9d3dc", "font-size": 12 }, g).textContent = e.nombre;
  }

  // Punto del cruce
  const [px, py] = P(cruce.punto);
  const pulso = el("circle", { cx: px, cy: py, r: 10, fill: "none", stroke: "#d93025", "stroke-width": 3, class: "pulso", opacity: 0 });
  const punto = el("circle", { cx: px, cy: py, r: 11, fill: "#7d8b97", stroke: "#fff", "stroke-width": 3 });

  // Norte y escala
  el("path", { d: `M${W - 28},48 l8,-22 l8,22 l-8,-6 z`, fill: "#e9eef3" });
  el("text", { x: W - 20, y: 64, fill: "#e9eef3", "font-size": 12, "text-anchor": "middle" }).textContent = "N";
  const opciones = [10, 20, 25, 50, 100, 200, 250, 500, 1000, 2000];
  const metros = opciones.find((m) => m / metrosPorPx >= 70) || 2000;
  const largo = metros / metrosPorPx;
  el("path", { d: `M16,${H - 20} h${largo} M16,${H - 25} v10 M${16 + largo},${H - 25} v10`, stroke: "#e9eef3", "stroke-width": 2, fill: "none" });
  el("text", { x: 16 + largo / 2, y: H - 28, fill: "#e9eef3", "font-size": 12, "text-anchor": "middle" }).textContent = metros >= 1000 ? `${metros / 1000} km` : `${metros} m`;
  if (cruce.atribucion) {
    el("text", { x: W - 8, y: H - 8, fill: "#7f91a1", "font-size": 10, "text-anchor": "end" }).textContent = cruce.atribucion;
  }
  if (!cruce.coordenadas_confirmadas) {
    el("text", { x: 12, y: 22, fill: "#f9ab00", "font-size": 12 }).textContent = "Punto de ejemplo: coordenadas por confirmar";
  }

  return {
    pintar(estado) {
      const color = PS.colorEstado(estado);
      if (via) via.setAttribute("stroke", estado === "LIBRE" ? "#7d8b97" : color);
      punto.setAttribute("fill", color);
      pulso.setAttribute("stroke", color);
      pulso.setAttribute("opacity", estado === "CERRADO" ? 1 : 0);
    },
  };
};
