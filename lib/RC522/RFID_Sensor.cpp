#include "RFID_Sensor.h"

void RFID_Sensor::init(int SS_PIN, int RST_PIN) {
    SPI.begin();
    this->device = MFRC522(SS_PIN, RST_PIN);
    this->device.PCD_Init();
    Serial.println(F("RFID Module initialized"));
}

bool RFID_Sensor::cardDetect() {
    // Kiểm tra thẻ mới
    if (!this->device.PICC_IsNewCardPresent()) {
        return false;
    }
    
    // Đọc serial number của thẻ
    if (!this->device.PICC_ReadCardSerial()) {
        return false;
    }

    // Chuyển đổi UID thành string
    this->lastCardUID = uidToString(this->device.uid.uidByte, this->device.uid.size);
    
    Serial.print(F("Card detected - UID: "));
    Serial.println(this->lastCardUID);
    
    // Dừng crypto và halt thẻ
    this->device.PICC_HaltA();
    this->device.PCD_StopCrypto1();
    
    return true;
}

String RFID_Sensor::uidToString(byte* buffer, byte bufferSize) {
    String result = "";
    
    for (byte i = 0; i < bufferSize; i++) {
        // Thêm số 0 phía trước nếu giá trị hex chỉ có 1 chữ số
        if (buffer[i] < 0x10) {
            result += "0";
        }
        result += String(buffer[i], HEX);
        
        // Thêm dấu : giữa các byte, trừ byte cuối
        if (i < bufferSize - 1) {
            result += ":";
        }
    }
    
    result.toUpperCase();
    return result;
}