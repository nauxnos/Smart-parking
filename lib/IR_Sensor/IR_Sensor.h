#ifndef IR_SENSOR_H
#define IR_SENSOR_H

#include <Arduino.h>

class IR_Sensor {
private:
    uint8_t pin;
    bool inverted;
    unsigned long debounceDelay;
    unsigned long lastDebounceTime;
    bool lastState;
    bool currentState;

public:
    IR_Sensor(uint8_t sensorPin, bool invertLogic = false);
    IR_Sensor() : pin(0), inverted(false), debounceDelay(0), lastDebounceTime(0), lastState(false), currentState(false) {}
    void begin();
    void updateStatus();
    bool getStatus();
    bool stateChanged();
    void setDebounceTime(unsigned long delay);
};

#endif