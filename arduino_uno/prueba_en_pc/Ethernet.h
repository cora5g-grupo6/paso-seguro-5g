// Banco de prueba en PC: Ethernet.h mínimo. EthernetClient abre conexiones TCP de verdad (sockets POSIX),
// así el sketch conversa con el borde real que corre en la PC.
#pragma once
#include "Arduino.h"
#include <arpa/inet.h>
#include <netinet/in.h>
#include <sys/select.h>
#include <sys/socket.h>
#include <unistd.h>

class IPAddress {
 public:
  uint8_t b[4] = {0, 0, 0, 0};
  IPAddress() {}
  IPAddress(uint8_t a, uint8_t c, uint8_t d, uint8_t e) { b[0] = a; b[1] = c; b[2] = d; b[3] = e; }
  uint8_t operator[](int i) const { return b[i]; }
};

extern bool pruebaDhcpOk;
extern const char* pruebaHostBorde;  // a dónde se conecta de verdad (por defecto 127.0.0.1)
extern bool pruebaBordeCaido;        // simula que el borde no responde

enum EthernetHardwareStatus { EthernetNoHardware, EthernetW5100, EthernetW5200, EthernetW5500 };
class EthernetClass {
 public:
  EthernetHardwareStatus hardwareStatus() { return EthernetW5100; }
  int begin(uint8_t*, unsigned long = 60000, unsigned long = 4000) { return pruebaDhcpOk ? 1 : 0; }
  void begin(uint8_t*, IPAddress, IPAddress, IPAddress, IPAddress) {}
  int maintain() { return 0; }
  IPAddress localIP() { return pruebaDhcpOk ? IPAddress(192, 168, 1, 33) : IPAddress(); }
  void setRetransmissionTimeout(uint16_t) {}
  void setRetransmissionCount(uint8_t) {}
};
extern EthernetClass Ethernet;

class EthernetClient {
  int fd = -1;
  bool cerrado = false;

 public:
  void setConnectionTimeout(uint16_t) {}
  int connect(IPAddress, uint16_t puerto) {
    if (pruebaBordeCaido) return 0;
    fd = socket(AF_INET, SOCK_STREAM, 0);
    if (fd < 0) return 0;
    sockaddr_in dir{};
    dir.sin_family = AF_INET;
    dir.sin_port = htons(puerto);
    inet_pton(AF_INET, pruebaHostBorde, &dir.sin_addr);
    if (::connect(fd, (sockaddr*)&dir, sizeof dir) != 0) {
      stop();
      return 0;
    }
    cerrado = false;
    return 1;
  }
  size_t print(const char* t) { return fd < 0 ? 0 : (size_t)send(fd, t, strlen(t), 0); }
  size_t print(const __FlashStringHelper* t) { return print(reinterpret_cast<const char*>(t)); }
  size_t print(long v) { char b[24]; snprintf(b, sizeof b, "%ld", v); return print(b); }
  size_t print(int v) { return print((long)v); }
  int available() {
    if (fd < 0 || cerrado) return 0;
    fd_set s;
    FD_ZERO(&s);
    FD_SET(fd, &s);
    timeval t{0, 0};
    return select(fd + 1, &s, nullptr, nullptr, &t) > 0 ? 1 : 0;
  }
  int read() {
    unsigned char c;
    if (recv(fd, &c, 1, 0) <= 0) {
      cerrado = true;
      return -1;
    }
    return c;
  }
  uint8_t connected() { return fd >= 0 && !cerrado; }
  void stop() {
    if (fd >= 0) close(fd);
    fd = -1;
  }
};
