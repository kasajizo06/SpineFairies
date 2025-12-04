#include <SoftwareWire.h>
#include <Wire.h>
#include "MPU6050.h"
#include <SoftwareSerial.h>

SoftwareWire Wire1(A2, A3);
SoftwareWire Wire2(A0, A1);
MPU6050 mpu(0x68);

void setup() {
  Serial.begin(9600);
  Wire1.begin();
  Wire1.begin();
  Wire2.begin();
}

String readMPU(SoftwareWire &myWire) {
  myWire.beginTransmission(0x68);
  myWire.write(0x3B);
  myWire.endTransmission(false);
  myWire.requestFrom(0x68, 6, true);

  int16_t ax = (myWire.read() << 8) | myWire.read();
  int16_t ay = (myWire.read() << 8) | myWire.read();
  int16_t az = (myWire.read() << 8) | myWire.read();

  String buffer = "";
  buffer += String(ax)+","+ String(ay) +","+ String(az);
  return buffer;
}

void loop() {
  String buffer;
  buffer = readMPU(Wire1) + "|" + readMPU(Wire2);
  Serial.println(buffer);
  delay(100);
}