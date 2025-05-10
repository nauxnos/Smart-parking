from flask import Flask, Response, render_template, jsonify, redirect, session, url_for, request
from flask_socketio import SocketIO, emit
import threading
import logging
import time
from camera_system import CameraSystem
from serial_handler import SerialHandler
from plate_regconize import LicensePlateDetector
from database_handler import DatabaseHandler

# Thiết lập logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")  # Cho phép truy cập từ các nguồn khác nếu cần
app.secret_key = 'secret'

camera = None
serial = None
plate_recognize = None
db_handler = None  # Thêm biến database handler

@app.route('/')
def home():
    if 'username' in session:
        return render_template('admin/dashboard.html')
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == 'admin' and password == 'admin':
            session['username'] = username
            return redirect(url_for('home'))
        else:
            return "Invalid credentials", 401
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/video_feed')
def video_feed():
    return Response(camera.generate_frames(),
                   mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/captured_feed')
def captured_feed():
    return Response(camera.generate_capture(),
                   mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/get_plate_number')
def get_plate_number():
    if camera and hasattr(camera, 'last_plate_number'):
        return jsonify({'plate_number': camera.last_plate_number})
    return jsonify({'plate_number': None})

@app.route('/get_vehicle_data')
def get_vehicle_data():
    if db_handler:
        data = db_handler.get_vehicle_logs()
        return jsonify(data)
    return jsonify([])

@app.route('/search_vehicle')
def search_vehicle():
    if db_handler:
        plate_number = request.args.get('plate_number', '')
        data = db_handler.search_vehicle_logs(plate_number)
        return jsonify(data)
    return jsonify([])

@socketio.on('connect')
def handle_connect():
    logging.info('Client kết nối thành công')
    # Gửi biển số hiện tại (nếu có) cho client mới kết nối
    if camera and hasattr(camera, 'last_plate_number') and camera.last_plate_number:
        emit('plate_update', {'plate_number': camera.last_plate_number})

@socketio.on('open_barrier')
def handle_open_barrier():
    """Xử lý yêu cầu mở barrier từ web"""
    if serial:
        serial.write_command("OPEN_BARRIER")
        logging.info("Đã gửi lệnh mở barrier")
        return {'status': 'success'}
    return {'status': 'error', 'message': 'Serial không khả dụng'}

def handle_serial():
    """Xử lý dữ liệu từ Serial"""
    while True:
        try:
            if serial:
                # response = serial.read_response()
                # if response and "CARD_DETECTED:" in response:
                #     rfid = response.split(":")[1].strip()
                #     logging.info(f"Phát hiện thẻ RFID: {rfid}")
                response = serial.read_response()
                if response and "Card detected" in response:
                    logging.info("Phát hiện thẻ RFID - Chụp ảnh")
                    if camera.capture_image():
                        license_plate, crop_img, ret = findPlate(camera.last_capture)
                        rfid = response.split("UID:")[1].strip()
                        logging.info(f"Phát hiện thẻ RFID: {rfid}")
                        if ret and crop_img is not None:
                            camera.last_crop = crop_img
                            camera.last_plate_number = license_plate
                            db_handler.save_vehicle_log(rfid, license_plate)
                            # Phát sóng thông báo về biển số đến tất cả client
                            socketio.emit('plate_update', {'plate_number': license_plate})
                            logging.info(f"Đã cập nhật biển số: {license_plate}")
                            handle_open_barrier()
                        else:
                            camera.last_crop = None
                            camera.last_plate_number = None
                            # Gửi thông báo không phát hiện
                            socketio.emit('plate_update', {'plate_number': None})
                            logging.warning("Không phát hiện biển số - Hiển thị ảnh trắng")
            time.sleep(0.1)  # Ngăn CPU hoạt động 100%
        except Exception as e:
            logging.error(f"Lỗi trong quá trình xử lý serial: {e}")
            time.sleep(1)  # Đợi một chút trước khi thử lại

def findPlate(img):
    license_plate, crop_img, ret = plate_recognize.detect_plate(img)
    if ret:
        logging.info(f"Biển số phát hiện: {license_plate}")
    else:
        logging.warning("Không phát hiện biển số")
    return license_plate, crop_img, ret

def main():
    global camera, serial, plate_recognize, db_handler
    try:
        camera = CameraSystem()
        logging.info("Đã khởi tạo camera")
        serial = SerialHandler()
        if not serial.connect():
            raise RuntimeError("Không thể kết nối Serial")
        logging.info("Đã khởi tạo Serial")
        plate_recognize = LicensePlateDetector()
        logging.info("Đã khởi tạo nhận diện biển số")
        db_handler = DatabaseHandler()
        logging.info("Đã khởi tạo database handler")
        
        # Khởi động luồng xử lý serial
        serial_thread = threading.Thread(target=handle_serial)
        serial_thread.daemon = True
        serial_thread.start()
        
        # Chạy ứng dụng Flask với SocketIO
        socketio.run(app, host='0.0.0.0', port=5000, debug=True, use_reloader=False)
        
    except Exception as e:
        logging.error(f"Lỗi: {e}")
    finally:
        if camera:
            camera.cleanup()
        if serial:
            serial.disconnect()
        if db_handler:
            db_handler.close()

if __name__ == '__main__':
    main()