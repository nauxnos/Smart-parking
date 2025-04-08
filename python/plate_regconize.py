import cv2
import torch
import plate_regconition.function.utils_rotate as utils_rotate
import plate_regconition.function.helper as helper

class LicensePlateDetector:
    def __init__(self, detector_path='plate_regconition/model/LP_detector.pt', ocr_path='plate_regconition/model/LP_ocr.pt'):
        """
        Khởi tạo detector với các model được train sẵn
        """
        self.detector = torch.hub.load('plate_regconition/yolov5', 'custom', 
                                     path=detector_path, 
                                     force_reload=True, 
                                     source='local')
        
        self.recognition = torch.hub.load('plate_regconition/yolov5', 'custom', 
                                        path=ocr_path, 
                                        force_reload=True, 
                                        source='local')
        self.recognition.conf = 0.60

    def detect_plate(self, image):
        """
        Phát hiện và nhận dạng biển số từ ảnh
        Args:
            image: Có thể là đường dẫn ảnh hoặc numpy array
        Returns:
            tuple: (license_plate_text, annotated_image, success)
        """
        # Kiểm tra input
        if isinstance(image, str):
            img = cv2.imread(image)
        else:
            img = image.copy()
            
        if img is None:
            return None, None, False

        # Phát hiện vùng chứa biển số
        plates = self.detector(img, size=640)
        list_plates = plates.pandas().xyxy[0].values.tolist()

        if len(list_plates) == 0:
            return None, img, False

        # Xử lý biển số được phát hiện
        for plate in list_plates:
            x = int(plate[0])  # xmin
            y = int(plate[1])  # ymin
            w = int(plate[2] - plate[0])  # xmax - xmin
            h = int(plate[3] - plate[1])  # ymax - ymin

            # Cắt vùng biển số
            crop_img = img[y:y+h, x:x+w]
            
            # Vẽ khung biển số
            cv2.rectangle(img, (x, y), (x+w, y+h), (0, 0, 255), 2)

            # Nhận dạng ký tự
            license_plate = self._recognize_characters(crop_img)
            
            if license_plate != "unknown":
                # Vẽ text lên ảnh
                cv2.putText(img, license_plate, (x, y-10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.9, (36,255,12), 2)
                return license_plate, img, True

        return None, img, False

    def _recognize_characters(self, crop_img):
        """
        Nhận dạng ký tự trên biển số đã được cắt
        """
        for cc in range(0, 2):
            for ct in range(0, 2):
                # Xoay ảnh và nhận dạng
                rotated_img = utils_rotate.deskew(crop_img, cc, ct)
                license_plate = helper.read_plate(self.recognition, rotated_img)
                
                if license_plate != "unknown":
                    return license_plate
        return "unknown"