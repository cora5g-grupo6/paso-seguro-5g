// Banco de prueba en PC: HTTPClient mínimo (POST y respuesta), con la misma interfaz del ESP32.
#pragma once
#include "WiFi.h"

class HTTPClient {
  WiFiClient* c_ = nullptr;
  std::string host_, ruta_ = "/", cabeceras_;
  uint16_t puerto_ = 80;
  int espera_ = 5000, espera_conexion_ = 5000;
  String cuerpo_;

 public:
  void setTimeout(uint16_t ms) { espera_ = ms; }
  void setConnectTimeout(int32_t ms) { espera_conexion_ = ms; }
  bool begin(WiFiClient& cliente, const String& url) {
    c_ = &cliente;
    std::string u = url.c_str();
    if (u.rfind("http://", 0) != 0) return false;
    u = u.substr(7);
    auto barra = u.find('/');
    std::string hp = u.substr(0, barra);
    ruta_ = barra == std::string::npos ? "/" : u.substr(barra);
    auto dos = hp.find(':');
    host_ = hp.substr(0, dos);
    puerto_ = dos == std::string::npos ? 80 : (uint16_t)atoi(hp.substr(dos + 1).c_str());
    return true;
  }
  void addHeader(const String& k, const String& v) { cabeceras_ += std::string(k.c_str()) + ": " + v.c_str() + "\r\n"; }
  int POST(const String& datos) {
    if (!c_ || !c_->connect(host_.c_str(), puerto_, espera_conexion_)) return -1;  // HTTPC_ERROR_CONNECTION_REFUSED
    std::string pedido = "POST " + ruta_ + " HTTP/1.1\r\nHost: " + host_ + "\r\n" + cabeceras_ +
                         "Content-Length: " + std::to_string(datos.length()) + "\r\nConnection: close\r\n\r\n" + datos.c_str();
    c_->write((const uint8_t*)pedido.data(), pedido.size());
    std::string resp;
    unsigned long t0 = millis();
    while (millis() - t0 < (unsigned long)espera_) {
      if (c_->esperarDatos(50)) {
        int b;
        bool algo = false;
        while (c_->available() && (b = c_->read()) >= 0) { resp += (char)b; algo = true; }
        if (!algo && !c_->connected()) break;
      } else if (!c_->connected()) {
        break;
      }
    }
    auto fin = resp.find("\r\n\r\n");
    if (resp.size() < 12 || fin == std::string::npos) return -11;  // HTTPC_ERROR_READ_TIMEOUT
    cuerpo_ = String(resp.substr(fin + 4).c_str());
    return atoi(resp.substr(9, 3).c_str());
  }
  String getString() { return cuerpo_; }
  void end() {
    if (c_) c_->stop();
  }
};
