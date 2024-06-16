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
#include <TimeLib.h>

MAX30105 particleSensor;
const int GSR = A0;

#define BUFFER_SIZE 100

#if defined(__AVR_ATmega328P__) || defined(__AVR_ATmega168__)
uint16_t irBuffer[BUFFER_SIZE]; // Infrared LED sensor data
uint16_t redBuffer[BUFFER_SIZE];  // Red LED sensor data
#else
uint32_t irBuffer[BUFFER_SIZE]; // Infrared LED sensor data
uint32_t redBuffer[BUFFER_SIZE];  // Red LED sensor data
#endif

void setup() {
  Serial.begin(115200); // Initialize serial communication at 115200 bits per second

  // Initialize sensor
  if (!particleSensor.begin(Wire, I2C_SPEED_FAST)) { // Use default I2C port, 400kHz speed
    Serial.println(F("MAX30105 was not found. Please check wiring/power."));
    while (1);
  }

  byte ledBrightness = 60; // Options: 0=Off to 255=50mA
  byte sampleAverage = 4; // Options: 1, 2, 4, 8, 16, 32
  byte ledMode = 2; // Options: 1 = Red only, 2 = Red + IR, 3 = Red + IR + Green
  byte sampleRate = 100; // Options: 50, 100, 200, 400, 800, 1000, 1600, 3200
  int pulseWidth = 411; // Options: 69, 118, 215, 411
  int adcRange = 4096; // Options: 2048, 4096, 8192, 16384

  particleSensor.setup(ledBrightness, sampleAverage, ledMode, sampleRate, pulseWidth, adcRange); // Configure sensor with these settings

  setTime(0, 0, 0, 1, 1, 2023); // Set initial time (adjust as needed)
  // Serial.println("Timestamp,Red,IR,GSR"); // Print CSV header
}

void loop() {
  const int bufferLength = BUFFER_SIZE; // Buffer length of 100 stores 4 seconds of samples running at 25sps

  // Read samples and print raw data in CSV format
  for (int i = 0; i < bufferLength; i++) {
    while (particleSensor.available() == false) // Do we have new data?
      particleSensor.check(); // Check the sensor for new data

    redBuffer[i] = particleSensor.getRed();
    irBuffer[i] = particleSensor.getIR();
    particleSensor.nextSample(); // We're finished with this sample so move to next sample

    // Get the current time
    unsigned long currentTime = now();
    // Print data in CSV format
    Serial.print(currentTime);
    Serial.print(",");
    Serial.print(redBuffer[i], DEC);
    Serial.print(",");
    Serial.print(irBuffer[i], DEC);
    Serial.print(",");
    
    // Read and print GSR sensor value
    int sensorValue = analogRead(GSR);
    Serial.println(sensorValue);
  }
}
