// Banco de prueba en PC: WebServer que no abre puertos; guarda las rutas para llamarlas desde main().
#pragma once
#include <map>

#include "Arduino.h"

class WebServer {
 public:
  std::map<std::string, std::function<void()>> rutas;
  String ultimaRespuesta;
  int ultimoCodigo = 0;
  explicit WebServer(int) {}
  void on(const char* ruta, std::function<void()> fn) { rutas[ruta] = fn; }
  void begin() {}
  void handleClient() {}
  void sendHeader(const char*, const char*) {}
  void send(int codigo, const char*, const String& contenido) {
    ultimoCodigo = codigo;
    ultimaRespuesta = contenido;
  }
};
