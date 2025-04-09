from flask import Flask, Response, render_template, jsonify
import threading
import logging
from camera_system import CameraSystem
from serial_handler import SerialHandler
from plate_regconize import LicensePlateDetector

# Thiết lập logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

app = Flask(__name__)
camera = None
serial = None
plate_recognize = None

@app.route('/')
def index():
    return render_template('index.html')

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
    if hasattr(camera, 'last_plate_number'):
        return jsonify({'plate_number': camera.last_plate_number})

def handle_serial():
    """Xử lý dữ liệu từ Serial"""
    while True:
        if serial:
            response = serial.read_response()
            if response == "CARD_DETECTED":
                logging.info("Phát hiện thẻ RFID - Chụp ảnh")
                if camera.capture_image():
                    license_plate, crop_img, ret = findPlate(camera.last_capture)  # Gọi findPlate ở đây
                    if ret and crop_img is not None:
                        camera.last_crop = crop_img  # Lưu ảnh đã cắt
                        camera.last_plate_number = license_plate  # Lưu biển số
                        logging.info(f"Đã cập nhật biển số: {license_plate}")
                    else:
                        camera.last_crop = None  # Reset về None để hiển thị ảnh trắng
                        camera.last_plate_number = None
                        logging.warning("Không phát hiện biển số - Hiển thị ảnh trắng")

def findPlate(img):
    license_plate, crop_img, ret = plate_recognize.detect_plate(img)
    if ret:
        logging.info(f"Biển số phát hiện: {license_plate}")
    else:
        logging.warning("Không phát hiện biển số")
    return license_plate, crop_img, ret

def main():
    global camera, serial, plate_recognize
    try:
        camera = CameraSystem()
        logging.info("Đã khởi tạo camera")
        serial = SerialHandler()
        if not serial.connect():
            raise RuntimeError("Không thể kết nối Serial")
        logging.info("Đã khởi tạo Serial")
        plate_recognize = LicensePlateDetector()
        logging.info("Đã khởi tạo nhận diện biển số")
        serial_thread = threading.Thread(target=handle_serial)
        serial_thread.daemon = True
        serial_thread.start()
        
        app.run(host='0.0.0.0', port=5000)
        
    except Exception as e:
        logging.error(f"Lỗi: {e}")
    finally:
        if camera:
            camera.cleanup()
        if serial:
            serial.disconnect()

if __name__ == '__main__':
    main()