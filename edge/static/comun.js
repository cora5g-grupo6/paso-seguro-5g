// Paso Seguro 5G · utilidades comunes de las páginas (sin librerías externas).
"use strict";

const PS = (() => {
  const COLORES = { LIBRE: "#1e8e3e", CUIDADO: "#f9ab00", CERRADO: "#d93025" };
  const ZONA = "America/Costa_Rica";

  const $ = (sel, raiz = document) => raiz.querySelector(sel);

  function texto(sel, valor) {
    const el = typeof sel === "string" ? $(sel) : sel;
    if (el) el.textContent = valor;
  }

  // Crea elementos sin innerHTML (el texto siempre entra escapado).
  function h(tag, attrs = {}, ...hijos) {
    const el = document.createElement(tag);
    for (const [k, v] of Object.entries(attrs)) {
      if (v === null || v === undefined || v === false) continue;
      if (k === "class") el.className = v;
      else if (k === "style") el.style.cssText = v;
      else el.setAttribute(k, v);
    }
    for (const c of hijos.flat()) if (c !== null && c !== undefined) el.append(c instanceof Node ? c : String(c));
    return el;
  }

  function num(x, dec = 0) {
    if (x === null || x === undefined || Number.isNaN(x)) return "—";
    return Number(x).toLocaleString("es-CR", { minimumFractionDigits: dec, maximumFractionDigits: dec });
  }

  function hora(ms, conSegundos = true) {
    if (!ms) return "—";
    return new Date(ms).toLocaleTimeString("es-CR", {
      timeZone: ZONA, hour: "2-digit", minute: "2-digit", second: conSegundos ? "2-digit" : undefined,
    });
  }

  async function pedir(url, opciones = {}) {
    const r = await fetch(url, { cache: "no-store", ...opciones });
    if (!r.ok) throw new Error(`${url}: ${r.status}`);
    const tipo = r.headers.get("content-type") || "";
    return tipo.includes("json") ? r.json() : r.text();
  }

  function enviar(url, cuerpo) {
    return pedir(url, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(cuerpo ?? {}) });
  }

  // --- Reloj del servidor y latencia: /ping cada segundo -------------------------------
  // offset = hora del servidor - hora local, tomado de la muestra con menor ida y vuelta.
  const reloj = { offset: 0, rtts: [], muestras: [], pendientes: [], cliente: "tablero" };

  async function unPing() {
    const t0 = performance.now();
    const a = Date.now();
    try {
      const r = await pedir("/ping");
      const rtt = performance.now() - t0;
      const b = Date.now();
      reloj.rtts.push(rtt);
      if (reloj.rtts.length > 120) reloj.rtts.shift();
      reloj.pendientes.push(Math.round(rtt * 10) / 10);
      reloj.muestras.push({ rtt, offset: r.t_srv - (a + b) / 2 });
      if (reloj.muestras.length > 30) reloj.muestras.shift();
      const mejor = reloj.muestras.reduce((m, x) => (x.rtt < m.rtt ? x : m));
      reloj.offset = mejor.offset;
      return rtt;
    } catch (e) {
      return null;
    }
  }

  function iniciarPing(cliente, cadaMs = 1000) {
    reloj.cliente = cliente;
    unPing();
    setInterval(unPing, cadaMs);
    setInterval(() => {
      if (!reloj.pendientes.length) return;
      const rtt_ms = reloj.pendientes.splice(0);
      enviar("/api/latencia/cliente", { cliente: reloj.cliente, rtt_ms }).catch(() => {});
    }, 5000);
  }

  const ahoraServidor = () => Date.now() + reloj.offset;

  function percentil(valores, p) {
    if (!valores.length) return null;
    const a = [...valores].sort((x, y) => x - y);
    const k = (a.length - 1) * p / 100;
    const f = Math.floor(k);
    const c = Math.min(f + 1, a.length - 1);
    return a[f] + (a[c] - a[f]) * (k - f);
  }

  // --- Gráfico chispa (canvas) -------------------------------------------------------------
  function chispa(canvas, valores, color = "#8ab4f8") {
    if (!canvas) return;
    const dpr = window.devicePixelRatio || 1;
    const w = canvas.clientWidth, h = canvas.clientHeight;
    canvas.width = w * dpr; canvas.height = h * dpr;
    const g = canvas.getContext("2d");
    g.scale(dpr, dpr);
    g.clearRect(0, 0, w, h);
    if (valores.length < 2) return;
    const arriba = 16; // espacio para la etiqueta, así la línea no la tapa
    const max = Math.max(...valores) * 1.1 || 1;
    g.strokeStyle = "rgba(255,255,255,.08)";
    g.beginPath(); g.moveTo(0, h - 0.5); g.lineTo(w, h - 0.5); g.stroke();
    g.strokeStyle = color; g.lineWidth = 2; g.beginPath();
    valores.forEach((v, i) => {
      const x = (i / (valores.length - 1)) * w;
      const y = h - 3 - (v / max) * (h - arriba - 3);
      i ? g.lineTo(x, y) : g.moveTo(x, y);
    });
    g.stroke();
    g.fillStyle = "#97a6b4"; g.font = "11px system-ui, sans-serif"; g.textAlign = "right";
    g.fillText(`últimos ${valores.length} s · máx ${num(Math.max(...valores), 0)} ms`, w - 2, 11);
  }

  // --- Eventos del servidor (SSE) -------------------------------------------------------------
  function escuchar(manejadores, alCambiarConexion) {
    let fuente;
    function abrir() {
      fuente = new EventSource("/api/stream");
      fuente.onopen = () => alCambiarConexion && alCambiarConexion(true);
      fuente.onerror = () => alCambiarConexion && alCambiarConexion(false);
      for (const [tipo, fn] of Object.entries(manejadores)) {
        fuente.addEventListener(tipo, (e) => {
          try { fn(JSON.parse(e.data)); } catch (err) { console.error(tipo, err); }
        });
      }
    }
    abrir();
    return () => fuente && fuente.close();
  }

  function colorEstado(estado) {
    return COLORES[estado] || "#3a4652";
  }

  return { $, texto, h, num, hora, pedir, enviar, reloj, iniciarPing, ahoraServidor, percentil, chispa, escuchar, colorEstado, COLORES };
})();
