#ifndef PINS_CONFIG_H
#define PINS_CONFIG_H

// RFID Pins - Entrance Gate
#define RFID_IN_SS_PIN     4    // SPI SS pin entrance
#define RFID_IN_RST_PIN    2    // Reset pin entrance

// RFID Pins - Exit Gate  
#define RFID_OUT_SS_PIN    5    // SPI SS pin exit
#define RFID_OUT_RST_PIN   17   // Reset pin exit

// Servo Pins
#define SERVO_IN_PIN       15   // Servo entrance gate
#define SERVO_OUT_PIN      12   // Servo exit gate

// IR Sensor pins
#define IR_SENSOR1_PIN 26  // D5
#define IR_SENSOR2_PIN 25  // D6
#define IR_SENSOR3_PIN 33  // D7

#define IR_SENSOR_IN 14
#define IR_SENSOR_OUT 27

// Status LEDs
#define LED_IN_READY       32   // Entrance gate ready
#define LED_OUT_READY      33   // Exit gate ready
#define LED_IN_ACTIVE      25   // Entrance gate active
#define LED_OUT_ACTIVE     26   // Exit gate active

// Debug và Serial
#define SERIAL_BAUD     9600

// Servo angles (degrees)
#define SERVO_ANGLE_CLOSED    0   
#define SERVO_ANGLE_OPEN    135   
#define SERVO_ANGLE_HALF     67   

#endif