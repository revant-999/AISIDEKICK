const int LIGHT_PIN = 9; 

enum DisplayState { IDLE, POMODORO };
DisplayState currentState = IDLE;

unsigned long pomodoroEndTime = 0;

void setup() {
  Serial.begin(115200);
  pinMode(LIGHT_PIN, OUTPUT);
  digitalWrite(LIGHT_PIN, LOW); 
}

void loop() {
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    command.trim(); 
    
    // We safely ignore the matrix commands so the Python script doesn't break
    if (command == "thinking" || command == "processing" || command == "greeting") {
      // Do nothing
    }
    else if (command.startsWith("pomodoro_sec_")) {
      int underscoreIdx = command.lastIndexOf("_");
      int secs = command.substring(underscoreIdx + 1).toInt();
      if (secs <= 0) secs = 30;
      
      pomodoroEndTime = millis() + (secs * 1000UL); 
      currentState = POMODORO;
      digitalWrite(LIGHT_PIN, HIGH);
    }
    else if (command.startsWith("pomodoro_")) {
      int underscoreIdx = command.indexOf("_");
      int mins = command.substring(underscoreIdx + 1).toInt();
      if (mins <= 0) mins = 25;
      
      pomodoroEndTime = millis() + (mins * 60000UL); 
      currentState = POMODORO;
      digitalWrite(LIGHT_PIN, HIGH); // Turn LED ON to indicate Pomodoro started
    }
    else if (command == "light_on") { 
      currentState = IDLE; // Override pomodoro timer
      digitalWrite(LIGHT_PIN, HIGH); 
    }
    else if (command == "light_off") { 
      currentState = IDLE; // Override pomodoro timer
      digitalWrite(LIGHT_PIN, LOW); 
    }
    
    Serial.println("ACK: " + command);
  }
  
  // State Management 
  if (currentState == POMODORO) {
    // If the current time has passed the end time, the Pomodoro is over
    if (millis() >= pomodoroEndTime) {
       currentState = IDLE; 
       digitalWrite(LIGHT_PIN, LOW); // Turn off the LED when finished!
    }
  }
}
