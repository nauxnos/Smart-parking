import pyodbc
import logging
from datetime import datetime

class DatabaseHandler:
    def __init__(self):
        self.conn = None
        self.cursor = None
        self.logger = logging.getLogger("Database")
        self.connect()

    def connect(self):
        try:
            conn_str = (
    'DRIVER={ODBC Driver 17 for SQL Server};'
    f'SERVER=hehe\\SQLEXPRESS;DATABASE=ParkSystem;'
    'Trusted_Connection=yes;'
)

            self.conn = pyodbc.connect(conn_str)
            self.cursor = self.conn.cursor()
            self.logger.info("Kết nối database thành công")
        except Exception as e:
            self.logger.error(f"Lỗi kết nối database: {e}")
            raise

    def check_login(self, username, password):
        try:
            sql = """
            SELECT a.id, a.username, a.role 
            FROM Accounts a
            WHERE a.username = ? AND a.password = ?
            """
            self.cursor.execute(sql, (username, password))
            result = self.cursor.fetchone()
            if result:
                return {'id': result[0], 'username': result[1], 'role': result[2]}
            return None
        except Exception as e:
            self.logger.error(f"Lỗi check_login: {e}")
            return None

    def log_vehicle_entry(self, uid, plate_number):
        try:
            # Kiểm tra thẻ RFID có hợp lệ
            sql_check = "SELECT id FROM Users WHERE uid = ?"
            self.cursor.execute(sql_check, (uid,))
            if not self.cursor.fetchone():
                self.logger.warning(f"Thẻ RFID không hợp lệ: {uid}")
                return False

            # Thêm log mới
            sql_insert = """
            INSERT INTO Logs (uid, plate_number, status)
            VALUES (?, ?, 'IN')
            """
            self.cursor.execute(sql_insert, (uid, plate_number))
            self.conn.commit()
            self.logger.info(f"Log xe vào: UID={uid}, Biển số={plate_number}")
            return True
        except Exception as e:
            self.logger.error(f"Lỗi log_vehicle_entry: {e}")
            self.conn.rollback()
            return False

    def log_vehicle_exit(self, uid):
        try:
            sql = """
            UPDATE Logs 
            SET time_out = GETDATE(), status = 'OUT'
            WHERE uid = ? AND status = 'IN'
            """
            self.cursor.execute(sql, (uid,))
            self.conn.commit()
            return self.cursor.rowcount > 0
        except Exception as e:
            self.logger.error(f"Lỗi log_vehicle_exit: {e}")
            self.conn.rollback()
            return False

    def get_vehicle_info(self, uid):
        try:
            sql = """
            SELECT u.name, l.plate_number, l.time_in
            FROM Users u
            LEFT JOIN Logs l ON u.uid = l.uid
            WHERE u.uid = ? AND l.status = 'IN'
            """
            self.cursor.execute(sql, (uid,))
            result = self.cursor.fetchone()
            if result:
                return {
                    'name': result[0],
                    'plate_number': result[1],
                    'time_in': result[2]
                }
            return None
        except Exception as e:
            self.logger.error(f"Lỗi get_vehicle_info: {e}")
            return None

    def close(self):
        if self.conn:
            self.conn.close()
            self.logger.info("Đã đóng kết nối database")