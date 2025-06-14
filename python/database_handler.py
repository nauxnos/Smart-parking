import pyodbc
from datetime import datetime
import logging
import pytz

class DatabaseHandler:
    def __init__(self):
        self.server = 'hehe\\SQLEXPRESS'
        self.database = 'ParkingSystem'
        self.connection = None
        self.timezone = pytz.timezone('Asia/Ho_Chi_Minh')

    def get_connection(self):
        """Tạo kết nối đến SQL Server"""
        if not self.connection:
            try:
                self.connection = pyodbc.connect(
                    'DRIVER={ODBC Driver 17 for SQL Server};'
                    f'SERVER={self.server};DATABASE={self.database};'
                    'Trusted_Connection=yes;'
                    'MARS_Connection=yes;'
                )
                logging.info("Đã kết nối database thành công")
            except Exception as e:
                logging.error(f"Lỗi kết nối database: {e}")
                return None
        return self.connection

    def get_current_time(self):
        return datetime.now(tz=pytz.timezone('Asia/Ho_Chi_Minh')) - self.timezone.utcoffset(datetime.now())

    def save_vehicle_log(self, rfid, plate_number, status='IN'):
        """Lưu thông tin xe vào/ra"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            current_time = self.get_current_time()
            
            if status == 'IN':
                # Luôn tạo bản ghi mới khi xe vào
                cursor.execute("""
                    INSERT INTO Logs (rfid, plate_number, time_in, status)
                    VALUES (?, ?, ?, 'IN')
                """, (rfid, plate_number, current_time))
            else:
                # Xe ra - cập nhật bản ghi IN gần nhất
                cursor.execute("""
                    UPDATE Logs 
                    SET time_out = ?, status = 'OUT'
                    WHERE id = (
                        SELECT TOP 1 id 
                        FROM Logs 
                        WHERE rfid = ? AND plate_number = ? AND status = 'IN'
                        ORDER BY time_in DESC
                    )
                """, (current_time, rfid, plate_number))
                    
            conn.commit()
            logging.info(f"Đã lưu log: RFID={rfid}, Biển số={plate_number}, Status={status}")
            return True
            
        except Exception as e:
            logging.error(f"Lỗi khi lưu vào database: {e}")
            return False

    def get_vehicle_logs(self, page=1, per_page=20, search_text=None):
        """Lấy danh sách các xe từ database với phân trang và tìm kiếm"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Base query without LIKE condition
            base_query = "FROM Logs"
            params = []
            
            # Add search condition if search_text is provided
            if search_text:
                base_query += " WHERE plate_number LIKE ?"
                params.append(f'%{search_text}%')
                
            # Lấy tổng số bản ghi
            cursor.execute(f"SELECT COUNT(*) {base_query}", params)
            total_records = cursor.fetchone()[0]
            total_pages = (total_records + per_page - 1) // per_page
            
            # Lấy dữ liệu theo trang
            query = f"""
                SELECT 
                    rfid,
                    plate_number,
                    time_in,
                    time_out,
                    status
                {base_query}
                ORDER BY time_in DESC
                OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
            """
            
            params.extend([(page - 1) * per_page, per_page])
            cursor.execute(query, params)
            
            columns = [column[0] for column in cursor.description]
            results = []
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))
                
            return {
                'data': results,
                'total_pages': total_pages,
                'current_page': page,
                'total_records': total_records,
                'search_text': search_text
            }
            
        except Exception as e:
            logging.error(f"Lỗi khi lấy dữ liệu: {e}")
            return {'data': [], 'total_pages': 1, 'current_page': 1, 'total_records': 0}

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

    def check_vehicle_entry(self, rfid, plate_number):
        """Kiểm tra xe vào có khớp với dữ liệu không"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Kiểm tra xe có trong hệ thống và đang ở trạng thái IN không
            cursor.execute("""
                SELECT id FROM Logs 
                WHERE rfid = ? AND plate_number = ? AND status = 'IN'
            """, (rfid, plate_number))
            
            result = cursor.fetchone()
            return result is not None
            
        except Exception as e:
            logging.error(f"Lỗi khi kiểm tra xe: {e}")
            return False

    def process_vehicle(self, rfid, license_plate, direction):
        """Xử lý xe vào/ra"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            if direction == 'IN':
                # Kiểm tra RFID đã được sử dụng cho xe khác chưa
                cursor.execute("""
                    SELECT plate_number 
                    FROM Logs 
                    WHERE rfid = ? AND status = 'IN'
                """, (rfid,))
                existing_rfid = cursor.fetchone()
                
                if existing_rfid:
                    return {
                        'status': 'ERROR',
                        'success': False,
                        'message': f'Thẻ RFID này đang được sử dụng cho xe {existing_rfid[0]}'
                    }
                
                # Kiểm tra xe đã có trong bãi chưa
                cursor.execute("""
                    SELECT rfid 
                    FROM Logs 
                    WHERE plate_number = ? AND status = 'IN'
                """, (license_plate,))
                existing_vehicle = cursor.fetchone()
                
                if existing_vehicle:
                    return {
                        'status': 'ERROR',
                        'success': False,
                        'message': 'Xe này đang ở trong bãi'
                    }
                    
                # Cho phép xe vào nếu cả RFID và biển số đều chưa được sử dụng
                self.save_vehicle_log(rfid, license_plate, 'IN')
                return {'status': 'IN', 'success': True}
                
            else:
                # Xe ra - kiểm tra khớp RFID và biển số
                cursor.execute("""
                    SELECT id 
                    FROM Logs 
                    WHERE rfid = ? AND plate_number = ? AND status = 'IN'
                """, (rfid, license_plate))
                
                if cursor.fetchone():
                    self.save_vehicle_log(rfid, license_plate, 'OUT')
                    return {'status': 'OUT', 'success': True}
                else:
                    return {
                        'status': 'ERROR',
                        'success': False,
                        'message': 'Thẻ RFID không khớp với biển số xe vào'
                    }
                
        except Exception as e:
            logging.error(f"Lỗi khi xử lý xe: {e}")
            return {'status': 'ERROR', 'success': False, 'message': str(e)}

    def close(self):
        """Đóng kết nối database"""
        if self.connection:
            self.connection.close()
            self.connection = None
    
    def get_latest_vehicle(self, status):
        """Lấy xe vào hoặc ra gần nhất"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            query = """
                SELECT TOP 1
                    plate_number
                FROM Logs 
                WHERE status = ?
                ORDER BY 
                    CASE 
                        WHEN status = 'IN' THEN time_in
                        ELSE time_out
                    END DESC
            """
            cursor.execute(query, (status,))
            result = cursor.fetchone()
            
            if result:
                return {
                    'plate_number': result[0]
                }
            return None
            
        except Exception as e:
            logging.error(f"Lỗi khi lấy xe {status} gần nhất: {e}")
            return None

    def get_parking_stats(self):
        """Lấy thống kê bãi đỗ xe"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Tổng số xe đang trong bãi
            cursor.execute("SELECT COUNT(*) FROM Logs WHERE status = 'IN'")
            current_vehicles = cursor.fetchone()[0]
            
            # Số lượt xe trong ngày
            cursor.execute("""
                SELECT 
                    COUNT(CASE WHEN status = 'IN' THEN 1 END) as entries,
                    COUNT(CASE WHEN status = 'OUT' THEN 1 END) as exits
                FROM Logs 
                WHERE CAST(time_in AS DATE) = CAST(GETDATE() AS DATE)
            """)
            daily_stats = cursor.fetchone()
            
            return {
                'current_vehicles': current_vehicles,
                'total_slots': 3,
                'available_slots': 3 - current_vehicles,
                'daily_entries': daily_stats[0],
                'daily_exits': daily_stats[1]
            }
        except Exception as e:
            logging.error(f"Lỗi khi lấy thống kê: {e}")
            return {}

    def is_admin(self, username):
        """Kiểm tra user có phải admin không"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT role FROM Users WHERE username = ?", (username,))
            result = cursor.fetchone()
            return result and result[0] == 'admin'
        except Exception as e:
            logging.error(f"Lỗi kiểm tra admin: {e}")
            return False
    
    def verify_user(self, username, password):
        """Xác thực đăng nhập user"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, username, role 
                FROM Users 
                WHERE username = ? AND password = ?
            """, (username, password))
            
            result = cursor.fetchone()
            if result:
                return {
                    'id': result[0],
                    'username': result[1],
                    'role': result[2]
                }
            return None
            
        except Exception as e:
            logging.error(f"Lỗi xác thực user: {e}")
            return None