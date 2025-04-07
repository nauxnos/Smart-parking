#include "Servo.h"

void servoMotor::init(int IO) {
    this->Servo_motor.attach(IO);
    this->currentAngle = 45;
    this->isOpen = false;
    
    // Di chuyển về vị trí đóng
    this->Servo_motor.write(this->currentAngle);
    
    Serial.printf("[SERVO] Initialized on pin %d\n", IO);
}

void servoMotor::controlAngle(int angle) {
    // Giới hạn góc từ 0-135
    angle = constrain(angle, 0, 135);
    
    this->Servo_motor.write(angle);
    this->currentAngle = angle;
    this->isOpen = (angle > 67);  // Coi như mở khi góc > 67 (một nửa của 135)
    
    Serial.printf("[SERVO] Moved to angle: %d\n", angle);
}

void servoMotor::openBarrier() {
    if (!this->isOpen) {
        Serial.println("[SERVO] Opening barrier...");
        this->controlAngle(135); // Thay đổi góc mở thành 135
    } else {
        Serial.println("[SERVO] Barrier already open");
    }
}

void servoMotor::closeBarrier() {
    if (this->isOpen) {
        Serial.println("[SERVO] Closing barrier...");
        this->controlAngle(45);
    } else {
        Serial.println("[SERVO] Barrier already closed");
    }
}