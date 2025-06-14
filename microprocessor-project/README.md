# Shadow Pattern Lockbox (Arduino Project)

This project implements a **contactless and secure password entry system** using shadow patterns detected by LDR sensors. The system mimics a digital lockbox where users unlock access by triggering a sequence of shadows over light sensors in a specific order.

---

## Project Info

- **Project Name:** Shadow Pattern Lockbox  
- **Language:** Arduino (C++)  
- **Author:** Betul Aslan - Melis Karadag 

---

## Academic Info

- **Course:** Microprocessors  
- **Institution:** Galatasaray University  
- **Department:** Computer Engineering  
- **Academic Year:** 2024–2025 Spring  
- **Assignment:** Term Project  

---

## Components Used

- Arduino Uno  
- 4 × LDR Light Sensors  
- 1 × 16x2 LCD (I2C)  
- 1 × 4x2 Keypad  
- 1 × Servo Motor (SG90)  
- 1 × Red LED  
- 1 × Green LED  
- 1 × Buzzer  
- Jumper wires, Breadboard  

---

## How It Works

1. **Unlocking Logic:**  
   - The correct “shadow password” consists of a predefined sequence of sensor activations (e.g., covering sensors in the order 1 → 2 → 3 → 4).
   - When the user covers the sensors in the correct sequence, the servo unlocks the box and LEDs indicate success.

2. **Keypad Features:**  
   - Pressing **‘B’** enters admin mode where a 4-digit master code is required to reset the shadow password.
   - After successful admin access, the new shadow password can be set using buttons 1–4.
   - Pressing **‘A’** locks the box again.

3. **Security Features:**  
   - 3 incorrect attempts trigger a **security lock mode** for 10 seconds.
   - During this period, access is blocked, and buzzer + LED warning is activated.

---

## Circuit Connections

| Component       | Arduino Pin     |
|----------------|------------------|
| LDR Sensors    | D2, D3, D4, D5    |
| Keypad Rows    | D7, D8            |
| Keypad Columns | D9, D10, D11, D12 |
| Servo          | D6                |
| Red LED        | A0                |
| Green LED      | A1                |
| Buzzer         | A2                |
| LCD (I2C)      | SDA/SCL (A4/A5)   |

---

## Files

- `shadow_pattern_lockbox.ino` — Full Arduino sketch containing shadow sensor logic, keypad input handling, and LCD feedback.

---

## Notes

- The system uses **contactless interaction** for both unlocking and password reset.
- LDR sensors detect light interruption as a form of gesture-based input.
- Ideal for secure storage scenarios where physical contact is not desired.
