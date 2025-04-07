#ifndef RFID_SENSOR_H
#define RFID_SENSOR_H

#include <MFRC522.h>
#include <SPI.h>

class RFID_Sensor {
private:
    MFRC522 device;
    String lastCardUID;

public:
    RFID_Sensor() {}
    
    // Khởi tạo module RFID
    void init(int SS_PIN, int RST_PIN);
    
    // Kiểm tra và đọc thẻ
    bool cardDetect();
    
    // Lấy UID của thẻ cuối cùng được đọc
    String getLastCardUID() { return lastCardUID; }
    
    // Chuyển đổi byte array sang string
    String uidToString(byte* buffer, byte bufferSize);
};

#endif