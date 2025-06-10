#pragma once

#ifndef SERVO_MOTOR_H
#define SERVO_MOTOR_H

#include <ESP32Servo.h>
#include <IR_Sensor.h>

class servoMotor {
private:
    Servo Servo_motor;
    int currentAngle;
    bool isOpen;
    IR_Sensor ir_sensor;
    
public:
    servoMotor() : currentAngle(0), isOpen(false), ir_sensor(), throughStatus(0) {}
    
    void init(int IO, int ir_pin);
    void controlAngle(int angle);
    void openBarrier();
    void closeBarrier();
    bool isBarrierOpen() { return isOpen; }
    int getCurrentAngle() { return currentAngle; }
    void checkIRSensor();
    int throughStatus;
};

#endif