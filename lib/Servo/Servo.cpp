#include "Servo.h"

void servoMotor::init(int IO, int ir_pin) {
    this->Servo_motor.attach(IO);
    this->currentAngle = 45;
    this->isOpen = false;
    this->ir_sensor = IR_Sensor(ir_pin, true);
    this->ir_sensor.begin();
    
    // Di chuyển về vị trí đóng
    this->Servo_motor.write(this->currentAngle);
    
    Serial.printf("[SERVO] Initialized on pin %d with IR sensor on pin %d\n", IO, ir_pin);
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
        this->startTimer(); // Bắt đầu đếm thời gian
    } else {
        Serial.println("[SERVO] Barrier already open");
    }
}

void servoMotor::closeBarrier() {
    if (this->isOpen) {
        Serial.println("[SERVO] Closing barrier...");
        this->controlAngle(45);
        this->stopTimer(); // Dừng đếm thời gian
        this->throughStatus = 0; // Reset throughStatus về 0
        Serial.println("[SERVO] Reset throughStatus to 0");
    } else {
        Serial.println("[SERVO] Barrier already closed");
    }
}

bool servoMotor::checkIRSensor() {
    if(this->ir_sensor.stateChanged()) {
        if(this->throughStatus == 0) {
            this->throughStatus = 1;
            Serial.println("[SERVO] IR Sensor: First detection");
        }
        else if(this->throughStatus == 1) {
            this->throughStatus = 2;
            Serial.println("[SERVO] IR Sensor: Second detection - Vehicle passed");
            this->closeBarrier(); // Đóng barrier khi xe đã đi qua
            return true;
        }
    }
    return false;
}

void servoMotor::updateTimer() {
    if (this->timerActive && this->isOpen) {
        if (millis() - this->openTimer >= BARRIER_TIMEOUT) {
            Serial.println("[SERVO] Timer expired - closing barrier");
            this->closeBarrier();
        }
    }
}

bool servoMotor::isTimerExpired() {
    return this->timerActive && (millis() - this->openTimer >= BARRIER_TIMEOUT);
}

void servoMotor::startTimer() {
    this->openTimer = millis();
    this->timerActive = true;
    Serial.println("[SERVO] Timer started");
}

void servoMotor::stopTimer() {
    this->timerActive = false;
    Serial.println("[SERVO] Timer stopped");
}