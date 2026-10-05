// Banco de prueba en PC para PasoSeguro.ino: versión mínima de Arduino.h (solo lo que usa el sketch).
// No reemplaza a la placa: sirve para compilar el sketch y probar que habla bien con el borde.
#pragma once
#include <cstdarg>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <functional>
#include <string>

#define HIGH 1
#define LOW 0
#define INPUT 0
#define OUTPUT 1
#define INPUT_PULLUP 2
#define constrain(amt, low, high) ((amt) < (low) ? (low) : ((amt) > (high) ? (high) : (amt)))

unsigned long millis();
void delay(unsigned long ms);
void pinMode(int pin, int modo);
void digitalWrite(int pin, int valor);
int digitalRead(int pin);
int analogRead(int pin);
long map(long x, long in_min, long in_max, long out_min, long out_max);

class String {
 public:
  std::string s;
  String() {}
  String(const char* c) : s(c ? c : "") {}
  String(const String& o) = default;
  String& operator=(const String& o) = default;
  explicit String(char c) : s(1, c) {}
  explicit String(int v) : s(std::to_string(v)) {}
  explicit String(unsigned int v) : s(std::to_string(v)) {}
  explicit String(long v) : s(std::to_string(v)) {}
  explicit String(unsigned long v) : s(std::to_string(v)) {}
  explicit String(double v, int dec = 2) {
    char b[48];
    snprintf(b, sizeof b, "%.*f", dec, v);
    s = b;
  }
  String& operator+=(const String& o) { s += o.s; return *this; }
  String& operator+=(const char* c) { s += c; return *this; }
  String& operator+=(char c) { s += c; return *this; }
  bool operator==(const char* c) const { return s == c; }
  bool operator==(const String& o) const { return s == o.s; }
  bool operator!=(const char* c) const { return s != c; }
  char operator[](unsigned i) const { return i < s.size() ? s[i] : 0; }
  unsigned length() const { return s.size(); }
  const char* c_str() const { return s.c_str(); }
  int indexOf(const char* sub, unsigned desde = 0) const {
    auto p = s.find(sub, desde);
    return p == std::string::npos ? -1 : (int)p;
  }
  int indexOf(char c, unsigned desde = 0) const {
    auto p = s.find(c, desde);
    return p == std::string::npos ? -1 : (int)p;
  }
  String substring(unsigned a) const { return a >= s.size() ? String() : String(s.substr(a).c_str()); }
  String substring(unsigned a, unsigned b) const {
    if (a >= s.size() || b <= a) return String();
    return String(s.substr(a, b - a).c_str());
  }
  void remove(unsigned i) { if (i < s.size()) s.erase(i); }
  long toInt() const { return atol(s.c_str()); }
};
inline String operator+(const String& a, const String& b) { String r(a); r += b; return r; }
inline String operator+(const String& a, const char* b) { String r(a); r += b; return r; }
inline String operator+(const char* a, const String& b) { String r(a); r += b; return r; }

struct SerialFalso {
  void begin(long) {}
  void print(const char* t) { fputs(t, stdout); fflush(stdout); }
  void print(const String& t) { print(t.c_str()); }
  void println() { print("\n"); }
  void println(const char* t) { print(t); println(); }
  void println(const String& t) { println(t.c_str()); }
  int printf(const char* f, ...) __attribute__((format(printf, 2, 3))) {
    va_list a;
    va_start(a, f);
    int r = vprintf(f, a);
    va_end(a);
    fflush(stdout);
    return r;
  }
};
extern SerialFalso Serial;
