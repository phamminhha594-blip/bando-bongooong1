from flask import Flask, render_template_string, request, redirect, url_for, session
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "congan_bongooong_secret_key" # Khóa bảo mật phiên đăng nhập Admin
DB_NAME = "diem_luudong.db"

# Khởi tạo cơ sở dữ liệu SQLite tự động
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS points (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            name TEXT NOT NULL,
            address TEXT NOT NULL,
            time TEXT NOT NULL,
            lat REAL NOT NULL,
            lng REAL NOT NULL,
            status TEXT NOT NULL,
            crowd TEXT NOT NULL,
            notes TEXT NOT NULL,
            phone TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# 1. TRANG CHỦ (Giao diện chính cho Người dân)
@app.route('/')
def index():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT id, category, name, address, time, lat, lng, status, crowd, notes, phone FROM points')
    rows = cursor.fetchall()
    conn.close()

    points = []
    for r in rows:
        points.append({
            "id": r[0], "category": r[1], "name": r[2], "address": r[3],
            "time": r[4], "lat": r[5], "lng": r[6], "status": r[7],
            "crowd": r[8], "notes": r[9], "phone": r[10]
        })

    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Cổng Thông Tin Bản Đồ Số - Công An & UBND Xã Bờ Ngoong</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
        <style>
            body { margin: 0; padding: 0; font-family: Arial, sans-serif; background: #f4f6f9; }
            #map { width: 100%; height: 100vh; z-index: 1; }
            
            /* Welcome Modal Splash */
            #welcomeModal {
                position: fixed; top: 0; left: 0; width: 100%; height: 100%;
                background: rgba(0,0,0,0.7); z-index: 9999; display: flex;
                justify-content: center; align-items: center; padding: 15px; box-sizing: border-box;
            }
            .modal-content {
                background: white; width: 100%; max-width: 480px; padding: 25px;
                border-radius: 12px; box-shadow: 0 5px 20px rgba(0,0,0,0.3); text-align: center;
                animation: fadeIn 0.3s ease;
            }
            .modal-content h2 { color: #b30000; margin-top: 0; font-size: 18px; text-transform: uppercase; }
            .modal-content p { color: #555; font-size: 14px; margin-bottom: 20px; }
            .choice-btn {
                display: block; width: 100%; background: #f8f9fa; border: 1px solid #ccc;
                padding: 12px; margin-bottom: 10px; border-radius: 8px; text-align: left;
                font-weight: bold; color: #333; cursor: pointer; text-decoration: none; font-size: 14px;
                transition: 0.2s;
            }
            .choice-btn:hover { background: #e2e6ea; border-color: #0275d8; color: #0275d8; }

            /* Top Header Floating */
            .header-box {
                position: absolute; top: 15px; left: 60px; z-index: 1000;
                background: white; padding: 10px 15px; border-radius: 8px;
                box-shadow: 0 4px 10px rgba(0,0,0,0.3); max-width: 320px;
            }
            .header-box h2 { margin: 0 0 3px 0; font-size: 14px; color: #b30000; }
            .header-box p { margin: 0; font-size: 11px; color: #555; }

            /* Control Buttons Floating */
            .floating-controls {
                position: absolute; top: 15px; right: 15px; z-index: 1000;
                display: flex; flex-direction: column; gap: 8px;
            }
            .ctrl-btn {
                background: #0275d8; color: white; padding: 10px 14px;
                border-radius: 6px; text-decoration: none; font-weight: bold; font-size: 13px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.3); border: none; cursor: pointer; text-align: center;
            }
            .ctrl-btn.admin { background: #343a40; }
            .ctrl-btn:hover { opacity: 0.9; }

            /* Filter Bar Thôn */
            .filter-bar {
                position: absolute; bottom: 30px; left: 50%; transform: translateX(-50%);
                z-index: 1000; background: white; padding: 8px 15px; border-radius: 20px;
                box-shadow: 0 4px 15px rgba(0,0,0,0.3); display: flex; gap: 8px; overflow-x: auto; max-width: 90%;
            }
            .filter-chip {
                background: #e9ecef; border: none; padding: 6px 12px; border-radius: 15px;
                font-size: 12px; font-weight: bold; cursor: pointer; white-space: nowrap;
            }
            .filter-chip.active, .filter-chip:hover { background: #b30000; color: white; }

            /* Alert Banner */
            .alert-banner {
                position: absolute; top: 90px; left: 60px; right: 20px; z-index: 1000;
                background: #fff3cd; color: #856404; padding: 8px 12px; border-radius: 6px;
                font-size: 12px; border: 1px solid #ffeeba; box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                display: flex; justify-content: space-between; align-items: center; max-width: 400px;
            }
        </style>
    </head>
    <body>

        <!-- POPUP CHÀO MỪNG & LỰA CHỌN -->
        <div id="welcomeModal">
            <div class="modal-content">
                <h2>🛡️ CÔNG AN XÃ & UBND XÃ BỜ NGOONG</h2>
                <p>Hệ thống bản đồ số chính thức hỗ trợ nhân dân tra cứu thủ tục hành chính, đăng ký xe và lịch thu nhận lưu động.</p>
                <div style="text-align: left; font-size: 12px; font-weight: bold; margin-bottom: 8px; color: #444;">Bạn cần hỗ trợ việc gì hôm nay?</div>
                
                <a href="#" onclick="closeModal()" class="choice-btn">🗺️ <b>Xem toàn bộ bản đồ & tất cả các điểm</b></a>
                <a href="#" onclick="focusCategory('UBND Xã')" class="choice-btn">🏛️ <b>Đến Trụ sở UBND Xã</b> (TTHC chung, Hộ tịch...)</a>
                <a href="#" onclick="focusCategory('Công an Xã')" class="choice-btn">🛡️ <b>Đến Trụ sở Công an Xã</b> (Đăng ký xe, CCCD cố định...)</a>
                <a href="#" onclick="findNearest()" class="choice-btn">📍 <b>Tìm điểm thu nhận lưu động gần bạn nhất</b></a>
            </div>
        </div>

        <div class="header-box">
            <h2>🏛️ XÃ BỜ NGOONG, GIA LAI</h2>
            <p>Bản đồ Hành chính & Lưu động VNeID</p>
        </div>

        <div class="floating-controls">
            <button onclick="findNearest()" class="ctrl-btn">📍 Điểm gần bạn nhất</button>
            <a href="/admin" class="ctrl-btn admin">⚙️ Quản trị (Admin)</a>
        </div>

        <div class="alert-banner">
            <span>📢 <b>Thông báo:</b> Bà con khi đi làm thủ tục nhớ mang theo CCCD gắn chip và điện thoại cá nhân.</span>
        </div>

        <div id="map"></div>

        <div class="filter-bar">
            <button class="filter-chip active" onclick="filterPoints('all', this)">Tất cả</button>
            <button class="filter-chip" onclick="filterPoints('UBND Xã', this)">🏛️ UBND Xã</button>
            <button class="filter-chip" onclick="filterPoints('Công an Xã', this)">🛡️ Trụ sở Công an</button>
            <button class="filter-chip" onclick="filterPoints('Lưu động', this)">📍 Điểm Lưu động</button>
        </div>

        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
        <script>
            var map = L.map('map').setView([13.905, 108.015], 13);

            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                maxZoom: 19,
                attribution: '© OpenStreetMap - Công an xã Bờ Ngoong'
            }).addTo(map);

            var points = {{ points | tojson | safe }};
            var markers = [];

            function renderMarkers(filter = 'all') {
                markers.forEach(m => map.removeLayer(m));
                markers = [];

                points.forEach(function(p) {
                    if (filter !== 'all' && p.category !== filter) return;

                    var color = '#0275d8';
                    if (p.category === 'UBND Xã') color = '#28a745';
                    if (p.category === 'Công an Xã') color = '#d9534f';

                    var marker = L.marker([p.lat, p.lng]).addTo(map);
                    
                    var popupContent = `
                        <div style="min-width: 200px; font-family: Arial;">
                            <span style="background: ${color}; color: white; padding: 2px 6px; border-radius: 4px; font-size: 11px; font-weight: bold;">${p.category}</span>
                            <b style="font-size: 14px; color: #222; display: block; margin-top: 5px;">${p.name}</b>
                            <p style="margin: 4px 0; font-size: 12px; color: #555;">📍 ${p.address}</p>
                            <hr style="border:0; border-top:1px solid #eee; margin:6px 0;">
                            ⏰ <b>Thời gian:</b> ${p.time}<br>
                            📌 <b>Trạng thái:</b> <span style="color: green;">${p.status}</span><br>
                            👥 <b>Mức độ đông đúc:</b> <b>${p.crowd}</b><br>
                            📋 <b>Mang theo:</b> ${p.notes}<br>
                            📞 <b>Hotline:</b> <a href="tel:${p.phone}">${p.phone}</a><br><br>
                            <a href="https://www.google.com/maps/search/?api=1&query=${p.lat},${p.lng}" target="_blank" style="display: block; text-align: center; background: #0275d8; color: white; padding: 7px; border-radius: 4px; text-decoration: none; font-weight: bold; font-size: 12px;">🚗 Mở bản đồ chỉ đường</a>
                        </div>
                    `;
                    marker.bindPopup(popupContent);
                    markers.push({marker: marker, category: p.category, lat: p.lat, lng: p.lng});
                });
            }

            renderMarkers('all');

            function closeModal() {
                document.getElementById('welcomeModal').style.display = 'none';
            }

            function focusCategory(cat) {
                closeModal();
                renderMarkers(cat);
                // Highlight chip
                document.querySelectorAll('.filter-chip').forEach(c => {
                    if(c.textContent.includes(cat)) c.click();
                });
            }

            function filterPoints(cat, btn) {
                document.querySelectorAll('.filter-chip').forEach(c => c.classList.remove('active'));
                btn.classList.add('active');
                renderMarkers(cat);
            }

            function findNearest() {
                closeModal();
                if (!navigator.geolocation) {
                    alert("Trình duyệt của bạn không hỗ trợ định vị GPS.");
                    return;
                }
                navigator.geolocation.getCurrentPosition(function(position) {
                    var userLat = position.coords.latitude;
                    var userLng = position.coords.longitude;

                    var userMarker = L.marker([userLat, userLng], {
                        icon: L.divIcon({className: 'user-pos', html: '🔵', iconSize: [20, 20]})
                    }).addTo(map);
                    userMarker.bindPopup("<b>Vị trí hiện tại của bạn</b>").openPopup();

                    let nearest = null;
                    let minDistance = Infinity;

                    points.forEach(p => {
                        let dist = Math.sqrt(Math.pow(p.lat - userLat, 2) + Math.pow(p.lng - userLng, 2));
                        if (dist < minDistance) {
                            minDistance = dist;
                            nearest = p;
                        }
                    });

                    if (nearest) {
                        map.setView([nearest.lat, nearest.lng], 15);
                        alert("📍 Điểm gần bạn nhất là: " + nearest.name + " (" + nearest.address + ")");
                    }
                }, function() {
                    alert("Không thể lấy được vị trí của bạn. Vui lòng bật định vị GPS trên điện thoại.");
                });
            }
        </script>
    </body>
    </html>
    """
    return render_template_string(html_template, points=points)


# 2. TRANG ĐĂNG NHẬP ADMIN
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    error = None
    if request.method == 'POST':
        password = request.form['password']
        if password == "congan2026": # Mật khẩu quản trị của cơ quan
            session['logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            error = "Mật khẩu không chính xác!"
            
    login_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8"><title>Đăng nhập Quản trị - Công an xã Bờ Ngoong</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body { font-family: Arial; background: #f4f6f9; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
            .login-box { background: white; padding: 30px; border-radius: 8px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); width: 100%; max-width: 350px; text-align: center; }
            h2 { color: #b30000; margin-top: 0; font-size: 18px; }
            input { width: 100%; padding: 10px; margin: 10px 0; box-sizing: border-box; border: 1px solid #ccc; border-radius: 4px; }
            button { width: 100%; background: #0275d8; color: white; border: none; padding: 10px; border-radius: 4px; font-weight: bold; cursor: pointer; }
            .error { color: red; font-size: 12px; margin-bottom: 10px; }
        </style>
    </head>
    <body>
        <div class="login-box">
            <h2>🛡️ QUẢN TRỊ HỆ THỐNG</h2>
            <p style="font-size: 12px; color: #666;">Công an xã Bờ Ngoong</p>
            {% if error %}<div class="error">{{ error }}</div>{% endif %}
            <form method="POST">
                <input type="password" name="password" placeholder="Nhập mật khẩu quản trị..." required>
                <button type="submit">Đăng nhập</button>
            </form>
            <br><a href="/" style="font-size: 12px; color: #0275d8; text-decoration: none;">⬅ Quay lại trang chủ bản đồ</a>
        </div>
    </body>
    </html>
    """
    return render_template_string(login_template, error=error)


# 3. TRANG QUẢN TRỊ CHÍNH (Thêm, Sửa, Xóa điểm)
@app.route('/admin', methods=['GET', 'POST'])
def admin_dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('admin_login'))

    if request.method == 'POST':
        category = request.form['category']
        name = request.form['name']
        address = request.form['address']
        time = request.form['time']
        lat = float(request.form['lat'])
        lng = float(request.form['lng'])
        status = request.form['status']
        crowd = request.form['crowd']
        notes = request.form['notes']
        phone = request.form['phone']

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO points (category, name, address, time, lat, lng, status, crowd, notes, phone)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (category, name, address, time, lat, lng, status, crowd, notes, phone))
        conn.commit()
        conn.close()
        return redirect(url_for('admin_dashboard'))

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT id, category, name, address, time, lat, lng, status, crowd, notes, phone FROM points')
    rows = cursor.fetchall()
    conn.close()

    admin_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8"><title>Quản lý Điểm - Công an xã Bờ Ngoong</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body { font-family: Arial; background: #f4f6f9; margin: 0; padding: 20px; }
            .container { max-width: 950px; margin: auto; background: white; padding: 25px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            h2 { color: #b30000; margin-top: 0; }
            .form-group { margin-bottom: 12px; }
            label { display: block; margin-bottom: 4px; font-weight: bold; font-size: 13px; }
            input, select, textarea { width: 100%; padding: 8px; box-sizing: border-box; border: 1px solid #ccc; border-radius: 4px; font-size: 13px; }
            button { background: #0275d8; color: white; border: none; padding: 10px 15px; border-radius: 4px; cursor: pointer; font-weight: bold; }
            table { width: 100%; border-collapse: collapse; margin-top: 20px; font-size: 12px; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            th { background: #f2f2f2; }
            .delete-btn { background: #d9534f; color: white; padding: 4px 8px; text-decoration: none; border-radius: 3px; font-size: 11px; }
            .top-nav { display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="top-nav">
                <a href="/" style="text-decoration: none; color: #0275d8; font-weight: bold;">⬅ Xem Bản Đồ Ngoài Trang Chủ</a>
                <a href="/admin/logout" style="text-decoration: none; color: #d9534f; font-weight: bold;">Đăng xuất 🔓</a>
            </div>
            
            <h2>⚙️ QUẢN LÝ ĐIỂM HÀNH CHÍNH & LƯU ĐỘNG</h2>
            
            <form method="POST" style="background: #fafafa; padding: 15px; border-radius: 6px; border: 1px solid #e3e3e3;">
                <h3 style="margin-top:0; font-size:15px; color:#333;">Thêm điểm mới vào hệ thống</h3>
                <div style="display: flex; gap: 10px;">
                    <div class="form-group" style="flex:1;">
                        <label>Loại điểm:</label>
                        <select name="category">
                            <option value="UBND Xã">UBND Xã</option>
                            <option value="Công an Xã">Trụ sở Công an Xã</option>
                            <option value="Lưu động">Điểm Lưu động theo thôn</option>
                        </select>
                    </div>
                    <div class="form-group" style="flex:2;">
                        <label>Tên điểm (VD: Nhà văn hóa Thôn 1):</label>
                        <input type="text" name="name" required>
                    </div>
                </div>
                <div class="form-group">
                    <label>Địa chỉ cụ thể:</label>
                    <input type="text" name="address" placeholder="VD: Thôn 1, xã Bờ Ngoong, Gia Lai" required>
                </div>
                <div class="form-group">
                    <label>Thời gian hoạt động:</label>
                    <input type="text" name="time" placeholder="VD: Sáng 12/11/2026 (08:00 - 11:30) hoặc Giờ HC" required>
                </div>
                <div style="display: flex; gap: 10px;">
                    <div class="form-group" style="flex: 1;"><label>Vĩ độ (Lat):</label><input type="text" name="lat" placeholder="VD: 13.905" required></div>
                    <div class="form-group" style="flex: 1;"><label>Kinh độ (Lng):</label><input type="text" name="lng" placeholder="VD: 108.015" required></div>
                </div>
                <div style="display: flex; gap: 10px;">
                    <div class="form-group" style="flex: 1;">
                        <label>Trạng thái:</label>
                        <select name="status"><option value="Sắp diễn ra">Sắp diễn ra</option><option value="Đang diễn ra">Đang diễn ra</option><option value="Hoạt động thường xuyên">Hoạt động thường xuyên</option></select>
                    </div>
                    <div class="form-group" style="flex: 1;">
                        <label>Mức độ đông đúc:</label>
                        <select name="crowd"><option value="🟢 Đang vắng - Đến làm ngay">🟢 Đang vắng - Đến làm ngay</option><option value="🟡 Vừa phải">🟡 Vừa phải</option><option value="🔴 Đang đông">🔴 Đang đông</option></select>
                    </div>
                </div>
                <div class="form-group">
                    <label>Giấy tờ cần mang / Chú ý:</label>
                    <input type="text" name="notes" placeholder="VD: CCCD cũ, ĐTDĐ chính chủ" value="CCCD cũ, Điện thoại cá nhân" required>
                </div>
                <div class="form-group">
                    <label>Số điện thoại Hotline liên hệ:</label>
                    <input type="text" name="phone" placeholder="VD: 0987654321" value="02693xxxxxx" required>
                </div>
                <button type="submit">➕ Lưu và Thêm Điểm</button>
            </form>

            <h3 style="margin-top:25px; font-size:15px;">Danh sách điểm hiện tại trong cơ sở dữ liệu</h3>
            <table>
                <tr>
                    <th>ID</th><th>Loại</th><th>Tên điểm</th><th>Thời gian</th><th>Tọa độ</th><th>Trạng thái</th><th>Thao tác</th>
                </tr>
                {% for r in rows %}
                <tr>
                    <td>{{ r[0] }}</td>
                    <td><b>{{ r[1] }}</b></td>
                    <td>{{ r[2] }}<br><small style="color:#666;">{{ r[3] }}</small></td>
                    <td>{{ r[4] }}</td>
                    <td>{{ r[5] }}, {{ r[6] }}</td>
                    <td>{{ r[7] }}<br><span style="color:#0275d8;">{{ r[8] }}</span></td>
                    <td><a href="/admin/delete/{{ r[0] }}" class="delete-btn" onclick="return confirm('Bạn chắc chắn muốn xóa điểm này?')">Xóa</a></td>
                </tr>
                {% endfor %}
            </table>
        </div>
    </body>
    </html>
    """
    return render_template_string(admin_template, rows=rows)

# 4. CHỨC NĂNG ĐĂNG XUẤT ADMIN
@app.route('/admin/logout')
def admin_logout():
    session.pop('logged_in', None)
    return redirect(url_for('admin_login'))

# 5. CHỨC NĂNG XÓA ĐIỂM
@app.route('/admin/delete/<int:id>')
def delete_point(id):
    if not session.get('logged_in'):
        return redirect(url_for('admin_login'))
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM points WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_dashboard'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)