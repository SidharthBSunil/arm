#include <WiFi.h>
#include <WiFiUdp.h>
#include <ESP32Servo.h>

const char* ssid = "SpaceX";
const char* password = "12345678";

WiFiUDP udp;
unsigned int localPort = 5005;

uint8_t data[5];

// Servos
Servo baseServo;
Servo shoulderServo;
Servo elbowServo;
Servo wristServo;
Servo gripServo;

// Pins
const int basePin = 18;
const int shoulderPin = 19;
const int elbowPin = 21;
const int wristPin = 22;
const int gripPin = 23;

void setup()
{
  Serial.begin(115200);

  baseServo.attach(basePin);
  shoulderServo.attach(shoulderPin);
  elbowServo.attach(elbowPin);
  wristServo.attach(wristPin);
  gripServo.attach(gripPin);

  // Safe start
  baseServo.write(90);
  shoulderServo.write(90);
  elbowServo.write(90);
  wristServo.write(90);
  gripServo.write(60);

  WiFi.begin(ssid, password);

  Serial.print("Connecting");

  while (WiFi.status() != WL_CONNECTED)
  {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\nConnected");
  Serial.print("ESP32 IP: ");
  Serial.println(WiFi.localIP());

  udp.begin(localPort);
}

void loop()
{
  int packetSize = udp.parsePacket();

  if (packetSize == 5)
  {
    udp.read(data, 5);

    int base = data[0];
    int shoulder = data[1];
    int elbow = data[2];
    int wrist = data[3];
    int grip = data[4];

    // Move servos
    baseServo.write(base);
    shoulderServo.write(shoulder);
    elbowServo.write(elbow);
    wristServo.write(wrist);
    gripServo.write(grip);

    Serial.printf(
      "Base:%d Shoulder:%d Elbow:%d Wrist:%d Grip:%d\n",
      base, shoulder, elbow, wrist, grip
    );
  }
}
