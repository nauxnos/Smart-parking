let currentPage = 1;
const socket = io();

document.addEventListener('DOMContentLoaded', function() {
    // Navigation functionality
    const navBtns = document.querySelectorAll('.nav-btn');
    const contentSections = document.querySelectorAll('.content-section');

    navBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            // Remove active class from all buttons and sections
            navBtns.forEach(b => b.classList.remove('active'));
            contentSections.forEach(s => s.classList.remove('active'));
            
            // Add active class to clicked button and its content
            btn.classList.add('active');
            const tabId = btn.getAttribute('data-tab');
            document.getElementById(`${tabId}-content`).classList.add('active');
        });
    });

    // Initialize table data and pagination
    loadVehicleData(currentPage);

    // Add search functionality
    const searchInput = document.getElementById('search-input');
    if (searchInput) {
        searchInput.addEventListener('input', debounce(() => {
            currentPage = 1;
            loadVehicleData(currentPage);
        }, 300));
    }

    // Add pagination event listeners
    const prevBtn = document.getElementById('prev-page');
    const nextBtn = document.getElementById('next-page');

    if (prevBtn) {
        prevBtn.addEventListener('click', () => {
            if (currentPage > 1) {
                currentPage--;
                loadVehicleData(currentPage);
            }
        });
    }

    if (nextBtn) {
        nextBtn.addEventListener('click', () => {
            currentPage++;
            loadVehicleData(currentPage);
        });
    }

    // Initialize slots and get initial status
    initializeSlots();
    getInitialSlotStatus();
    
    // Update stats grid as well
    updateStatsGrid();
    
    // Load parking slots data periodically (same as admin)
    loadParkingSlots();
    setInterval(loadParkingSlots, 5000); // Update every 5 seconds like admin
});

// Function to initialize slots with proper styling
function initializeSlots() {
    const slots = document.querySelectorAll('.slot');
    slots.forEach(slot => {
        const slotStatus = slot.querySelector('.slot-status');
        if (slotStatus) {
            // Set default styling for slot status indicator
            slotStatus.style.width = '12px';
            slotStatus.style.height = '12px';
            slotStatus.style.borderRadius = '50%';
            slotStatus.style.position = 'absolute';
            slotStatus.style.top = '10px';
            slotStatus.style.right = '10px';
            slotStatus.style.backgroundColor = '#2ecc71'; // Default green (free)
            slotStatus.style.transition = 'background-color 0.3s ease';
        }
        
        const carIcon = slot.querySelector('.car-icon');
        if (carIcon) {
            carIcon.style.fontSize = '48px';
            carIcon.style.opacity = '0.2'; // Default low opacity
            carIcon.style.transition = 'opacity 0.3s ease';
        }
        
        // Make sure slot has proper styling
        slot.style.position = 'relative';
        slot.style.width = '120px';
        slot.style.height = '160px';
        slot.style.border = '2px solid #ddd';
        slot.style.borderRadius = '8px';
        slot.style.display = 'flex';
        slot.style.flexDirection = 'column';
        slot.style.alignItems = 'center';
        slot.style.justifyContent = 'center';
        slot.style.transition = 'all 0.3s ease';
        slot.style.backgroundColor = 'white';
    });
}

// Function to load parking slots (same as admin)
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

