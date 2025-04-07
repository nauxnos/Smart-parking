from flask import Flask, Response, render_template
import cv2
import threading
from datetime import datetime
from serial_handler import SerialHandler
import numpy as np

app = Flask(__name__)

class CameraSystem:
    def __init__(self):
        # Khởi tạo camera
        self.camera = cv2.VideoCapture(0)
        if not self.camera.isOpened():
            raise RuntimeError("Không thể mở camera")

        # Khởi tạo Serial Handler
        self.serial = SerialHandler()
        if not self.serial.connect():
            self.camera.release()
            raise RuntimeError("Không thể kết nối Serial")

        self.card_detected = False
        self.last_capture = None  # Lưu ảnh trong bộ nhớ

    def capture_image(self):
        ret, frame = self.camera.read()
        if ret:
            self.last_capture = frame
            return True
        return False

    def cleanup(self):
        self.camera.release()
        self.serial.disconnect()

def generate_frames():
    while True:
        ret, frame = system.camera.read()  # Sử dụng read() thay vì get_frame()
        if not ret:
            continue
            
        # Convert frame to jpg
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        
        # Return frame in multipart format
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

def generate_capture():
    while True:
        if system.last_capture is not None:
            ret, buffer = cv2.imencode('.jpg', system.last_capture)
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

def read_serial():
    while True:
        response = system.serial.read_response()
        if response == "CARD_DETECTED":
            system.card_detected = True
            system.capture_image()
            # Gửi phản hồi cho ESP32
            system.serial.send_command("CAPTURING")

if __name__ == '__main__':
    try:
        system = CameraSystem()
        
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