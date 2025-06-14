#include <Wire.h>
#include <LiquidCrystal_I2C.h>
#include <Servo.h>

LiquidCrystal_I2C lcd(0x27, 16, 2);
Servo boxServo;

const int NUM_SENSORS = 4;
const int sensorPins[NUM_SENSORS] = {2, 3, 4, 5};

const int rowPins[2] = {7, 8};            
const int colPins[4] = {9, 10, 11, 12};   

const int redLedPin = A0;
const int greenLedPin = A1;
const int buzzerPin = A2;
const int servoPin = 6;

const char KEYPAD_MAP[2][4] = {
  {'1', '2', '3', 'A'},
  {'4', '5', '6', 'B'}
};

const String ADMIN_RESET_CODE = "5555"; 

int correctCode[NUM_SENSORS] = {0, 1, 2, 3};
int inputCode[NUM_SENSORS];
int inputIndex = 0;
int activeSensor = -1;
bool alreadyRecorded = false;
bool systemUnlocked = false;
bool boxOpen = false;

bool resetMode = false;         
bool resetCodeMode = false;    
String adminBuffer = "";        
String newPasswordBuffer = "";  

bool buttonPrevState[8] = {HIGH, HIGH, HIGH, HIGH, HIGH, HIGH, HIGH, HIGH};

int wrongAttempts = 0;
bool securityLock = false;
unsigned long securityStartTime = 0;
const int securityDuration = 10000;

void setup() {
  Serial.begin(9600);
  lcd.init();
  lcd.backlight();
  lcd.setCursor(0, 0);
  lcd.print("Sifre Giriniz");

  boxServo.attach(servoPin);
  boxServo.write(165);

  for (int i = 0; i < NUM_SENSORS; i++) {
    pinMode(sensorPins[i], INPUT);
  }

  for (int i = 0; i < 2; i++) {
    pinMode(rowPins[i], OUTPUT);
    digitalWrite(rowPins[i], HIGH);
  }

  for (int i = 0; i < 4; i++) {
    pinMode(colPins[i], INPUT_PULLUP);
  }

  pinMode(redLedPin, OUTPUT);
  pinMode(greenLedPin, OUTPUT);
  pinMode(buzzerPin, OUTPUT);

  digitalWrite(greenLedPin, LOW);
  digitalWrite(redLedPin, HIGH);
  digitalWrite(buzzerPin, LOW);
}

void loop() {
  if (securityLock) {
    handleSecurityLock();
    return;
  }

  readKeypad();

  if (boxOpen || resetMode || resetCodeMode) {
    return;
  }

  if (inputIndex >= NUM_SENSORS) return;

  if (activeSensor == -1) {
    for (int i = 0; i < NUM_SENSORS; i++) {
      if (digitalRead(sensorPins[i]) == HIGH) {
        activeSensor = i;
        alreadyRecorded = false;
        break;
      }
    }
  }

  if (activeSensor != -1) {
    int state = digitalRead(sensorPins[activeSensor]);

    if (state == HIGH && !alreadyRecorded) {
      bool alreadyEntered = false;
      for (int k = 0; k < inputIndex; k++) {
        if (inputCode[k] == activeSensor) {
          alreadyEntered = true;
          break;
        }
      }

      if (!alreadyEntered) {
        inputCode[inputIndex++] = activeSensor;
        Serial.print("Giris eklendi: Sensor ");
        Serial.println(activeSensor + 1);
        alreadyRecorded = true;

        if (inputIndex == NUM_SENSORS) {
          checkCode();
        }
      }
    }
    
    if (state == LOW) {
      activeSensor = -1;
      alreadyRecorded = false;
    }
  }
}