// Function to update parking slots (matching admin functionality)
function updateParkingSlots(slotsData) {
    console.log('Cập nhật parking slots:', slotsData);
    
    // Cập nhật từng slot giống như admin
    Object.keys(slotsData).forEach(slotId => {
        const slotElement = document.getElementById(`slot${slotId}`);
        const status = slotsData[slotId];
        
        if (slotElement) {
            const carIcon = slotElement.querySelector('.car-icon');
            const slotStatus = slotElement.querySelector('.slot-status');
            
            if (status === 1) {
                // Có xe - thêm class occupied (giống admin)
                slotElement.classList.add('occupied');
                slotElement.classList.remove('free');
                slotElement.style.borderColor = '#e74c3c';
                slotElement.style.backgroundColor = 'rgba(231, 76, 60, 0.1)';
                
                if (carIcon) carIcon.style.opacity = '1';
                if (slotStatus) slotStatus.style.backgroundColor = '#e74c3c'; // Red for occupied
            } else {
                // Trống - xóa class occupied (giống admin)
                slotElement.classList.remove('occupied');
                slotElement.classList.add('free');
                slotElement.style.borderColor = '#ddd';
                slotElement.style.backgroundColor = 'white';
                
                if (carIcon) carIcon.style.opacity = '0.2';
                if (slotStatus) slotStatus.style.backgroundColor = '#2ecc71'; // Green for free
            }
        }
    });
    
    // Cập nhật số xe hiện tại (giống admin)
    const occupiedCount = Object.values(slotsData).filter(status => status === 1).length;
    
    // Update stats if elements exist
    const currentVehiclesElement = document.querySelector('.stat-item p');
    if (currentVehiclesElement) {
        const totalSlots = Object.keys(slotsData).length;
        currentVehiclesElement.textContent = `${occupiedCount}/${totalSlots}`;
    }
    
    // Update available slots
    const availableSlotsElement = document.querySelectorAll('.stat-item p')[1];
    if (availableSlotsElement) {
        const totalSlots = Object.keys(slotsData).length;
        availableSlotsElement.textContent = totalSlots - occupiedCount;
    }
    
    // Also update the slots grid in stats tab
    updateSlotsGrid(slotsData);
}

// Function to load vehicle data
function loadVehicleData(page) {
    const searchText = document.getElementById('search-input')?.value || '';
    let url = `/get_vehicle_data?page=${page}`;
    if (searchText) {
        url += `&search=${encodeURIComponent(searchText)}`;
    }

    fetch(url)
        .then(response => response.json())
        .then(data => {
            updateTable(data.data);
            updatePagination(data.current_page, data.total_pages);
        })
        .catch(error => console.error('Error loading data:', error));
}

