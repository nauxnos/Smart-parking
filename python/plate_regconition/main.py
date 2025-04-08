from test import LicensePlateDetector
import cv2

def main():
    # Khởi tạo detector
    detector = LicensePlateDetector()
    
    # Đường dẫn ảnh cần nhận dạng
    image_path = "test_image/3.jpg"
    
    # Nhận dạng biển số
    license_plate, annotated_image, success = detector.detect_plate(image_path)
    
    if success:
        print(f"Detected license plate: {license_plate}")
        cv2.imwrite('output.jpg', annotated_image)
    else:
        print("No license plate detected or recognition failed")

if __name__ == "__main__":
    main()