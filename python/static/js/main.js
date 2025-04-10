document.addEventListener('DOMContentLoaded', function() {
    const plateNumberElement = document.getElementById('plate-number');
    const capturedFeedImg = document.querySelector('.camera-box:nth-child(2) img');
    
    // Kết nối Socket.IO
    const socket = io();
    
    // Xử lý khi kết nối thành công
    socket.on('connect', function() {
        console.log('Đã kết nối với server');
    });
    
    // Xử lý khi kết nối lỗi
    socket.on('connect_error', function(error) {
        console.error('Không thể kết nối với server:', error);
    });
    
    // Xử lý khi ngắt kết nối
    socket.on('disconnect', function() {
        console.log('Đã ngắt kết nối với server');
    });
    
    // Xử lý cập nhật biển số
    socket.on('plate_update', function(data) {
        console.log('Nhận được cập nhật biển số:', data);
        if (data.plate_number) {
            plateNumberElement.textContent = data.plate_number;
            capturedFeedImg.alt = "Biển số: " + data.plate_number;
        } else {
            plateNumberElement.textContent = "Không phát hiện";
            capturedFeedImg.alt = "Không phát hiện biển số";
        }
    });
});