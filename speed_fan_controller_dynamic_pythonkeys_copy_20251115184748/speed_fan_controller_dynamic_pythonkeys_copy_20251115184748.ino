// Dual Fan control via Serial – works with the Python Flask UI
// Pin 11 = Fan A (PWM)   Pin 10 = Fan B (PWM)
// Use transistor/MOSFET/driver for high-current fans!

const int FAN_A_PIN = 11;
const int FAN_B_PIN = 10;

void setup() {
  Serial.begin(115200);
  pinMode(FAN_A_PIN, OUTPUT);
  pinMode(FAN_B_PIN, OUTPUT);
  analogWrite(FAN_A_PIN, 0);
  analogWrite(FAN_B_PIN, 0);
  Serial.println("Dual fan controller ready.");
  Serial.println("Format: <fan><cmd>  (a/b)(0-9fs)");
}

void loop() {
  if (Serial.available() < 2) return;   // need fan + cmd

  char fan = Serial.read();
  char cmd = Serial.read();

  // ----- validate fan -----
  const int *pin;
  if (fan == 'a' || fan == 'A') pin = &FAN_A_PIN;
  else if (fan == 'b' || fan == 'B') pin = &FAN_B_PIN;
  else { Serial.println("?"); return; }

  // ----- compute speed -----
  int speed = 0;
  cmd = tolower(cmd);
  if (cmd >= '0' && cmd <= '9') {
    speed = map(cmd - '0', 0, 9, 0, 255);   // 0-9 → 0-255
  }
  else if (cmd == 'f') speed = 255;
  else if (cmd == 's') speed = 0;
  else { Serial.println("?"); return; }

  // ----- apply -----
  analogWrite(*pin, speed);

  // ----- feedback (percent + which fan) -----
  int percent = map(speed, 0, 255, 0, 100);
  Serial.print((fan == 'a' || fan == 'A') ? "A" : "B");
  Serial.print(percent);
  Serial.println("%");
}