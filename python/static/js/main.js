// Khởi tạo Socket.IO
const socket = io();

let currentSearchValue = ''; // Thêm biến để lưu từ khóa tìm kiếm hiện tại
let currentPage = 1;
let currentSearch = '';

function loadVehicleData(page = currentPage) {
    let url = `/get_vehicle_data?page=${page}`;
    if (currentSearch) {
        url += `&search=${encodeURIComponent(currentSearch)}`;
    }

    fetch(url)
        .then(response => response.json())
        .then(response => {
            const tableBody = document.querySelector('#vehicle-table tbody');
            tableBody.innerHTML = '';

            response.data.forEach((vehicle, index) => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${(page - 1) * 20 + index + 1}</td>
                    <td>${vehicle.plate_number || 'N/A'}</td>
                    <td>${vehicle.rfid || 'N/A'}</td>
                    <td>${formatDateTime(vehicle.time_in)}</td>
                    <td>${vehicle.status === 'IN' 
                        ? `<button onclick="handleManualOut('${vehicle.rfid}', '${vehicle.plate_number}')" 
                       class="manual-out-btn">Cho ra</button>`
                        : formatDateTime(vehicle.time_out)}</td>
                    <td data-status="${vehicle.status}">${vehicle.status}</td>
                `;
                tableBody.appendChild(row);
            });

            currentPage = response.current_page;
            updatePagination(response.current_page, response.total_pages);
        });
}

function updatePagination(currentPage, totalPages) {
    const pageNumbers = document.getElementById('page-numbers');
    const prevBtn = document.getElementById('prev-page');
    const nextBtn = document.getElementById('next-page');
    
    pageNumbers.innerHTML = '';
    prevBtn.disabled = currentPage === 1;
    nextBtn.disabled = currentPage === totalPages;

    function addPageButton(num) {
        const pageBtn = document.createElement('button');
        pageBtn.className = `page-number ${num === currentPage ? 'active' : ''}`;
        pageBtn.textContent = num;
        pageBtn.onclick = () => loadVehicleData(num);
        pageNumbers.appendChild(pageBtn);
    }

    function addEllipsis() {
        const span = document.createElement('span');
        span.className = 'ellipsis';
        span.textContent = '...';
        pageNumbers.appendChild(span);
    }

    // Always show first page
    addPageButton(1);

    if (totalPages <= 5) {
        // Show all pages if total is 5 or less
        for (let i = 2; i <= totalPages; i++) {
            addPageButton(i);
        }
    } else {
        if (currentPage <= 3) {
            // Near the start
            for (let i = 2; i <= 4; i++) {
                addPageButton(i);
            }
            addEllipsis();
            addPageButton(totalPages);
        } else if (currentPage >= totalPages - 2) {
            // Near the end
            addEllipsis();
            for (let i = totalPages - 3; i <= totalPages; i++) {
                addPageButton(i);
            }
        } else {
            // Middle - show current page and neighbors
            addEllipsis();
            for (let i = currentPage - 1; i <= currentPage + 1; i++) {
                addPageButton(i);
            }
            addEllipsis();
            addPageButton(totalPages);
        }
    }
}

// Add event listeners for prev/next buttons
document.getElementById('prev-page').addEventListener('click', () => {
    if (currentPage > 1) {
        loadVehicleData(--currentPage);
    }
});

document.getElementById('next-page').addEventListener('click', () => {
    currentPage++;
    loadVehicleData(currentPage);
});

// Add new function to update recent logs
function updateRecentLogs() {
    fetch('/get_recent_logs')
        .then(response => response.json())
        .then(data => {
            const recentLogsBody = document.querySelector('#recent-logs-table tbody');
            recentLogsBody.innerHTML = '';

            data.forEach(vehicle => {
                const row = document.createElement('tr');
                const time = vehicle.status === 'IN' ? vehicle.time_in : vehicle.time_out;
                
                row.innerHTML = `
                    <td>${vehicle.plate_number || 'N/A'}</td>
                    <td>${formatDateTime(time)}</td>
                    <td class="${vehicle.status === 'IN' ? 'status-in' : 'status-out'}">${vehicle.status}</td>
                `;
                recentLogsBody.appendChild(row);
            });
        });
}

function updateLatestVehicles() {
    fetch('/get_latest_vehicles')
        .then(response => response.json())
        .then(data => {
            const latestInInput = document.getElementById('latest-in');
            const latestOutInput = document.getElementById('latest-out');

            if (data.latest_in) {
                latestInInput.value = data.latest_in.plate_number;
            } else {
                latestInInput.value = 'N/A';
            }

            if (data.latest_out) {
                latestOutInput.value = data.latest_out.plate_number;
            } else {
                latestOutInput.value = 'N/A';
            }
        });
}

// Thêm hàm cập nhật trạng thái parking slots
function updateParkingSlots(slotsData) {
    // Cập nhật từng slot
    Object.keys(slotsData).forEach(slotId => {
        const slotElement = document.getElementById(slotId);
        const status = slotsData[slotId];
        
        if (slotElement) {
            if (status === 1) {
                // Có xe - thêm class occupied
                slotElement.classList.add('occupied');
            } else {
                // Trống - xóa class occupied
                slotElement.classList.remove('occupied');
            }
        }
    });
    
    // Cập nhật số xe hiện tại
    const occupiedCount = Object.values(slotsData).filter(status => status === 1).length;
    const carCountElement = document.getElementById('car-count');
    if (carCountElement) {
        carCountElement.value = occupiedCount;
    }
}

// Hàm load trạng thái parking slots từ server
function loadParkingSlots() {
    fetch('/get_parking_slots')
        .then(response => response.json())
        .then(slotsData => {
            updateParkingSlots(slotsData);
        })
        .catch(error => {
            console.error('Lỗi khi load parking slots:', error);
        });
}

// Add handler for manual exit
function handleManualOut(rfid, plateNumber) {
    if (confirm(`Xác nhận cho xe ${plateNumber} ra?`)) {
        fetch('/manual_vehicle_out', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                rfid: rfid,
                plate_number: plateNumber
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                loadVehicleData(currentPage);
                updateRecentLogs();
                alert('Đã cho xe ra thành công!');
            } else {
                alert('Có lỗi xảy ra: ' + data.message);
            }
        });
    }
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

socket.on('plate_update', function(data) {
    console.log('Received plate update:', data); // Debug log
    
    // Cập nhật biển số cho camera tương ứng
    const plateElement = document.getElementById(`plate-number-${data.camera_id}`);
    if (plateElement) {
        plateElement.textContent = data.plate_number || 'Không phát hiện';
        console.log(`Updated plate number for camera ${data.camera_id}:`, data.plate_number); // Debug log
    }
    
    // Cập nhật lại bảng và thông tin
    loadVehicleData(currentPage);
    updateRecentLogs();
    updateLatestVehicles();
});

// Thêm hàm để cập nhật trạng thái barrier
function updateBarrierStatus(status) {
    const barrierInBtn = document.getElementById('barrier-in-control');
    const barrierOutBtn = document.getElementById('barrier-out-control');
    
    if (barrierInBtn) {
        barrierInBtn.disabled = status === 'opening';
    }
    if (barrierOutBtn) {
        barrierOutBtn.disabled = status === 'opening';
    }
}

// Thêm socket listener cho cập nhật parking slots
socket.on('parking_slots_update', function(slotsData) {
    console.log('Nhận cập nhật parking slots:', slotsData);
    updateParkingSlots(slotsData);
});

// Thêm socket listener cho thông báo lỗi
socket.on('error', (data) => {
    alert(data.message);
});

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

    // Xử lý nút mở barrier vào
    const barrierInButton = document.getElementById('barrier-in-control');
    if (barrierInButton) {
        barrierInButton.addEventListener('click', function() {
            this.disabled = true;
            socket.emit('open_barrier_in');
            console.log('Sent open barrier in command'); // Debug log
            setTimeout(() => {
                this.disabled = false;
            }, 3000);
        });
    }

    // Xử lý nút mở barrier ra
    const barrierOutButton = document.getElementById('barrier-out-control');
    if (barrierOutButton) {
        barrierOutButton.addEventListener('click', function() {
            this.disabled = true;
            socket.emit('open_barrier_out');
            console.log('Sent open barrier out command'); // Debug log
            setTimeout(() => {
                this.disabled = false;
            }, 3000);
        });
    }

    // Thay thế cả 2 event listener cũ của search-btn và search-input bằng code mới
    const searchInput = document.getElementById('search-input');
    
    searchInput.addEventListener('input', function(e) {
        currentSearch = this.value.trim();
        currentPage = 1; // Reset to first page when searching
        loadVehicleData();
    });

    // Initial load of recent logs
    updateRecentLogs();
    
    // Update recent logs every 30 seconds
    setInterval(updateRecentLogs, 30000);

    // Initial update
    updateLatestVehicles();
    
    // Update every 30 seconds
    setInterval(updateLatestVehicles, 30000);

    // Load parking slots khi trang được tải
    loadParkingSlots();
});