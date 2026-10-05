// Paso Seguro 5G · tablero principal (pantalla del pitch y del centro de control).
"use strict";

(() => {
  const { $, texto, h, num, hora } = PS;
  let mapa = null;
  let ultimo = null;
  let sonido = false;
  let videoActivo = false;
  let umbralesPintados = "";

  PS.iniciarPing("tablero");
  setInterval(() => texto("#reloj", hora(PS.ahoraServidor())), 500);

  // --- cruce y mapa ------------------------------------------------------------------
  async function cargarCruce() {
    try {
      const c = await PS.pedir("/api/cruce");
      texto("#nombre-cruce", `${c.nombre} · ${c.rio} · ${c.lugar}`);
      mapa = PS.mapa($("#mapa"), c);
      texto("#mapa-pie", c.publica_en_waze
        ? `Vía vehicular: va al feed de Waze como «${c.calle}».`
        : "Vía peatonal: Waze no admite cierres aquí; el aviso va al guía y al turista.");
      if (ultimo) mapa.pintar(ultimo.estado);
    } catch (e) {
      setTimeout(cargarCruce, 3000);
    }
  }

  // --- estado ----------------------------------------------------------------------------
  function pintarUmbrales(u) {
    const clave = `${u.cuidado}-${u.cerrado}`;
    if (clave === umbralesPintados) return;
    umbralesPintados = clave;
    const medidor = $("#medidor");
    medidor.querySelectorAll(".umbral").forEach((n) => n.remove());
    for (const [pct, color] of [[u.cuidado, PS.COLORES.CUIDADO], [u.cerrado, PS.COLORES.CERRADO]]) {
      medidor.append(h("div", { class: "umbral", style: `bottom:${pct}%;border-color:${color}` },
        h("span", { style: `color:${color}` }, `${pct}%`)));
    }
  }

  function estadoPunto(edad, limite = 10) {
    if (edad === null || edad === undefined) return "mal";
    return edad > limite ? "aviso" : "ok";
  }

  function tarjeta(titulo, valor, nota, punto) {
    return h("div", { class: "fuente" },
      h("div", { class: "entre" }, h("span", { class: "t" }, titulo), h("span", { class: `punto ${punto}` })),
      h("div", { class: "v" }, valor),
      h("div", { class: "n" }, nota));
  }

  function pintarFuentes(s) {
    const e = s.entradas;
    const cam = e.camara;
    const camNota = !s.camara.activa ? "Cámara apagada"
      : cam.edad_s === null ? "Sin cuadros todavía"
      : cam.confianza < 0.5 ? (cam.motivo || "No ve bien la regla")
      : `confianza ${num(cam.confianza * 100)} % · hace ${num(cam.edad_s, 1)} s`;
    const sen = e.sensor;
    const disp = (s.sensores || []).map((x) => `${x.id} (${x.origen}${x.rssi ? `, ${x.rssi} dBm` : ""})`).join(", ");
    const lluvia = e.lluvia || {};
    const lluviaValor = lluvia.fuente ? `${num(lluvia.mm_1h, 1)} mm/h` : "—";
    const lluviaNota = !lluvia.fuente ? (s.imn.activo ? "Esperando al IMN" : "IMN apagado")
      : lluvia.fuente === "simulación" ? "Simulada para el ensayo"
      : `${lluvia.estacion}${lluvia.distancia_km ? ` · a ${num(lluvia.distancia_km)} km` : ""} · hace ${num(lluvia.edad_min)} min`;
    const per = s.personas || {};
    const man = e.manual;
    $("#fuentes").replaceChildren(
      tarjeta("Cámara (IA en el borde)", cam.nivel === null || cam.confianza < 0.5 ? "—" : `${num(cam.nivel)} %`, camNota,
        s.camara.activa ? (cam.confianza < 0.5 ? "mal" : estadoPunto(cam.edad_s)) : "mal"),
      tarjeta("Sensor de agua ESP32", sen.nivel === null ? "—" : `${num(sen.nivel)} %`,
        sen.edad_s === null ? "Sin datos del ESP32" : `hace ${num(sen.edad_s, 1)} s · ${disp}`, estadoPunto(sen.edad_s)),
      tarjeta("Flotador (respaldo)", e.flotador.activo === null ? "—" : e.flotador.activo ? "ACTIVADO" : "normal",
        e.flotador.edad_s === null ? "Sin datos" : `hace ${num(e.flotador.edad_s, 1)} s`,
        e.flotador.activo ? "mal" : estadoPunto(e.flotador.edad_s)),
      tarjeta("Lluvia", lluviaValor, lluviaNota, lluvia.fuente ? "ok" : "aviso"),
      tarjeta("Personas en la zona", per.metodo === "apagado" ? "apagado" : String(per.en_zona ?? 0),
        s.alarma_persona ? "¡Alarma de persona activa!" : `detección: ${per.metodo || "—"}${per.ms ? ` · ${num(per.ms)} ms` : ""}`,
        s.alarma_persona ? "mal" : "ok"),
      tarjeta("Cierre manual", man ? man.estado : "—", man ? `${man.motivo || "sin motivo"} · hasta ${man.hasta_iso.slice(11, 16)}` : "Nadie lo forzó",
        man ? "aviso" : "ok"),
    );
    const c = s.camara;
    texto("#cam-estado", c.activa
      ? `Fuente: ${c.fuente || "—"} · ${num(c.fps, 1)} cuadros/s · ${c.conectada ? "conectada" : "sin señal"}${c.ultimo_error ? ` · ${c.ultimo_error}` : ""}`
      : "Cámara apagada (CAMARA_ACTIVA=false)");
  }

  function pintarEstado(s) {
    const cambio = !ultimo || ultimo.estado !== s.estado;
    ultimo = s;
    const color = PS.colorEstado(s.estado);
    const b = $("#banner");
    b.style.setProperty("--color-estado", color);
    b.classList.remove("LIBRE", "CUIDADO", "CERRADO");
    b.classList.add(s.estado);
    b.classList.toggle("degradado", !!s.degradado);
    texto("#estado", s.estado);
    texto("#nivel", s.nivel === null ? "Nivel: sin dato" : `Nivel ${num(s.nivel)} %`);
    texto("#fuente", { camara: "por cámara", sensor: "por sensor ESP32", ninguna: "sin fuente" }[s.fuente] || "");
    texto("#desde", `desde ${hora(s.desde_ms, false)}`);
    texto("#razon", (s.razones || []).join(" · "));
    texto("#bajada", s.bajada_en_s !== null ? `Pasa a un nivel más bajo en ${s.bajada_en_s} s si sigue así` : "");
    document.documentElement.style.setProperty("--color-estado", color);
    const n = s.nivel ?? 0;
    $("#agua").style.height = `${Math.max(0, Math.min(100, n))}%`;
    texto("#medidor-valor", s.nivel === null ? "—" : `${num(n)}%`);
    pintarUmbrales(s.umbrales);
    if (mapa && cambio) mapa.pintar(s.estado);
    texto("#msg-es", s.mensajes.es);
    texto("#msg-en", s.mensajes.en);
    pintarFuentes(s);
    const nube = s.nube || {};
    $("#pt-internet").className = `punto ${nube.ok === true ? "ok" : nube.ok === false ? "mal" : ""}`;
    texto("#txt-internet", !nube.activa ? "Internet: no se mide" : nube.ok === true ? `Internet: sí (${num(nube.ms)} ms)` : nube.ok === false ? "Internet: NO" : "Internet: —");
    $("#panel-demo").classList.toggle("oculto", !s.modo_demo);
    if (s.camara.activa && s.camara.conectada && !videoActivo) revisarVideo();
  }

  // --- latencia ----------------------------------------------------------------------------
  const FILAS = [
    ["guia", "Teléfono del guía ↔ borde"],
    ["captura_a_decision_ms", "Cámara → decisión"],
    ["vision_ms", "Análisis del cuadro (CPU)"],
    ["esp32_rtt_ms", "ESP32 ↔ borde (Wi-Fi + 5G)"],
    ["alerta_entrega_ms", "Alerta → teléfono del guía"],
    ["nube_rtt_ms", "Borde → internet (nube)"],
  ];

  function pintarLatencia(lat) {
    const filas = FILAS.map(([clave, nombre]) => {
      let r = lat[clave];
      let etiqueta = nombre;
      if (clave === "guia") {
        const k = Object.keys(lat).find((x) => x.startsWith("cliente_rtt_ms:guia"));
        r = k ? lat[k] : null;
        if (k) etiqueta = `${nombre} (${k.split(":")[1]})`;
      }
      const v = (x) => (r && r.n ? `${num(x, x < 10 ? 1 : 0)}` : "—");
      return h("tr", {}, h("td", {}, etiqueta), h("td", { class: "num" }, r ? v(r.p50) : "—"), h("td", { class: "num" }, r ? v(r.p95) : "—"));
    });
    $("#tabla-lat").replaceChildren(...filas);
  }

  setInterval(() => {
    const ult = PS.reloj.rtts.slice(-60);
    const p50 = PS.percentil(ult.slice(-30), 50);
    $("#lat-ping").replaceChildren(p50 === null ? "—" : num(p50, p50 < 10 ? 1 : 0), h("small", {}, " ms"));
    PS.chispa($("#chispa"), ult);
  }, 1000);

  // --- eventos --------------------------------------------------------------------------------
  const TITULOS = { cambio_estado: "Cambio de estado", persona_en_cruce: "Persona en el cruce" };

  function agregarEvento(ev) {
    const lista = $("#eventos");
    if (lista.firstElementChild && lista.firstElementChild.classList.contains("suave")) lista.replaceChildren();
    const envios = h("div", { class: "envio", id: `envios-${ev.id}` });
    const li = h("li", { id: `ev-${ev.id}` },
      h("div", { class: "cab" },
        h("span", { class: `marca-estado ${ev.estado}`, style: `background:${PS.colorEstado(ev.estado)}` }, ev.estado),
        h("b", {}, TITULOS[ev.tipo] || ev.tipo),
        h("span", { class: "suave mono" }, hora(ev.t_evento_ms))),
      h("div", { class: "suave" }, (ev.razones || []).join(" · ")),
      envios);
    lista.prepend(li);
    while (lista.children.length > 40) lista.lastElementChild.remove();
    if (ev.envios && ev.envios.length) pintarEnvios(ev.id, ev.envios);
  }

  function pintarEnvios(id, envios) {
    const el = $(`#envios-${id}`);
    if (!el) return;
    el.dataset.envios = envios.map((x) => `${x.canal}: ${x.ok ? "✓" : "✗"} ${num(x.ms)} ms${x.ok ? "" : ` (${x.detalle})`}`).join(" · ");
    el.textContent = [el.dataset.envios, el.dataset.acks].filter(Boolean).join(" · ");
  }

  function pintarAck(a) {
    const el = $(`#envios-${a.id}`);
    if (!el) return;
    el.dataset.acks = `${a.cliente} la recibió en ${num(a.entrega_ms)} ms`;
    el.textContent = [el.dataset.envios, el.dataset.acks].filter(Boolean).join(" · ");
  }

  function pitar(estado) {
    if (!sonido) return;
    try {
      const ctx = new (window.AudioContext || window.webkitAudioContext)();
      const veces = estado === "CERRADO" ? 6 : estado === "CUIDADO" ? 2 : 1;
      for (let i = 0; i < veces; i++) {
        const o = ctx.createOscillator();
        const g = ctx.createGain();
        o.frequency.value = i % 2 ? 660 : 880;
        g.gain.value = 0.15;
        o.connect(g).connect(ctx.destination);
        o.start(ctx.currentTime + i * 0.3);
        o.stop(ctx.currentTime + i * 0.3 + 0.22);
      }
    } catch (e) { /* sin audio */ }
  }

  function alAlerta(ev) {
    agregarEvento(ev);
    const b = $("#banner");
    b.classList.remove("alerta");
    void b.offsetWidth;
    b.classList.add("alerta");
    pitar(ev.estado);
  }

  // --- video ------------------------------------------------------------------------------------
  const img = $("#video");
  async function revisarVideo() {
    try {
      const r = await fetch("/api/camara/captura.jpg", { cache: "no-store" });
      if (r.ok) {
        if (!videoActivo) {
          videoActivo = true;
          img.src = `/video.mjpg?t=${Date.now()}`;
          img.classList.remove("oculto");
          $("#sin-video").classList.add("oculto");
        }
        return;
      }
    } catch (e) { /* sin red */ }
    videoActivo = false;
    img.removeAttribute("src");
    img.classList.add("oculto");
    $("#sin-video").classList.remove("oculto");
  }
  img.addEventListener("error", () => { videoActivo = false; setTimeout(revisarVideo, 3000); });
  setInterval(revisarVideo, 15000);

  // --- feeds e IMN --------------------------------------------------------------------------------
  async function revisarFeeds() {
    try {
      const v = await PS.pedir("/feeds/validacion");
      const j = v.waze_json;
      texto("#val-json", j.ok ? `✓ cumple la spec CIFS${j.avisos.length ? ` (${j.avisos.length} avisos)` : ""}` : `✗ ${j.errores[0]}`);
      const x = v.waze_xml_xsd;
      texto("#val-xml", x.ok === true ? "✓ válido contra el XSD oficial" : x.ok === false ? `✗ ${x.errores[0]}` : "sin validar");
      const n = ultimo && ultimo.waze ? ultimo.waze.incidentes : 0;
      texto("#feeds-nota", `${n} incidente(s) en el feed ahora. Waze consulta la URL cada pocos minutos. Publicarlo exige un socio oficial de Waze for Cities (por ejemplo, el MOPT); Google Maps toma los cierres del mismo feed.`);
    } catch (e) { /* reintenta */ }
  }

  async function revisarIMN() {
    try {
      const d = await PS.pedir("/api/imn");
      const est = d.estado || {};
      const c = d.cruce;
      if (!est.activo) texto("#imn-resumen", "IMN apagado en la configuración.");
      else if (c) {
        const base = `Estación más cercana: ${c.estacion} (a ${num(c.distancia_km)} km). Última hora: ${num(c.mm_1h, 1)} mm · 3 h: ${num(c.mm_3h, 1)} mm · 24 h: ${num(c.mm_24h, 1)} mm.`;
        texto("#imn-resumen", est.ok === false ? `${base} Sin conexión con el IMN ahora: se usa el último dato guardado.` : base);
      } else texto("#imn-resumen", est.error ? `Sin datos del IMN: ${est.error}` : "Consultando al IMN…");
      const filas = [...(d.estaciones || [])].sort((a, b) => b.max_1h - a.max_1h).map((r) =>
        h("tr", {}, h("td", {}, r.estacion), h("td", { class: "num" }, `${num(r.mm_1h, 1)} mm`),
          h("td", { class: "num" }, `${num(r.max_1h, 1)} mm`), h("td", { class: "suave" }, r.t_max_iso ? r.t_max_iso.slice(5, 16).replace("T", " ") : "—")));
      $("#tabla-imn").replaceChildren(...filas);
    } catch (e) { /* reintenta */ }
  }

  // --- modo demo ----------------------------------------------------------------------------------
  let espera = null;
  $("#deslizador").addEventListener("input", (e) => {
    const v = Number(e.target.value);
    texto("#deslizador-valor", `${v} %`);
    clearTimeout(espera);
    espera = setTimeout(() => PS.enviar("/api/demo/nivel", { nivel_pct: v }).catch(() => {}), 120);
  });

  const ACCIONES = {
    async subida() {
      for (const v of [10, 25, 45, 65, 85]) {
        $("#deslizador").value = v;
        texto("#deslizador-valor", `${v} %`);
        await PS.enviar("/api/demo/nivel", { nivel_pct: v });
        await new Promise((r) => setTimeout(r, 1200));
      }
    },
    lluvia: () => PS.enviar("/api/demo/lluvia", { mm_1h: 40.4, minutos: 10 }),
    persona: () => PS.enviar("/api/demo/persona"),
    cerrar: () => PS.enviar("/api/manual", { estado: "CERRADO", motivo: "Cierre desde el tablero", minutos: 60 }),
    quitar: () => PS.enviar("/api/manual", { estado: null }),
    reiniciar: () => PS.enviar("/api/demo/reiniciar"),
  };
  document.querySelectorAll("[data-demo]").forEach((btn) =>
    btn.addEventListener("click", () => ACCIONES[btn.dataset.demo]().catch((e) => alert(e.message))));

  $("#btn-sonido").addEventListener("click", () => {
    sonido = !sonido;
    texto("#btn-sonido", `Sonido: ${sonido ? "sí" : "no"}`);
    if (sonido) pitar("LIBRE");
  });

  // --- arranque ---------------------------------------------------------------------------------------
  PS.escuchar({
    estado: pintarEstado,
    latencia: pintarLatencia,
    alerta: alAlerta,
    envios: (d) => pintarEnvios(d.id, d.envios),
    ack: pintarAck,
  }, (ok) => {
    $("#pt-conexion").className = `punto ${ok ? "ok" : "mal"}`;
    texto("#txt-conexion", ok ? "Conectado al borde" : "Sin conexión con el borde");
  });
  PS.pedir("/api/eventos?n=20").then((evs) => evs.reverse().forEach(agregarEvento)).catch(() => {});
  cargarCruce();
  revisarVideo();
  revisarFeeds();
  revisarIMN();
  setInterval(revisarFeeds, 10000);
  setInterval(revisarIMN, 60000);
})();
