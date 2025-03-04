function showTab(tabId) {
    document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
    document.getElementById(tabId).classList.add('active');
}

function updateLog(logs) {
    const logDiv = document.getElementById('log');
    logDiv.innerHTML = logs.join('<br>');
    logDiv.scrollTop = logDiv.scrollHeight;
}

async function fetchGlpi() {
    const computerId = document.getElementById('glpi_id').value;
    const response = await fetch('/fetch_glpi', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ computer_id: computerId })
    });
    const data = await response.json();
    if (data.error) {
        alert(data.error);
    } else {
        document.getElementById('glpi_info').textContent = data.display_text;
    }
    updateLog(data.logs);
}

async function importSnipeIt() {
    const computerId = document.getElementById('glpi_id').value;
    const response = await fetch('/import_snipe_it', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ computer_id: computerId })
    });
    const data = await response.json();
    alert(data.message);
    updateLog(data.logs);
}

let full_category_list = [];

async function loadCategories() {
    const response = await fetch('/get_categories', { method: 'GET' });
    const data = await response.json();
    if (data.error) {
        alert(data.error);
        return;
    }
    full_category_list = data.categories;
    const input = document.getElementById('manual_category');
    input.value = ''; // Reset giá trị
    filterCategories('');
}

function filterCategories(typed) {
    const input = document.getElementById('manual_category');
    const list = document.getElementById('category-autocomplete-list');
    list.innerHTML = '';
    if (typed === '') {
        full_category_list.forEach(cat => {
            const div = document.createElement('div');
            div.textContent = cat;
            div.onclick = () => {
                input.value = cat;
                list.style.display = 'none';
            };
            list.appendChild(div);
        });
    } else {
        const filtered = full_category_list.filter(cat => cat.toLowerCase().includes(typed.toLowerCase()));
        filtered.forEach(cat => {
            const div = document.createElement('div');
            div.textContent = cat;
            div.onclick = () => {
                input.value = cat;
                list.style.display = 'none';
            };
            list.appendChild(div);
        });
    }
    list.style.display = filtered.length > 0 ? 'block' : 'none';
}

document.getElementById('manual_category').addEventListener('input', function(e) {
    filterCategories(e.target.value);
});

document.addEventListener('click', function(e) {
    const list = document.getElementById('category-autocomplete-list');
    if (!e.target.closest('.form-group')) {
        list.style.display = 'none';
    }
});

async function loadStatusLabels() {
    const response = await fetch('/get_status_labels', { method: 'GET' });
    const data = await response.json();
    const select = document.getElementById('manual_status');
    data.status_labels.forEach(status => {
        const option = document.createElement('option');
        option.value = status.split(' (ID: ')[1].slice(0, -1);  // Lấy ID
        option.textContent = status;
        select.appendChild(option);
    });
}

// Hàm giả lập để tải dữ liệu (tùy chỉnh theo API nếu cần)
function loadSerial() { alert("Chức năng nhập số seri tài sản chưa được triển khai!"); }
function loadModel() { alert("Chức năng lấy dữ liệu model chưa được triển khai!"); }
function loadManufacturer() { alert("Chức năng lấy dữ liệu nhà sản xuất chưa được triển khai!"); }
function loadStatus() { alert("Chức năng lấy dữ liệu trạng thái chưa được triển khai!"); }

let components = {
    itemharddisk: [],
    itemmemory: [],
    itemgraphic: [],
    itemprocessor: []
};

function addHd() {
    const name = document.getElementById('hd_name').value;
    const serial = document.getElementById('hd_serial').value;
    if (name || serial) {
        components.itemharddisk.push({ designation: name, serial: serial });
        document.getElementById('hd_list').textContent += `${name || 'Unknown'} (${serial || 'Không có'})\n`;
        document.getElementById('hd_name').value = '';
        document.getElementById('hd_serial').value = '';
    }
}

function addMem() {
    const designation = document.getElementById('mem_name').value;
    const size = document.getElementById('mem_size').value;
    const freq = document.getElementById('mem_freq').value;
    const serial = document.getElementById('mem_serial').value;
    if (designation || size || freq || serial) {
        components.itemmemory.push({ designation: designation, size: size, frequence: freq, serial: serial });
        document.getElementById('mem_list').textContent += `${designation} ${size}MB ${freq}MHz (${serial || 'Không có'})\n`;
        document.getElementById('mem_serial').value = '';
    }
}