// Function to update table content
function updateTable(data) {
    const tableBody = document.querySelector('#vehicle-table tbody');
    if (!tableBody) return;

    tableBody.innerHTML = '';
    data.forEach((vehicle, index) => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${(currentPage - 1) * 20 + index + 1}</td>
            <td>${vehicle.plate_number || 'N/A'}</td>
            <td>${vehicle.rfid || 'N/A'}</td>
            <td>${formatDateTime(vehicle.time_in)}</td>
            <td>${vehicle.time_out ? formatDateTime(vehicle.time_out) : 'N/A'}</td>
            <td data-status="${vehicle.status}">${vehicle.status}</td>
        `;
        tableBody.appendChild(row);
    });
}

// Function to update pagination
function updatePagination(current, total) {
    const pageNumbers = document.getElementById('page-numbers');
    const prevBtn = document.getElementById('prev-page');
    const nextBtn = document.getElementById('next-page');
    
    if (!pageNumbers || !prevBtn || !nextBtn) return;

    // Update prev/next buttons
    prevBtn.disabled = current === 1;
    nextBtn.disabled = current === total;

    pageNumbers.innerHTML = '';
    
    // Calculate start and end page numbers
    let startPage = Math.max(1, current - 2);
    let endPage = Math.min(total, startPage + 4);
    
    // Adjust start if we're near the end
    if (endPage - startPage < 4) {
        startPage = Math.max(1, endPage - 4);
    }

    // Add first page if needed
    if (startPage > 1) {
        const firstButton = document.createElement('button');
        firstButton.className = 'page-number';
        firstButton.textContent = 1;
        firstButton.onclick = () => {
            currentPage = 1;
            loadVehicleData(1);
        };
        pageNumbers.appendChild(firstButton);
        
        if (startPage > 2) {
            const ellipsis = document.createElement('span');
            ellipsis.className = 'ellipsis';
            ellipsis.textContent = '...';
            pageNumbers.appendChild(ellipsis);
        }
    }

    // Add page numbers
    for (let i = startPage; i <= endPage; i++) {
        const button = document.createElement('button');
        button.className = `page-number${i === current ? ' active' : ''}`;
        button.textContent = i;
        button.onclick = () => {
            currentPage = i;
            loadVehicleData(i);
        };
        pageNumbers.appendChild(button);
    }

    // Add last page if needed
    if (endPage < total) {
        if (endPage < total - 1) {
            const ellipsis = document.createElement('span');
            ellipsis.className = 'ellipsis';
            ellipsis.textContent = '...';
            pageNumbers.appendChild(ellipsis);
        }
        
        const lastButton = document.createElement('button');
        lastButton.className = 'page-number';
        lastButton.textContent = total;
        lastButton.onclick = () => {
            currentPage = total;
            loadVehicleData(total);
        };
        pageNumbers.appendChild(lastButton);
    }
}

// Helper function to format date
function formatDateTime(dateStr) {
    if (!dateStr) return 'N/A';
    const date = new Date(dateStr);
    return date.toLocaleString('vi-VN');
}

// Debounce function for search
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Socket event listeners
socket.on('connect', function() {
    console.log('Socket connected successfully');
});

socket.on('disconnect', function() {
    console.log('Socket disconnected');
});

// Add socket listener for parking slots update (same as admin)
socket.on('parking_slots_update', function(slotsData) {
    console.log('Nhận cập nhật parking slots:', slotsData);
    updateParkingSlots(slotsData);
});

socket.on('slot_update', function(data) {
    console.log('Received slot update:', data);
    updateParkingSlots(data);
    updateStatsGrid(); // Also update stats when slots change
});

// New function to update slots grid in stats tab
function updateSlotsGrid(data) {
    const slotsGrid = document.getElementById('slots-grid');
    if (!slotsGrid) return;
    
    // Clear existing content
    slotsGrid.innerHTML = '';
    
    // Create slot status indicators
    for (let i = 1; i <= 3; i++) {
        const slotDiv = document.createElement('div');
        slotDiv.className = 'slot-indicator';
        slotDiv.style.cssText = `
            display: inline-block;
            margin: 10px;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
            min-width: 100px;
            font-weight: bold;
        `;
        
        const isOccupied = data[i] === 1; // Match admin logic: 1 = occupied, 0 = free
        slotDiv.style.backgroundColor = isOccupied ? '#ffebee' : '#e8f5e8';
        slotDiv.style.color = isOccupied ? '#c62828' : '#2e7d32';
        slotDiv.style.border = `2px solid ${isOccupied ? '#c62828' : '#2e7d32'}`;
        
        slotDiv.innerHTML = `
            <div style="font-size: 24px; margin-bottom: 5px;">
                ${isOccupied ? '🚗' : '🅿️'}
            </div>
            <div>Vị trí ${i}</div>
            <div style="font-size: 12px; margin-top: 5px;">
                ${isOccupied ? 'Có xe' : 'Trống'}
            </div>
        `;
        
        slotsGrid.appendChild(slotDiv);
    }
}

// Function to get initial slot status
function getInitialSlotStatus() {
    console.log('Getting initial slot status...');
    fetch('/get_parking_slots')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Initial slot status received:', data);
            updateParkingSlots(data);
        })
        .catch(error => {
            console.error('Error getting slot status:', error);
            // Set default status if API fails
            const defaultStatus = {1: 0, 2: 0, 3: 0}; // All slots free (0 = free, 1 = occupied)
            updateParkingSlots(defaultStatus);
        });
}

// Function to update stats grid
function updateStatsGrid() {
    // This function can be enhanced to fetch real-time stats
    // For now, it's a placeholder for future implementation
    console.log('Stats grid update triggered');
}