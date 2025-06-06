#include "IR_Sensor.h"

IR_Sensor::IR_Sensor(uint8_t sensorPin, bool invertLogic) {
    pin = sensorPin;
    inverted = invertLogic;
    debounceDelay = 50; // Default 50ms debounce
    lastDebounceTime = 0;
    lastState = false;
    currentState = false;
}

void IR_Sensor::begin() {
    pinMode(pin, INPUT);
    updateStatus();
    lastState = currentState;
}

void IR_Sensor::updateStatus() {
    currentState = digitalRead(pin);
}

bool IR_Sensor::getStatus() {
    return currentState;
}

bool IR_Sensor::stateChanged() {
    updateStatus();
    bool changed = false;
    if (currentState != lastState) {
        changed = true;
        lastState = currentState;
    }
    return changed;
}

void IR_Sensor::setDebounceTime(unsigned long delay) {
    debounceDelay = delay;
}