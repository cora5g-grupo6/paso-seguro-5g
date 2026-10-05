// Paso Seguro 5G · página del guía (teléfono Nokia XR20 u otro).
// Recibe la alerta por SSE, la confirma sola (para medir la entrega) y avisa con sirena, voz y vibración.
"use strict";

(() => {
  const { $, texto, h, num, hora } = PS;
  const params = new URLSearchParams(location.search);
  const cliente = (params.get("id") || "guia-xr20").replace(/[^A-Za-z0-9_.-]/g, "").slice(0, 32) || "guia";
  let activado = false;
  let audio = null;
  let sirena = null;
  let bloqueo = null;
  let videoActivo = false;
  let estadoPrevio = null;

  PS.iniciarPing(cliente);
  setInterval(() => texto("#reloj", hora(PS.ahoraServidor())), 500);
  setInterval(() => {
    const ult = PS.reloj.rtts.slice(-60);
    const p50 = PS.percentil(ult.slice(-30), 50);
    $("#lat-ping").replaceChildren(p50 === null ? "—" : num(p50, p50 < 10 ? 1 : 0), h("small", {}, " ms"));
    PS.chispa($("#chispa"), ult);
  }, 1000);

  // --- sonido, voz, vibración y pantalla encendida -----------------------------------------
  async function activar() {
    activado = true;
    try { audio = new (window.AudioContext || window.webkitAudioContext)(); } catch (e) { audio = null; }
    try { if ("wakeLock" in navigator) bloqueo = await navigator.wakeLock.request("screen"); } catch (e) { bloqueo = null; }
    $("#activar").classList.add("oculto");
    tono(880, 0.15);
    hablar("Alertas activadas.");
  }
  document.addEventListener("visibilitychange", async () => {
    if (activado && document.visibilityState === "visible" && "wakeLock" in navigator) {
      try { bloqueo = await navigator.wakeLock.request("screen"); } catch (e) { /* sin bloqueo */ }
    }
  });

  function tono(frecuencia, segundos, cuando = 0) {
    if (!audio) return;
    const o = audio.createOscillator();
    const g = audio.createGain();
    o.frequency.value = frecuencia;
    g.gain.value = 0.25;
    o.connect(g).connect(audio.destination);
    o.start(audio.currentTime + cuando);
    o.stop(audio.currentTime + cuando + segundos);
  }

  function iniciarSirena(segundos = 20) {
    pararSirena();
    let n = 0;
    sirena = setInterval(() => {
      tono(n % 2 ? 660 : 960, 0.35);
      if (++n > segundos * 2.5) pararSirena();
    }, 400);
    if (navigator.vibrate) navigator.vibrate([400, 150, 400, 150, 400, 150, 800]);
  }

  function pararSirena() {
    if (sirena) clearInterval(sirena);
    sirena = null;
    if (window.speechSynthesis) speechSynthesis.cancel();
    if (navigator.vibrate) navigator.vibrate(0);
  }

  function hablar(frase) {
    if (!activado || !window.speechSynthesis) return;
    const u = new SpeechSynthesisUtterance(frase);
    u.lang = "es-CR";
    u.rate = 1.0;
    speechSynthesis.speak(u);
  }

  // --- estado ---------------------------------------------------------------------------------
  function pintarEstado(s) {
    const b = $("#banner");
    b.style.setProperty("--color-estado", PS.colorEstado(s.estado));
    b.classList.remove("LIBRE", "CUIDADO", "CERRADO");
    b.classList.add(s.estado);
    texto("#estado", s.estado);
    texto("#nivel", s.nivel === null ? "Nivel: sin dato" : `Nivel ${num(s.nivel)} %`);
    texto("#razon", (s.razones || []).join(" · "));
    if (s.camara.activa && s.camara.conectada && !videoActivo) revisarVideo();
    estadoPrevio = s.estado;
  }

  // --- alertas ----------------------------------------------------------------------------------
  async function alAlerta(ev) {
    const recibido = PS.ahoraServidor();
    const tarjeta = $("#alerta");
    tarjeta.classList.remove("oculto");
    tarjeta.style.setProperty("--color-estado", PS.colorEstado(ev.estado));
    texto("#alerta-hora", hora(ev.t_evento_ms));
    texto("#alerta-texto", ev.mensajes.guia || ev.mensajes.es);
    texto("#alerta-lat", "");
    // primero avisar (sirena, voz, vibración); la confirmación al borde va después y sin esperar
    if (ev.estado === "CERRADO" || ev.tipo === "persona_en_cruce") iniciarSirena();
    else if (ev.estado === "CUIDADO") { tono(880, 0.2); tono(880, 0.2, 0.35); if (navigator.vibrate) navigator.vibrate([300, 120, 300]); }
    else tono(660, 0.3);
    hablar(ev.mensajes.guia || ev.mensajes.es);
    mostrarImagen(ev);
    PS.enviar(`/api/alertas/${encodeURIComponent(ev.id)}/ack`, { cliente, t_recibido_ms: recibido })
      .then((r) => texto("#alerta-lat", `Llegó ${num(r.entrega_ms)} ms después de la decisión en el borde.`))
      .catch(() => { /* sin ack: la alerta ya sonó */ });
  }

  async function mostrarImagen(ev) {
    const img = $("#alerta-img");
    if (!ev.media) { img.classList.add("oculto"); return; }
    await new Promise((r) => setTimeout(r, 800)); // el borde guarda la captura en paralelo
    let clip = [];
    try { clip = ((await PS.pedir(`/api/eventos/${encodeURIComponent(ev.id)}`)).media || {}).clip || []; } catch (e) { /* solo captura */ }
    const cuadros = clip.length ? clip : [ev.media.captura];
    img.classList.remove("oculto");
    let i = 0;
    const pasar = () => { img.src = cuadros[i % cuadros.length]; i++; if (i < cuadros.length * 3) setTimeout(pasar, 500); };
    pasar();
  }

  // --- video ----------------------------------------------------------------------------------
  const video = $("#video");
  async function revisarVideo() {
    try {
      const r = await fetch("/api/camara/captura.jpg", { cache: "no-store" });
      if (r.ok) {
        if (!videoActivo) {
          videoActivo = true;
          video.src = `/video.mjpg?t=${Date.now()}`;
          video.classList.remove("oculto");
          $("#sin-video").classList.add("oculto");
        }
        return;
      }
    } catch (e) { /* sin red */ }
    videoActivo = false;
    video.removeAttribute("src");
    video.classList.add("oculto");
    $("#sin-video").classList.remove("oculto");
  }
  video.addEventListener("error", () => { videoActivo = false; setTimeout(revisarVideo, 3000); });
  setInterval(revisarVideo, 15000);

  // --- botones -------------------------------------------------------------------------------
  $("#btn-activar").addEventListener("click", activar);
  $("#btn-entendido").addEventListener("click", () => { pararSirena(); $("#alerta").classList.add("oculto"); });
  $("#btn-cerrar").addEventListener("click", () =>
    PS.enviar("/api/manual", { estado: "CERRADO", motivo: `Cierre del guía (${cliente})`, minutos: 120 }).catch((e) => alert(e.message)));
  $("#btn-quitar").addEventListener("click", () => PS.enviar("/api/manual", { estado: null }).catch((e) => alert(e.message)));

  PS.pedir("/api/cruce").then((c) => texto("#nombre-cruce", c.nombre)).catch(() => {});
  PS.escuchar({ estado: pintarEstado, alerta: alAlerta }, (ok) => {
    $("#pt-conexion").className = `punto ${ok ? "ok" : "mal"}`;
    texto("#txt-conexion", ok ? "Conectado" : "Sin conexión");
    if (!ok && activado && estadoPrevio !== null) tono(330, 0.4);
  });
  revisarVideo();
})();
