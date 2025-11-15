// Fan control via Serial - works with ultra-responsive Python script
// Pin 11 = PWM output to fan (use transistor/MOSFET/driver for high current!)

const int FAN_PIN = 11;

void setup() {
  Serial.begin(115200);
  pinMode(FAN_PIN, OUTPUT);
  analogWrite(FAN_PIN, 0); // Start stopped
  Serial.println("Fan controller ready. Use 0-9, f=full, s=stop");
}

void loop() {
  if (Serial.available() > 0) {
  char cmd = Serial.read();

    int speed = 0; // 0 to 255 for analogWrite

    if (cmd >= '0' && cmd <= '9') {
      speed = map(cmd - '0', 0, 9, 0, 255); // 0-9 → 0-255
    }
    else if (cmd == 'f' || cmd == 'F') {
      speed = 255;
    }
    else if (cmd == 's' || cmd == 'S') {
      speed = 0;
    }
    else {
      // Ignore invalid commands, but optionally echo
      Serial.print("?");
      return;
    }

    // Apply speed
    analogWrite(FAN_PIN, speed);

    // Send feedback: percentage
    int percent = map(speed, 0, 255, 0, 100);
    Serial.print(percent);
    Serial.println("%");
  }
}