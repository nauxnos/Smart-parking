import cv2
import logging
import numpy as np

class CameraSystem:

    def __init__(self):
        self.camera = cv2.VideoCapture(0)
        if not self.camera.isOpened():
            raise RuntimeError("Không thể mở camera")
        self.logger = logging.getLogger("Camera")
        self.last_capture = None
        self.last_crop = None  # Thêm biến lưu ảnh đã cắt
        # Thêm kích thước cố định cho ảnh
        self.CAPTURE_WIDTH = 320   # Thay đổi từ 640 xuống 320
        self.CAPTURE_HEIGHT = 240  # Thay đổi từ 480 xuống 240
        self.blank_image = np.ones((self.CAPTURE_HEIGHT, self.CAPTURE_WIDTH, 3), 
                              dtype=np.uint8) * 255  # Tạo ảnh trắng

    def resize_image(self, image):
        """Resize ảnh về kích thước cố định"""
        return cv2.resize(image, (self.CAPTURE_WIDTH, self.CAPTURE_HEIGHT))

    def capture_image(self):
        """Chụp và lưu vào bộ nhớ"""
        ret, frame = self.camera.read()
        if ret:
            # Resize ảnh về kích thước cố định
            frame = self.resize_image(frame)
            self.last_capture = frame.copy()
            self.logger.info(f"Đã chụp ảnh {self.CAPTURE_WIDTH}x{self.CAPTURE_HEIGHT}")
            return True
        return False

    def generate_frames(self):
        """Stream camera"""
        while True:
            ret, frame = self.camera.read()
            if not ret:
                continue
            # Resize frame stream
            frame = self.resize_image(frame)
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    def generate_capture(self):
        """Stream ảnh đã chụp"""
        while True:
            if self.last_crop is not None:
                # Resize ảnh đã cắt
                resized_crop = self.resize_image(self.last_crop)
                ret, buffer = cv2.imencode('.jpg', resized_crop)
                frame = buffer.tobytes()
            else:
                # Trả về ảnh trắng nếu không có biển số
                ret, buffer = cv2.imencode('.jpg', self.blank_image)
                frame = buffer.tobytes()
                
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    def cleanup(self):
        if self.camera.isOpened():
            self.camera.release()