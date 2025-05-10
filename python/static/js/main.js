// Khởi tạo Socket.IO
const socket = io();

let currentSearchValue = ''; // Thêm biến để lưu từ khóa tìm kiếm hiện tại

// Xử lý chuyển tab
document.addEventListener('DOMContentLoaded', function() {
    const tabs = document.querySelectorAll('.nav-btn');
    const sections = document.querySelectorAll('.content-section');

    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            // Xóa active class từ tất cả tabs và sections
            tabs.forEach(t => t.classList.remove('active'));
            sections.forEach(s => s.classList.remove('active'));

            // Thêm active class cho tab được chọn
            tab.classList.add('active');
            const targetId = tab.getAttribute('data-target');
            document.getElementById(targetId).classList.add('active');

            // Nếu chuyển sang tab table thì load dữ liệu
            if (targetId === 'table-content') {
                loadVehicleData();
            }
        });
    });

    // Hiển thị thời gian
    function updateTime() {
        const now = new Date();
        document.getElementById('current-time').textContent = now.toLocaleString('vi-VN');
    }
    setInterval(updateTime, 1000);
    updateTime();

    // Load dữ liệu bảng lần đầu
    loadVehicleData();

    // Thêm xử lý sự kiện cho nút mở barrier
    const barrierButton = document.getElementById('barrier-control');
    if (barrierButton) {
        barrierButton.addEventListener('click', function() {
            // Vô hiệu hóa nút trong 3 giây
            this.disabled = true;
            
            // Gửi lệnh mở barrier
            socket.emit('open_barrier');
            
            // Kích hoạt lại nút sau 3 giây
            setTimeout(() => {
                this.disabled = false;
            }, 3000);
        });
    }

    // Thay thế cả 2 event listener cũ của search-btn và search-input bằng code mới
    const searchInput = document.getElementById('search-input');
    
    searchInput.addEventListener('input', function(e) {
        currentSearchValue = this.value.trim().toLowerCase();
        const tableRows = document.querySelectorAll('#vehicle-table tbody tr');
        
        tableRows.forEach(row => {
            const plateNumber = row.querySelector('td:nth-child(2)').textContent.toLowerCase();
            if (plateNumber.includes(currentSearchValue)) {
                row.style.display = '';
            } else {
                row.style.display = 'none';
            }
        });
    });
});

// Sửa hàm load dữ liệu xe từ server
function loadVehicleData() {
    fetch('/get_vehicle_data')
        .then(response => response.json())
        .then(data => {
            const tableBody = document.querySelector('#vehicle-table tbody');
            tableBody.innerHTML = ''; // Xóa dữ liệu cũ

            data.forEach((vehicle, index) => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${index + 1}</td>
                    <td>${vehicle.plate_number || 'N/A'}</td>
                    <td>${formatDateTime(vehicle.time_in)}</td>
                    <td>${vehicle.time_out ? formatDateTime(vehicle.time_out) : 'N/A'}</td>
                    <td>${vehicle.status}</td>
                `;
                
                // Ẩn row nếu không khớp với từ khóa tìm kiếm
                if (currentSearchValue && !vehicle.plate_number?.toLowerCase().includes(currentSearchValue.toLowerCase())) {
                    row.style.display = 'none';
                }
                
                tableBody.appendChild(row);
            });
        })
        .catch(error => console.error('Error:', error));
}

// Hàm format datetime
function formatDateTime(dateString) {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleString('vi-VN');
}

// Cập nhật dữ liệu mỗi 5 giây
setInterval(loadVehicleData, 5000);

// Socket.IO event handlers
socket.on('connect', () => {
    console.log('Connected to server');
});

socket.on('plate_update', (data) => {
    const plateElement = document.getElementById('plate-number');
    if (plateElement) {
        plateElement.textContent = data.plate_number || 'Không phát hiện';
    }
    // Cập nhật lại bảng khi có biển số mới
    loadVehicleData();
});