function addGc() {
    const name = document.getElementById('gc_name').value;
    const serial = document.getElementById('gc_serial').value;
    if (name || serial) {
        components.itemgraphic.push({ designation: name, serial: serial });
        document.getElementById('gc_list').textContent += `${name || 'Unknown'} (${serial || 'Không có'})\n`;
        document.getElementById('gc_name').value = '';
        document.getElementById('gc_serial').value = '';
    }
}

function addProc() {
    const name = document.getElementById('proc_name').value;
    const serial = document.getElementById('proc_serial').value;
    if (name || serial) {
        components.itemprocessor.push({ designation: name, serial: serial });
        document.getElementById('proc_list').textContent += `${name || 'Unknown'} (${serial || 'Không có'})\n`;
        document.getElementById('proc_name').value = '';
        document.getElementById('proc_serial').value = '';
    }
}

async function displayManual() {
    const manualInfo = {
        name: document.getElementById('manual_name').value,
        serial: document.getElementById('manual_serial').value,
        computertypes_id: document.getElementById('manual_category').value,
        model: document.getElementById('manual_model').value,
        manufacturer: document.getElementById('manual_manufacturer').value,
        statuslabels_id: document.getElementById('manual_status').value,
        employee_number: document.getElementById('manual_employee_number').value,
        itemharddisk: components.itemharddisk,
        itemmemory: components.itemmemory,
        itemgraphic: components.itemgraphic,
        itemprocessor: components.itemprocessor
    };
    const response = await fetch('/display_manual', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(manualInfo)
    });
    const data = await response.json();
    document.getElementById('manual_info').textContent = data.info;
    updateLog(data.logs);
}

async function importManual() {
    const manualInfo = {
        name: document.getElementById('manual_name').value,
        serial: document.getElementById('manual_serial').value,
        computertypes_id: document.getElementById('manual_category').value,
        model: document.getElementById('manual_model').value,
        manufacturer: document.getElementById('manual_manufacturer').value,
        statuslabels_id: document.getElementById('manual_status').value,
        employee_number: document.getElementById('manual_employee_number').value,
        itemharddisk: components.itemharddisk,
        itemmemory: components.itemmemory,
        itemgraphic: components.itemgraphic,
        itemprocessor: components.itemprocessor
    };
    const response = await fetch('/import_manual', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(manualInfo)
    });
    const data = await response.json();
    alert(data.message);
    updateLog(data.logs);
    // Reset components
    components = { itemharddisk: [], itemmemory: [], itemgraphic: [], itemprocessor: [] };
    document.getElementById('hd_list').textContent = '';
    document.getElementById('mem_list').textContent = '';
    document.getElementById('gc_list').textContent = '';
    document.getElementById('proc_list').textContent = '';
    document.getElementById('manual_name').value = '';
    document.getElementById('manual_serial').value = '';
    document.getElementById('manual_model').value = '';
    document.getElementById('manual_manufacturer').value = '';
    document.getElementById('manual_employee_number').value = '';
    document.getElementById('manual_category').value = ''; // Reset Category
}

async function searchAsset() {
    const serialNumber = document.getElementById('search_input').value;
    const response = await fetch('/search_asset', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ serial_number: serialNumber })
    });
    const data = await response.json();
    if (data.error) {
        alert(data.error);
    } else {
        document.getElementById('search_info').textContent = data.display_text;
    }
    updateLog(data.logs);
}

function clearManual() {
    document.getElementById('manual_category').value = '';
    document.getElementById('manual_name').value = '';
    document.getElementById('manual_serial').value = '';
    document.getElementById('manual_status').value = '4';
    document.getElementById('manual_model').value = '';
    document.getElementById('manual_manufacturer').value = '';
    document.getElementById('manual_employee_number').value = '';
    components = { itemharddisk: [], itemmemory: [], itemgraphic: [], itemprocessor: [] };
    document.getElementById('hd_list').textContent = '';
    document.getElementById('mem_list').textContent = '';
    document.getElementById('gc_list').textContent = '';
    document.getElementById('proc_list').textContent = '';
    document.getElementById('manual_info').textContent = '';
}

window.onload = function() {
    loadCategories();
    loadStatusLabels();
    showTab('glpi');
};