document.addEventListener('DOMContentLoaded', function() {
    const capturedImage = document.querySelector('.camera-box img:last-child');
    const plateNumber = document.getElementById('plate-number');
    
    // Hàm cập nhật biển số
    function updatePlateNumber(number) {
        plateNumber.textContent = number || 'Không phát hiện';
    }
    
    // Kiểm tra biển số mỗi khi ảnh được cập nhật
    capturedImage.addEventListener('load', function() {
        // TODO: Thêm API endpoint để lấy biển số
        fetch('/get_plate_number')
            .then(response => response.json())
            .then(data => {
                if (data.plate_number) {
                    updatePlateNumber(data.plate_number);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                updatePlateNumber(null);
            });
    });
    
    // Xử lý lỗi nếu ảnh không load được
    capturedImage.addEventListener('error', function() {
        console.error("Image failed to load");
    });
});