from flask import Flask, Response, render_template
import cv2
import numpy as np
import threading
import time
from camera_system import CameraSystem
from plate_regconition import LicensePlateDetector

app = Flask(__name__)
system = None
detected_result = None
frame_size = None  # Biến lưu kích thước frame camera

def generate_frames():
    global frame_size
    while True:
        ret, frame = system.get_frame()
        if not ret:
            continue
            
        # Lưu kích thước frame gốc để tính toán kích thước biển số
        frame_size = frame.shape[:2]
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

def process_captured_image():
    global detected_result
    if system.last_capture is not None and detected_result is None:
        license_plate, annotated_image, success = plate_recognition.detect_plate(system.last_capture)
        
        if success:
            # Tính toán kích thước mới cho phần biển số (1/4 kích thước camera)
            target_height = frame_size[0] // 4
            target_width = frame_size[1] // 4
            
            # Lấy vùng biển số từ ảnh gốc
            for plate in plate_recognition.detector(system.last_capture).pandas().xyxy[0].values.tolist():
                x1, y1, x2, y2 = map(int, plate[:4])
                plate_region = system.last_capture[y1:y2, x1:x2]
                
                # Resize vùng biển số về kích thước mong muốn
                plate_region = cv2.resize(plate_region, (target_width, target_height))
                
                # Thêm footer hiển thị biển số
                footer = np.zeros((30, target_width, 3), dtype=np.uint8)
                cv2.putText(footer, f"Plate: {license_plate}", (5, 20),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                
                # Ghép ảnh và footer
                final_image = np.vstack((plate_region, footer))
                break  # Chỉ lấy biển số đầu tiên
        else:
            # Tạo ảnh thông báo lỗi với kích thước 1/4
            target_height = frame_size[0] // 4
            target_width = frame_size[1] // 4
            final_image = np.zeros((target_height + 30, target_width, 3), dtype=np.uint8)
            cv2.putText(final_image, "No plate detected!", (5, target_height//2),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)

        ret, buffer = cv2.imencode('.jpg', final_image)
        detected_result = buffer.tobytes()

def generate_capture():
    while True:
        if system.last_capture is not None and system.is_processing:
            # Reset current result before new detection
            system.set_current_result(None)
            
            # Nhận dạng biển số
            license_plate, annotated_image, detected = plate_recognition.detect_plate(system.last_capture)
            
            if detected:
                # Lấy vùng biển số từ ảnh gốc
                for plate in plate_recognition.detector(system.last_capture).pandas().xyxy[0].values.tolist():
                    x1, y1, x2, y2 = map(int, plate[:4])
                    plate_region = system.last_capture[y1:y2, x1:x2].copy()
                    
                    # Tính toán kích thước mới (1/4 frame gốc)
                    target_height = system.last_capture.shape[0] // 4
                    target_width = system.last_capture.shape[1] // 4
                    
                    # Resize vùng biển số
                    plate_region = cv2.resize(plate_region, (target_width, target_height))
                    
                    # Set new result
                    system.set_current_result({
                        'image': plate_region,
                        'plate_number': license_plate,
                        'detected': True,
                        'timestamp': time.time()  # Add timestamp
                    })
                    break
            else:
                # Create error image
                target_height = system.last_capture.shape[0] // 4
                target_width = system.last_capture.shape[1] // 4
                error_image = np.zeros((target_height, target_width, 3), dtype=np.uint8)
                system.set_current_result({
                    'image': error_image,
                    'plate_number': None,
                    'detected': False,
                    'timestamp': time.time()  # Add timestamp
                })
            
            system.is_processing = False

        # Display current result if available
        if system.current_result is not None:
            ret, buffer = cv2.imencode('.jpg', system.current_result['image'])
            if ret:
                frame = buffer.tobytes()
                yield (b'--frame\r\n'
                      b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), 
                   mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/captured_feed')
def captured_feed():
    return Response(generate_capture(),
                   mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/get_plate_number')
def get_plate_number():
    if system and system.current_result and system.new_detection:
        try:
            if (system.current_result.get('detected', False) and 
                system.current_result.get('plate_number')):
                system.new_detection = False  # Reset flag after getting number
                return system.current_result['plate_number']
        except Exception as e:
            print(f"Error in get_plate_number: {e}")
    return ""

def read_serial():
    while True:
        response = system.serial.read_response()
        if response == "CARD_DETECTED" and not system.is_processing:  # Chỉ xử lý khi không có quá trình đang chạy
            system.card_detected = True
            system.capture_image()
            # Gửi phản hồi cho ESP32
            system.serial.send_command("CAPTURING")

if __name__ == '__main__':
    try:
        system = CameraSystem()
        plate_recognition = LicensePlateDetector()
        # Start serial thread
        serial_thread = threading.Thread(target=read_serial)
        serial_thread.daemon = True
        serial_thread.start()
        
        # Run Flask app
        app.run(host='0.0.0.0', port=5000)
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'system' in locals():
            system.cleanup()