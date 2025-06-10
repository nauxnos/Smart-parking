import cv2
import logging
import numpy as np

class CameraSystem:

    def __init__(self):
        # Khởi tạo 2 camera
        self.cameras = {
            'in': cv2.VideoCapture(0),  # Camera vào
            'out': cv2.VideoCapture(1)  # Camera ra
        }
        
        # Kiểm tra kết nối camera
        for camera_id, camera in self.cameras.items():
            if not camera.isOpened():
                raise RuntimeError(f"Không thể mở camera {camera_id}")
                
        self.logger = logging.getLogger("Camera")
        self.last_captures = {
            'in': None,
            'out': None
        }
        self.last_crops = {
            'in': None,
            'out': None
        }
        self.last_plate_numbers = {
            'in': None,
            'out': None
        }
        
        # Thêm kích thước cố định cho ảnh
        self.CAPTURE_WIDTH = 320
        self.CAPTURE_HEIGHT = 240
        self.blank_image = np.ones((self.CAPTURE_HEIGHT, self.CAPTURE_WIDTH, 3), 
                              dtype=np.uint8) * 255

    def resize_image(self, image):
        """Resize ảnh về kích thước cố định"""
        return cv2.resize(image, (self.CAPTURE_WIDTH, self.CAPTURE_HEIGHT))

    def capture_image(self, camera_id):
        """Chụp và lưu vào bộ nhớ cho camera cụ thể"""
        camera = self.cameras.get(camera_id)
        if not camera:
            return False
            
        ret, frame = camera.read()
        if ret:
            frame = self.resize_image(frame)
            self.last_captures[camera_id] = frame.copy()
            self.logger.info(f"Đã chụp ảnh {camera_id} {self.CAPTURE_WIDTH}x{self.CAPTURE_HEIGHT}")
            return True
        return False

    def generate_frames(self, camera_id):
        """Stream camera cụ thể"""
        camera = self.cameras.get(camera_id)
        if not camera:
            return
            
        while True:
            ret, frame = camera.read()
            if not ret:
                continue
            frame = self.resize_image(frame)
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    def generate_capture(self, camera_id):
        """Stream ảnh đã chụp cho camera cụ thể"""
        while True:
            if self.last_crops[camera_id] is not None:
                resized_crop = self.resize_image(self.last_crops[camera_id])
                ret, buffer = cv2.imencode('.jpg', resized_crop)
                frame = buffer.tobytes()
            else:
                ret, buffer = cv2.imencode('.jpg', self.blank_image)
                frame = buffer.tobytes()
                
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    def cleanup(self):
        """Đóng tất cả camera"""
        for camera in self.cameras.values():
            if camera.isOpened():
                camera.release()