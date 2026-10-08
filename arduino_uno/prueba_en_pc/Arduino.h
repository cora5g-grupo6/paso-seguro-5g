// Banco de prueba en PC para PasoSeguroUNO.ino: lo mínimo de Arduino.h que usa el sketch.
// Sirve para compilarlo en la PC y probar su lógica y su HTTP contra el borde. No reemplaza a la placa.
#pragma once
#include <chrono>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <thread>

typedef uint8_t byte;
#define HIGH 1
#define LOW 0
#define INPUT 0
#define OUTPUT 1
#define INPUT_PULLUP 2
#define A0 14
#define constrain(amt, low, high) ((amt) < (low) ? (low) : ((amt) > (high) ? (high) : (amt)))

// Reloj: simulado en las pruebas de lógica (delay lo adelanta) y real en la conversación con el borde.
extern unsigned long pruebaMicros;
extern bool pruebaTiempoReal;
inline unsigned long micros() {
  if (!pruebaTiempoReal) return pruebaMicros;
  static auto inicio = std::chrono::steady_clock::now();
  return (unsigned long)std::chrono::duration_cast<std::chrono::microseconds>(
             std::chrono::steady_clock::now() - inicio).count();
}
inline unsigned long millis() { return micros() / 1000UL; }
inline void delayMicroseconds(unsigned int us) {
  if (pruebaTiempoReal) std::this_thread::sleep_for(std::chrono::microseconds(us));
  else pruebaMicros += us;
}
inline void delay(unsigned long ms) { delayMicroseconds((unsigned int)(ms * 1000UL)); }

// Pines simulados
extern int pruebaPines[32];
extern int pruebaAnalogico[8];
extern long pruebaEchoUs;  // duración del eco que devuelve pulseIn (0 = sin eco)
inline void pinMode(int, int) {}
inline void digitalWrite(int pin, int v) { pruebaPines[pin] = v; }
inline int digitalRead(int pin) { return pruebaPines[pin]; }
inline int analogRead(int pin) { return pruebaAnalogico[pin - A0]; }
inline unsigned long pulseIn(int, int, unsigned long espera) {
  return pruebaEchoUs > 0 && (unsigned long)pruebaEchoUs <= espera ? (unsigned long)pruebaEchoUs : 0;
}

// F(): en la PC es texto normal
class __FlashStringHelper;
#define F(t) (reinterpret_cast<const __FlashStringHelper*>(t))

inline char* dtostrf(double v, signed char ancho, unsigned char dec, char* buf) {
  snprintf(buf, 10, "%*.*f", ancho, dec, v);  // 10: el tamaño del búfer que usa el sketch
  return buf;
}

struct SerialFalso {
  bool silencio = false;
  void begin(long) {}
  void print(const char* t) { if (!silencio) fputs(t, stdout); }
  void print(const __FlashStringHelper* t) { print(reinterpret_cast<const char*>(t)); }
  void print(long v) { char b[24]; snprintf(b, sizeof b, "%ld", v); print(b); }
  void print(int v) { print((long)v); }
  void print(unsigned long v) { char b[24]; snprintf(b, sizeof b, "%lu", v); print(b); }
  void print(double v, int dec = 2) { char b[32]; snprintf(b, sizeof b, "%.*f", dec, v); print(b); }
  void println() { print("\n"); }
  void println(const char* t) { print(t); println(); }
  void println(const __FlashStringHelper* t) { print(t); println(); }
};
extern SerialFalso Serial;
