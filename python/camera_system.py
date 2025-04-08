import cv2
from serial_handler import SerialHandler

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
        self.detected_result = None
        self.is_processing = False  # Thêm flag để kiểm soát việc xử lý
        self.current_result = None  # Thêm biến để lưu kết quả hiện tại
        self.new_detection = False  # Add flag for new detections

    def capture_image(self):
        ret, frame = self.camera.read()
        if ret:
            self.last_capture = frame.copy()  # Tạo bản copy của frame
            self.is_processing = True  # Set flag khi bắt đầu xử lý
            self.current_result = None  # Reset kết quả cũ
            return True
        return False

    def get_frame(self):
        ret, frame = self.camera.read()
        if ret:
            return ret, frame
        return False, None

    def set_current_result(self, result):
        self.current_result = result
        self.new_detection = True  # Set flag when new result is set

    def cleanup(self):
        self.camera.release()
        self.serial.disconnect()