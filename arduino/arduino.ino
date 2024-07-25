/*
 Hardware Connections (Breakoutboard to Arduino):
  -5V = 5V (3.3V is allowed)
  -GND = GND
  -SDA = A4 (or SDA)
  -SCL = A5 (or SCL)
  -INT = Not connected

GSR sensor:
  SIG = A0

OUTPUT:
  Timestamp,Red,IR,GSR
*/

#include <Wire.h>
#include "MAX30105.h"

MAX30105 particleSensor;

void setup() {
  Serial.begin(230400); 

  if (!particleSensor.begin(Wire, I2C_SPEED_FAST)) { 
    Serial.println(F("MAX30105 was not found. Please check wiring/power."));
    while (1);
  }

  byte ledBrightness = 60; 
  byte sampleAverage = 1;
  byte ledMode = 2; // Options: 1 = Red only, 2 = Red + IR, 3 = Red + IR + Green
  int sampleRate = 1000; // Options: 50, 100, 200, 400, 800, 1000, 1600, 3200
  int pulseWidth = 411; // Options: 69, 118, 215, 411
  int adcRange = 4096; // Options: 2048, 4096, 8192, 16384

  particleSensor.setup(ledBrightness, sampleAverage, ledMode, sampleRate, pulseWidth, adcRange); // Configure sensor with these settings
}
void loop() {
  // Read samples and print raw data in CSV format
  do {
      Serial.print(millis());
      Serial.print(",");
      Serial.print(particleSensor.getRed());
      Serial.print(",");
      Serial.print(particleSensor.getIR());
      Serial.print(",");
      Serial.println(analogRead(A0));
  }while (true);
}
