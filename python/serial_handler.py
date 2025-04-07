import serial
import serial.tools.list_ports
import time
import logging

class SerialHandler:
    def __init__(self, baud_rate=9600):
        self.baud_rate = baud_rate
        self.serial_port = None
        self.setup_logging()
        
    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger("SerialHandler")

    def find_arduino_port(self):
        """Tìm cổng Arduino tự động"""
        ports = serial.tools.list_ports.comports()
        for port in ports:
            if "CH340" in port.description or "Arduino" in port.description:
                return port.device
        return None

    def connect(self):
        """Kết nối với Arduino"""
        try:
            port = self.find_arduino_port()
            if not port:
                self.logger.error("Không tìm thấy Arduino!")
                return False

            self.serial_port = serial.Serial(port, self.baud_rate, timeout=1)
            self.logger.info(f"Đã kết nối với Arduino tại {port}")
            return True

        except serial.SerialException as e:
            self.logger.error(f"Lỗi kết nối: {e}")
            return False

    def disconnect(self):
        """Đóng kết nối Serial"""
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
            self.logger.info("Đã đóng kết nối Serial")

    def send_command(self, command):
        """Gửi lệnh tới ESP32"""
        if not self.serial_port or not self.serial_port.is_open:
            self.logger.error("Serial port chưa được kết nối")
            return False

        try:
            self.serial_port.write(f"{command}\n".encode())
            self.logger.info(f"Đã gửi lệnh: {command}")
            return True
        except serial.SerialException as e:
            self.logger.error(f"Lỗi gửi lệnh: {e}")
            return False

    def read_response(self):
        """Đọc phản hồi từ ESP32"""
        if not self.serial_port or not self.serial_port.is_open:
            return None

        try:
            if self.serial_port.in_waiting:
                response = self.serial_port.readline().decode().strip()
                self.logger.info(f"Nhận được: {response}")
                return response
        except serial.SerialException as e:
            self.logger.error(f"Lỗi đọc dữ liệu: {e}")
        return None