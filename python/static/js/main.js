document.addEventListener('DOMContentLoaded', function() {
    const plateNumberElement = document.getElementById('plate-number');
    const capturedFeedImg = document.querySelector('.camera-box:nth-child(2) img');
    
    // Kết nối Socket.IO
    const socket = io();
    
    // Xử lý khi kết nối thành công
    socket.on('connect', () => {
        console.log('Connected to server');
    });
    
    // Xử lý khi ngắt kết nối
    socket.on('disconnect', function() {
        console.log('Đã ngắt kết nối với server');
    });
    
    // Xử lý cập nhật biển số
    socket.on('plate_update', (data) => {
        console.log('Nhận được cập nhật biển số:', data);
        const plateElement = document.getElementById('plate-number');
        if (plateElement) {
            plateElement.textContent = data.plate_number || 'Không phát hiện';
        }
        if (data.plate_number) {
            capturedFeedImg.alt = "Biển số: " + data.plate_number;
        } else {
            capturedFeedImg.alt = "Không phát hiện biển số";
        }
    });
});