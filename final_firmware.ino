// final_firmware.ino
// Firmware code for Signal Processing and Serial Communication
// SF4 : Data Logger
// ak2444 and jz587

// Include necessary libraries
#include <DHT.h>
#include <Wire.h>
#include "DFRobot_BMP3XX.h"

// Pin Assignments
//LEDs
#define LED_PIN2   2       // Red LED
#define LED_PIN3   3       // Green LED
#define LED_PIN4   4      // Yellow LED

// Temperature and Humidity Sensor
#define DHTPIN    5  
#define DHTTYPE   DHT11
DHT dht(DHTPIN, DHTTYPE);

// Light Dependent Resistor
#define LDR_PIN   A1   

// Pressure Sensor
#define BMP_SDA   18
#define BMP_SCL   19
DFRobot_BMP388_I2C bmp388;

// Wind Sensor
#define WIND_PIN  A3

// Arduino Setup
void setup() {
  pinMode(LED_PIN2, OUTPUT);
  pinMode(LED_PIN3, OUTPUT);
  pinMode(LED_PIN4, OUTPUT);

  // pinMode(LDR_PIN, INPUT);

  digitalWrite(LED_PIN2, LOW);
  digitalWrite(LED_PIN3, LOW);
  digitalWrite(LED_PIN4, LOW);

  dht.begin();
  bmp388.begin();

  Serial.begin(9600); // Setting Baud Rate to 9600
}

void loop() {
  // Read and process sensor values

  // Temp and Humidity
  float h = dht.readHumidity();
  float t = dht.readTemperature();
  if (isnan(h) || isnan(t)) {
    Serial.println("ERR");
    delay(500);
    return;
  }

  // Light Intensity 
  int rawL = analogRead(LDR_PIN);
  float vL  = rawL * (5.0 / 1023.0);
  float r   = (vL / (5.0 - vL)) * 8.3;
  float lux = 732.5 * pow(r, -0.6592);

  // Pressure
  float p = bmp388.readPressPa() / 100.0;

  // Wind Speed
  int rawW = analogRead(WIND_PIN);
  float windV = rawW * (5.0 / 1023.0);

  // Writing to LEDs upon breach of threshold values

  // Temp crosses 26 degrees
  if (t > 26.0) {
    digitalWrite(LED_PIN2, HIGH);
  }
  else{
    digitalWrite(LED_PIN2, LOW);
  }

  // Light Intensity falls below 100 lux
  if (lux < 100.0) {
    digitalWrite(LED_PIN3, HIGH);
  }
  else{
    digitalWrite(LED_PIN3, LOW);
  }

  // 2-way communication between PC and Arduino (receiving commands from PC upon failed checksum)
  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();
    if (cmd == "LED_ON") {
      digitalWrite(LED_PIN4, HIGH);
    }
    else if (cmd == "LED_OFF") {
      digitalWrite(LED_PIN4, LOW);
    }
  }

  // Compute XOR Checksum - part of communication protocol
  String payload = "HUM:"   + String(h,1)
                 + " T:"    + String(t,1)
                 + " LUX:"  + String(lux,1)
                 + " PRES:" + String(p,1)
                 + " WIND:" + String(windV,2);

  uint8_t checksum = 0;
  for (size_t i = 0; i < payload.length(); i++) {
    checksum ^= payload[i];
  }

  // Transmit with checksum
  Serial.print(payload);
  Serial.print(" CHK:");
  if (checksum < 16) Serial.print('0');     
  Serial.println(checksum, HEX);

  delay(500);  // 0.5s delay
}
