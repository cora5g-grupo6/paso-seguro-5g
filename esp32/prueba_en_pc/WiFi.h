// Banco de prueba en PC: WiFi y WiFiClient sobre sockets TCP reales.
// PRUEBA_HOST cambia la IP del borde (p. ej. 127.0.0.1) sin tocar el sketch.
#pragma once
#include "Arduino.h"

#include <arpa/inet.h>
#include <fcntl.h>
#include <netdb.h>
#include <netinet/in.h>
#include <netinet/tcp.h>
#include <poll.h>
#include <sys/ioctl.h>
#include <sys/socket.h>
#include <unistd.h>

#define WIFI_STA 1
#define WL_CONNECTED 3
#define WL_DISCONNECTED 6

struct IPAddress {
  const char* ip;
  String toString() const { return String(ip); }
};

class WiFiFalso {
 public:
  void mode(int) {}
  void begin(const char*, const char*) {}
  void setAutoReconnect(bool) {}
  bool reconnect() { return true; }
  int status() { return getenv("PRUEBA_SIN_WIFI") ? WL_DISCONNECTED : WL_CONNECTED; }
  IPAddress localIP() { return {"127.0.0.1"}; }
  int8_t RSSI() { return -58; }
  int8_t RSSI(int) { return -58; }
  int scanNetworks() { return 0; }
  String SSID(int) { return String(""); }
};
extern WiFiFalso WiFi;

class WiFiClient {
  int fd_ = -1;

 public:
  int connect(const char* host, uint16_t puerto, int32_t espera_ms = 3000) {
    stop();
    const char* destino = getenv("PRUEBA_HOST") ? getenv("PRUEBA_HOST") : host;
    addrinfo pista{}, *res = nullptr;
    pista.ai_family = AF_INET;
    pista.ai_socktype = SOCK_STREAM;
    char p[8];
    snprintf(p, sizeof p, "%u", puerto);
    if (getaddrinfo(destino, p, &pista, &res) != 0 || !res) return 0;
    fd_ = socket(res->ai_family, res->ai_socktype, res->ai_protocol);
    fcntl(fd_, F_SETFL, O_NONBLOCK);
    int r = ::connect(fd_, res->ai_addr, res->ai_addrlen);
    freeaddrinfo(res);
    if (r != 0) {
      pollfd pf{fd_, POLLOUT, 0};
      int err = 0;
      socklen_t largo = sizeof err;
      if (poll(&pf, 1, espera_ms) <= 0 || getsockopt(fd_, SOL_SOCKET, SO_ERROR, &err, &largo) != 0 || err != 0) {
        stop();
        return 0;
      }
    }
    int uno = 1;
    setsockopt(fd_, IPPROTO_TCP, TCP_NODELAY, &uno, sizeof uno);
    return 1;
  }
  size_t write(const uint8_t* buf, size_t n) {
    size_t total = 0;
    while (fd_ >= 0 && total < n) {
      ssize_t w = ::send(fd_, buf + total, n - total, 0);
      if (w > 0) total += w;
      else if (errno == EAGAIN) { pollfd pf{fd_, POLLOUT, 0}; poll(&pf, 1, 100); }
      else return total;
    }
    return total;
  }
  int available() {
    if (fd_ < 0) return 0;
    int n = 0;
    ioctl(fd_, FIONREAD, &n);
    return n;
  }
  int read() {
    uint8_t b;
    if (fd_ < 0) return -1;
    return ::recv(fd_, &b, 1, 0) == 1 ? b : -1;
  }
  bool esperarDatos(int ms) {
    if (fd_ < 0) return false;
    pollfd pf{fd_, POLLIN, 0};
    return poll(&pf, 1, ms) > 0;
  }
  bool connected() {
    if (fd_ < 0) return false;
    char c;
    ssize_t r = ::recv(fd_, &c, 1, MSG_PEEK);
    if (r == 0) return false;  // el otro lado cerró
    return r > 0 || errno == EAGAIN || errno == EWOULDBLOCK;
  }
  void stop() {
    if (fd_ >= 0) ::close(fd_);
    fd_ = -1;
  }
};
