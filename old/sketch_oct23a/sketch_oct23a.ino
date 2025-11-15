const int FAN_PIN = 9; // Pin connected to the FAN

void setup() {
  pinMode(FAN_PIN, OUTPUT); // Set the FAN pin as an output
}

void loop() {
  digitalWrite(FAN_PIN, HIGH); // Turn the FAN on
  Serial.print("Fan-High");
  delay(2000);                 // Wait for 1 second
  digitalWrite(FAN_PIN, LOW);  // Turn the FAN off
  Serial.print("Fan-Low");
  delay(2000);                 // Wait for 1 second
}