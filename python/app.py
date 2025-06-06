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

# Thêm biến lưu trạng thái các slot
parking_slots = {
    "slot1": 0,  # 0: trống, 1: có xe
    "slot2": 0,
    "slot3": 0
}

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
            return render_template('login.html', error='Tài khoản hoặc mật khẩu không đúng')
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
        page = request.args.get('page', 1, type=int)
        search = request.args.get('search', None)
        data = db_handler.get_vehicle_logs(page=page, search_text=search)
        return jsonify(data)
    return jsonify({'data': [], 'total_pages': 1, 'current_page': 1, 'total_records': 0})

@app.route('/search_vehicle')
def search_vehicle():
    if db_handler:
        plate_number = request.args.get('plate_number', '')
        data = db_handler.search_vehicle_logs(plate_number)
        return jsonify(data)
    return jsonify([])

@app.route('/manual_vehicle_out', methods=['POST'])
def manual_vehicle_out():
    if not request.is_json:
        return jsonify({'success': False, 'message': 'Invalid request'})
        
    data = request.json
    rfid = data.get('rfid')
    plate_number = data.get('plate_number')
    
    if not rfid or not plate_number:
        return jsonify({'success': False, 'message': 'Missing data'})
    
    # Gọi hàm xử lý xe ra từ DatabaseHandler
    result = db_handler.save_vehicle_log(rfid, plate_number, 'OUT')
    
    if result:
        return jsonify({'success': True})
    return jsonify({'success': False, 'message': 'Database error'})

@app.route('/get_recent_logs')
def get_recent_logs():
    """Lấy 5 bản ghi gần nhất"""
    if db_handler:
        data = db_handler.get_vehicle_logs(page=1, per_page=5)
        return jsonify(data.get('data', []))
    return jsonify([])

@app.route('/get_latest_vehicles')
def get_latest_vehicles():
    """Lấy xe vào và ra gần nhất"""
    if db_handler:
        latest_in = db_handler.get_latest_vehicle('IN')
        latest_out = db_handler.get_latest_vehicle('OUT')
        return jsonify({
            'latest_in': latest_in,
            'latest_out': latest_out
        })
    return jsonify({'latest_in': None, 'latest_out': None})

# Thêm route để lấy trạng thái parking slots
@app.route('/get_parking_slots')
def get_parking_slots():
    """Lấy trạng thái hiện tại của các slot đỗ xe"""
    return jsonify(parking_slots)

@socketio.on('connect')
def handle_connect():
    logging.info('Client kết nối thành công')
    # Gửi biển số hiện tại (nếu có) cho client mới kết nối
    if camera and hasattr(camera, 'last_plate_number') and camera.last_plate_number:
        emit('plate_update', {'plate_number': camera.last_plate_number})
    
    # Gửi trạng thái parking slots hiện tại cho client mới
    emit('parking_slots_update', parking_slots)

@socketio.on('open_barrier')
def handle_open_barrier():
    """Xử lý yêu cầu mở barrier từ web"""
    if serial:
        serial.write_command("OPEN_BARRIER")
        logging.info("Đã gửi lệnh mở barrier")
        return {'status': 'success'}
    return {'status': 'error', 'message': 'Serial không khả dụng'}

@socketio.on('open_barrier_in')
def handle_open_barrier_in():
    """Xử lý yêu cầu mở barrier vào từ web"""
    if serial:
        serial.open_barrier_in()
        logging.info("Đã gửi lệnh mở barrier vào")
        return {'status': 'success'}
    return {'status': 'error', 'message': 'Serial không khả dụng'}

@socketio.on('open_barrier_out')
def handle_open_barrier_out():
    """Xử lý yêu cầu mở barrier ra từ web"""
    if serial:
        serial.open_barrier_out()
        logging.info("Đã gửi lệnh mở barrier ra")
        return {'status': 'success'}
    return {'status': 'error', 'message': 'Serial không khả dụng'}

def update_parking_slot(slot_id, status):
    """Cập nhật trạng thái slot và gửi tới client"""
    global parking_slots
    if slot_id in parking_slots:
        parking_slots[slot_id] = status
        logging.info(f"Cập nhật {slot_id}: {'Có xe' if status == 1 else 'Trống'}")
        # Gửi cập nhật tới tất cả client
        socketio.emit('parking_slots_update', parking_slots)

def handle_serial():
    """Xử lý dữ liệu từ Serial"""
    while True:
        try:
            if serial:
                response = serial.read_response()
                if response:
                    rfid = None
                    direction = None
                    
                    # Xử lý cập nhật trạng thái parking slot
                    if "SLOT" in response and ":" in response:
                        try:
                            # Ví dụ: "SLOT1:1" hoặc "SLOT2:0"
                            slot_info = response.strip()
                            slot_name, slot_status = slot_info.split(":")
                            slot_number = slot_name.lower()  # slot1, slot2, slot3
                            status = int(slot_status)
                            
                            # Cập nhật trạng thái slot
                            update_parking_slot(slot_number, status)
                            continue  # Tiếp tục vòng lặp, không xử lý RFID
                            
                        except (ValueError, IndexError) as e:
                            logging.warning(f"Lỗi parse slot data: {response} - {e}")
                    
                    # Xử lý RFID vào
                    elif "ENTRY" in response:
                        direction = "IN"
                        rfid = response.split("ENTRY - Card UID: ")[1].strip()
                        logging.info(f"Phát hiện thẻ RFID vào: {rfid}")
                    
                    # Xử lý RFID ra
                    elif "EXIT" in response:
                        direction = "OUT"
                        rfid = response.split("EXIT - Card UID: ")[1].strip()
                        logging.info(f"Phát hiện thẻ RFID ra: {rfid}")
                    
                    if rfid and direction:
                        if camera.capture_image():
                            license_plate, crop_img, ret = findPlate(camera.last_capture)
                            
                            if ret and crop_img is not None:
                                camera.last_crop = crop_img
                                camera.last_plate_number = license_plate
                                
                                # Xử lý xe qua DatabaseHandler với trạng thái cụ thể
                                result = db_handler.process_vehicle(rfid, license_plate, direction)
                                
                                if result['success']:
                                    if direction == 'IN':
                                        serial.open_barrier_in()
                                    else:
                                        serial.open_barrier_out()
                                        
                                    socketio.emit('plate_update', {
                                        'plate_number': license_plate, 
                                        'status': direction
                                    })
                                else:
                                    error_msg = "Thẻ không hợp lệ cho hướng này" if direction == 'OUT' else result['message']
                                    logging.warning(error_msg)
                                    socketio.emit('error', {'message': error_msg})
                            else:
                                camera.last_crop = None
                                camera.last_plate_number = None
                                socketio.emit('plate_update', {'plate_number': None})
                                logging.warning("Không phát hiện biển số")
                            
            time.sleep(0.1)
        except Exception as e:
            logging.error(f"Lỗi trong quá trình xử lý serial: {e}")
            time.sleep(1)

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