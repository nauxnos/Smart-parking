import pyodbc
from datetime import datetime
import logging
import pytz  # Thêm import pytz

class DatabaseHandler:
    def __init__(self):
        self.server = 'hehe\\SQLEXPRESS'
        self.database = 'ParkingSystem'
        self.connection = None
        self.timezone = pytz.timezone('Asia/Bangkok')  # Bangkok sử dụng GMT+7
    
    def get_connection(self):
        """Tạo kết nối đến SQL Server"""
        if not self.connection:
            try:
                self.connection = pyodbc.connect(
                    'DRIVER={ODBC Driver 17 for SQL Server};'
                    f'SERVER={self.server};DATABASE={self.database};'
                    'Trusted_Connection=yes;'
                )
                logging.info("Đã kết nối database thành công")
            except Exception as e:
                logging.error(f"Lỗi kết nối database: {e}")
                return None
        return self.connection

    def get_current_time(self):
        """Lấy thời gian hiện tại theo GMT+7"""
        return datetime.now(self.timezone)

    def save_vehicle_log(self, rfid, plate_number):
        """Lưu thông tin xe vào/ra"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            current_time = self.get_current_time()
            
            # Kiểm tra xe đã có trong hệ thống chưa
            cursor.execute("SELECT status FROM Logs WHERE plate_number = ?", plate_number)
            result = cursor.fetchone()
            
            if result is None:
                # Xe vào - tạo bản ghi mới
                cursor.execute("""
                    INSERT INTO Logs (rfid, plate_number, time_in, status)
                    VALUES (?, ?, ?, ?)
                """, (rfid, plate_number, current_time, 'IN'))
            else:
                # Xe ra - cập nhật bản ghi
                cursor.execute("""
                    UPDATE Logs 
                    SET time_out = ?, status = 'OUT'
                    WHERE rfid = ? AND status = 'IN'
                """, (current_time, rfid))
                
            conn.commit()
            logging.info(f"Đã lưu log: RFID={rfid}, Biển số={plate_number}")
            return True
            
        except Exception as e:
            logging.error(f"Lỗi khi lưu vào database: {e}")
            return False

    def get_vehicle_logs(self):
        """Lấy danh sách các xe từ database"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    rfid,
                    plate_number,
                    time_in,
                    time_out,
                    status
                FROM Logs 
                ORDER BY time_in DESC
            """)
            columns = [column[0] for column in cursor.description]
            results = []
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))
            return results
        except Exception as e:
            logging.error(f"Lỗi khi lấy dữ liệu: {e}")
            return []

    def search_vehicle_logs(self, plate_number):
        """Tìm kiếm xe theo biển số"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            query = """
                SELECT * FROM Logs 
                WHERE plate_number LIKE ?
                ORDER BY time_in DESC
            """
            cursor.execute(query, f'%{plate_number}%')
            
            columns = [column[0] for column in cursor.description]
            results = []
            
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))
                
            return results
            
        except Exception as e:
            logging.error(f"Lỗi khi tìm kiếm: {e}")
            return []

    def close(self):
        """Đóng kết nối database"""
        if self.connection:
            self.connection.close()
            self.connection = None