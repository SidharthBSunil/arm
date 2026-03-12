#include <ESP32Servo.h>

Servo myServo;

int servoPin = 21;
int angle = 90;

void setup() {

  Serial.begin(115200);

  myServo.attach(servoPin);

  Serial.println("Type servo angle (0-180) and press ENTER:");

}

void loop() {

  if (Serial.available()) {

    angle = Serial.parseInt();

    if (angle >= 0 && angle <= 180) {

      myServo.write(angle);

      Serial.print("Servo moved to: ");
      Serial.println(angle);

    } 
    else {

      Serial.println("Invalid angle. Enter 0-180.");

    }

  }

}