void readKeypad() {
  static int currentRow = 0;

  for (int r = 0; r < 2; r++) {
    digitalWrite(rowPins[r], r == currentRow ? LOW : HIGH);
  }

  for (int c = 0; c < 4; c++) {
    bool buttonState = digitalRead(colPins[c]);
    int buttonIndex = currentRow * 4 + c;

    if (buttonPrevState[buttonIndex] == HIGH && buttonState == LOW) {
      char pressedKey = KEYPAD_MAP[currentRow][c];
      if (!resetMode && !resetCodeMode) {
        if (pressedKey == 'A' && boxOpen) {
          lcd.clear();
          lcd.print("Kilit Kapandi");
          boxServo.write(165);
          digitalWrite(greenLedPin, LOW);
          digitalWrite(redLedPin, HIGH);
          boxOpen = false;
          delay(2000);
          lcd.clear();
          lcd.print("Sifre Giriniz");
        }

        else if (pressedKey == 'B') {
          resetCodeMode = true;
          adminBuffer = "";
          lcd.clear();
          lcd.print("Admin Kodunu Giriniz:");
          lcd.setCursor(0, 1);
        }
      }
      
      else if (resetCodeMode) {
        if (pressedKey == 'B') { 
          resetCodeMode = false;
          adminBuffer = "";
          lcd.clear();
          lcd.print("Sifre Giriniz");
        }

        else if (pressedKey >= '0' && pressedKey <= '9') {
          if (adminBuffer.length() < 4) {
            adminBuffer += pressedKey;
            lcd.setCursor(0, 1);
            for (int i = 0; i < adminBuffer.length(); i++) lcd.print('*');
          }

          if (adminBuffer.length() == 4) {
            delay(400);
            if (adminBuffer == ADMIN_RESET_CODE) {
              resetCodeMode = false;
              resetMode = true;
              newPasswordBuffer = "";
              lcd.clear();
              lcd.setCursor(0, 0);
              lcd.print("Sifre: ");
            } else {
              lcd.clear();
              lcd.print("Kod Yanlis");
              errorBuzzer(); 
              delay(1000);
              resetCodeMode = false;
              adminBuffer = "";
              lcd.clear();
              lcd.print("Sifre Giriniz");
            }
          }
        }
      }

      else if (resetMode) {
        if (pressedKey == 'B') { 
          resetMode = false;
          newPasswordBuffer = "";
          lcd.clear();
          lcd.print("Sifre Giriniz");
        }

        else if (pressedKey >= '1' && pressedKey <= '4') {
          if (newPasswordBuffer.indexOf(pressedKey) == -1 && newPasswordBuffer.length() < NUM_SENSORS) {
            newPasswordBuffer += pressedKey;
            lcd.clear();
            lcd.setCursor(0, 0);
            lcd.print("Sifre: ");
            for (int j = 0; j < newPasswordBuffer.length(); j++) {
              lcd.print(newPasswordBuffer[j]);
              if (j != newPasswordBuffer.length() - 1)
                lcd.print('-');
            }
          }
        }
        
        if (newPasswordBuffer.length() >= 4) {
          for (int j = 0; j < NUM_SENSORS; j++) {
            int val = newPasswordBuffer[j] - '1';
            correctCode[j] = val;
          }
          resetMode = false;
          newPasswordBuffer = "";
          lcd.clear();
          lcd.print("Sifre Degisti");
          delay(2000);
          lcd.clear();
          lcd.print("Sifre Giriniz");
        }
      }
      delay(50);
    }
    buttonPrevState[buttonIndex] = buttonState;
  }

  for (int r = 0; r < 2; r++) {
    digitalWrite(rowPins[r], HIGH);
  }
  currentRow = (currentRow + 1) % 2;
}

void checkCode() {
  bool correct = true;
  for (int i = 0; i < NUM_SENSORS; i++) {
    if (inputCode[i] != correctCode[i]) {
      correct = false;
      break;
    }
  }
  
  if (correct) {
    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("Sifre Dogru");
    lcd.setCursor(0, 1);
    lcd.print("Kilit Acildi");
    boxServo.write(65);
    digitalWrite(greenLedPin, HIGH);
    digitalWrite(redLedPin, LOW);
    systemUnlocked = true;
    boxOpen = true;
    wrongAttempts = 0;
  } else {
    wrongAttempts++;
    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("Sifre Yanlis");
    lcd.setCursor(0, 1);
    lcd.print("Kalan Hak: ");
    lcd.print(3 - wrongAttempts);
    errorBuzzer();

    if (wrongAttempts >= 3) {
      securityLock = true;
      securityStartTime = millis();
      lcd.clear();
      lcd.print("Guvenlik Modu");
      delay(1000);
    }
  }
  delay(500);
  resetInput();
}

void resetInput() {
  inputIndex = 0;
  activeSensor = -1;
  alreadyRecorded = false;
}

void errorBuzzer() {
  for (int i = 0; i < 2; i++) {
    digitalWrite(redLedPin, LOW);
    delay(200);
    digitalWrite(redLedPin, HIGH);
    delay(200);
  }
  digitalWrite(buzzerPin, HIGH);
  delay(1000);
  digitalWrite(buzzerPin, LOW);
}

void handleSecurityLock() {
  unsigned long elapsed = millis() - securityStartTime;
  
  if (elapsed < securityDuration) {
    int secondsLeft = (securityDuration - elapsed) / 1000;
    lcd.setCursor(0, 0);
    lcd.print("Bekleyin: ");
    lcd.print(secondsLeft + 1);
    lcd.print("s   ");
    digitalWrite(redLedPin, millis() % 300 < 150 ? HIGH : LOW);
    digitalWrite(buzzerPin, HIGH);
  } else {
    securityLock = false;
    wrongAttempts = 0;
    lcd.clear();
    lcd.print("Sistem Acildi");
    delay(2000);
    lcd.clear();
    lcd.print("Sifre Giriniz");
    digitalWrite(buzzerPin, LOW);
    digitalWrite(redLedPin, HIGH);
  }
}
