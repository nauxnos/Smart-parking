#include <Arduino.h>
#include "RFID_Sensor.h"
#include "Servo.h"
#include "pins_config.h"

// Khởi tạo đối tượng cơ bản
RFID_Sensor rfid_in;
servoMotor barrier_in;
bool lastCardState = false;

void setup() {
    Serial.begin(SERIAL_BAUD);
    
    // Chỉ khởi tạo RFID và Servo
    rfid_in.init(RFID_IN_SS_PIN, RFID_IN_RST_PIN);
    barrier_in.init(SERVO_IN_PIN);
    
    Serial.println("[SYSTEM] Ready");
}

void loop() {
    // Đọc RFID
    rfid_in.cardDetect();
    
    // Kiểm tra lệnh từ Serial
    if (Serial.available() > 0) {
        String command = Serial.readStringUntil('\n');
        if (command == "OPEN_BARRIER") {
            Serial.println("OPENING_BARRIER");
            barrier_in.openBarrier();
            delay(3000);
            barrier_in.closeBarrier();
        }
    }
    
    delay(50);
}
