#pragma once

#ifndef SERVO_MOTOR_H
#define SERVO_MOTOR_H

#include <ESP32Servo.h>

class servoMotor {
private:
    Servo Servo_motor;
    int currentAngle;
    bool isOpen;
    
public:
    servoMotor() : currentAngle(0), isOpen(false) {}
    
    void init(int IO);
    void controlAngle(int angle);
    void openBarrier();
    void closeBarrier();
    bool isBarrierOpen() { return isOpen; }
    int getCurrentAngle() { return currentAngle; }
};

#endif