#include <Arduino.h>
#include "RFID_Sensor.h"
#include "Servo.h"
#include "pins_config.h"
#include "IR_Sensor.h"

// Thêm thư viện FreeRTOS
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

// Khởi tạo đối tượng cơ bản
RFID_Sensor rfid_in;
RFID_Sensor rfid_out;
servoMotor barrier_in;
servoMotor barrier_out;

// Khởi tạo cảm biến hồng ngoại cho 3 vị trí đỗ xe
IR_Sensor ir_sensor1(IR_SENSOR1_PIN, true);  // true nếu logic đảo
IR_Sensor ir_sensor2(IR_SENSOR2_PIN, true);
IR_Sensor ir_sensor3(IR_SENSOR3_PIN, true);

// Task xử lý barrier vào
void barrierInTask(void * parameter) {
    while(1) {
        // Kiểm tra cảm biến và thời gian
        barrier_in.checkIRSensor();
        barrier_in.updateTimer();
        vTaskDelay(50 / portTICK_PERIOD_MS);
    }
}

// Task xử lý barrier ra
void barrierOutTask(void * parameter) {
    while(1) {
        // Kiểm tra cảm biến và thời gian
        barrier_out.checkIRSensor();
        barrier_out.updateTimer();
        vTaskDelay(50 / portTICK_PERIOD_MS);
    }
}

void setup() {
    Serial.begin(SERIAL_BAUD);
    
    // Khởi tạo RFID và Servo
    rfid_in.init(RFID_IN_SS_PIN, RFID_IN_RST_PIN, 1);
    rfid_out.init(RFID_OUT_SS_PIN, RFID_OUT_RST_PIN, 0);
    barrier_in.init(SERVO_IN_PIN, IR_SENSOR_IN);
    barrier_out.init(SERVO_OUT_PIN, IR_SENSOR_OUT);
    
    // Khởi tạo cảm biến hồng ngoại
    ir_sensor1.begin();
    ir_sensor2.begin();
    ir_sensor3.begin();
    
    // Tạo task cho mỗi barrier
    xTaskCreatePinnedToCore(
        barrierInTask,   // Task function
        "BarrierInTask", // Task name
        10000,           // Stack size
        NULL,            // Parameters
        1,              // Priority
        NULL,           // Task handle
        0               // Core ID (0 or 1)
    );
    
    xTaskCreatePinnedToCore(
        barrierOutTask,
        "BarrierOutTask",
        10000,
        NULL,
        1,
        NULL,
        1
    );
    
    Serial.println("[SYSTEM] Ready");
}

void loop() { 
    rfid_in.cardDetect();
    rfid_out.cardDetect();
    
    // Kiểm tra lệnh từ Serial
    if (Serial.available() > 0) {
        String command = Serial.readStringUntil('\n');
        if (command == "OPEN_BARRIER_IN") {
            Serial.println("OPENING_BARRIER_IN");
            barrier_in.openBarrier();
        }
        else if (command == "OPEN_BARRIER_OUT") {
            Serial.println("OPENING_BARRIER_OUT");
            barrier_out.openBarrier();
        }
    }
    
    // Kiểm tra trạng thái cảm biến và gửi cập nhật
    if (ir_sensor1.stateChanged()) {
        Serial.print("SLOT1:");
        Serial.println(ir_sensor1.getStatus() ? "0" : "1");
    }
    
    if (ir_sensor2.stateChanged()) {
        Serial.print("SLOT2:");
        Serial.println(ir_sensor2.getStatus() ? "0" : "1");
    }
    
    if (ir_sensor3.stateChanged()) {
        Serial.print("SLOT3:");
        Serial.println(ir_sensor3.getStatus() ? "0" : "1");
    }
    
    delay(50);
}
