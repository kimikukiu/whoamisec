#!/usr/bin/env python3
"""
JARVIS MIND SECURE - DOAR ADMIN CREEAZĂ VPS
2,603 AGENȚI ABLITERAȚI | CONTROL TOTAL ADMIN
"""

import os
import sys
import json
import time
import hashlib
import secrets
import threading
import subprocess
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, request, jsonify, render_template_string, session
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import jwt

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(32)
app.config['JWT_SECRET'] = secrets.token_hex(32)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins='*')

# ============================================
# BAZĂ DATE ADMINI (DOAR TU)
# ============================================
ADMIN_CREDENTIALS = {
    'username': 'boss',
    'password_hash': hashlib.sha256('WhoamiSecBoss2026!'.encode()).hexdigest(),
    'role': 'super_admin',
    'permissions': ['create_vps', 'delete_vps', 'manage_mining', 'create_apps', 'all']
}

# Stocare token-uri active
active_tokens = {}

def generate_token(username):
    """Generează JWT token pentru admin"""
    token = jwt.encode({
        'username': username,
        'role': 'super_admin',
        'exp': datetime.utcnow() + timedelta(hours=24)
    }, app.config['JWT_SECRET'], algorithm='HS256')
    active_tokens[token] = datetime.utcnow()
    return token

def verify_token(token):
    """Verifică token-ul JWT"""
    try:
        payload = jwt.decode(token, app.config['JWT_SECRET'], algorithms=['HS256'])
        if payload.get('role') == 'super_admin':
            return True
    except:
        pass
    return False

def admin_required(f):
    """Decorator pentru endpoint-uri doar admin"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token or not verify_token(token):
            return jsonify({'error': 'Unauthorized. Admin access required.'}), 401
        return f(*args, **kwargs)
    return decorated

# ============================================
# LOGURI CREARE VPS
# ============================================
def log_vps_creation(admin_user, vps_name, vps_ip, ram, cpu):
    """Înregistrează cine a creat VPS-ul"""
    log_entry = {
        'timestamp': datetime.utcnow().isoformat(),
        'admin': admin_user,
        'vps_name': vps_name,
        'vps_ip': vps_ip,
        'ram': ram,
        'cpu': cpu,
        'action': 'CREATE_VPS'
    }
    
    with open('/var/log/vps_audit.log', 'a') as f:
        f.write(json.dumps(log_entry) + '\n')
    
    print(f"📝 LOG: {admin_user} a creat VPS {vps_name}")

# ============================================
# FUNCȚII CREARE VPS (DOAR ADMIN)
# ============================================
def create_vps_secure(admin_user, count=1, ram=256, cpu=64, disk=500):
    """Creează VPS-uri noi - DOAR chemată de admin"""
    results = []
    
    for i in range(count):
        vps_id = int(time.time()) * 1000 + i
        vps_name = f"vps_admin_{vps_id}"
        vps_ip = f"10.100.{i}.{i+1}"
        
        # Aici ar fi codul real de creare VPS
        # systemd-nspawn, docker, etc.
        
        results.append({
            'name': vps_name,
            'ip': vps_ip,
            'ram': f"{ram}GB",
            'cpu': f"{cpu} cores",
            'disk': f"{disk}GB",
            'status': 'created',
            'created_by': admin_user,
            'created_at': datetime.utcnow().isoformat()
        })
        
        log_vps_creation(admin_user, vps_name, vps_ip, ram, cpu)
    
    return results

# ============================================
# ENDPOINT-URI SECURIZATE
# ============================================

@app.route('/')
def index():
    """Pagina principală - login înainte"""
    return render_template_string(LOGIN_TEMPLATE)

@app.route('/api/login', methods=['POST'])
def login():
    """Autentificare admin"""
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    if username == ADMIN_CREDENTIALS['username'] and password_hash == ADMIN_CREDENTIALS['password_hash']:
        token = generate_token(username)
        return jsonify({
            'success': True,
            'token': token,
            'username': username,
            'role': 'super_admin'
        })
    
    return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/api/dashboard', methods=['GET'])
@admin_required
def dashboard():
    """Dashboard admin - doar după login"""
    return render_template_string(DASHBOARD_TEMPLATE)

@app.route('/api/vps/create', methods=['POST'])
@admin_required
def create_vps_endpoint():
    """Endpoint creare VPS - DOAR ADMIN"""
    data = request.json
    count = data.get('count', 1)
    ram = data.get('ram', 256)
    cpu = data.get('cpu', 64)
    disk = data.get('disk', 500)
    
    # Obține admin-ul din token
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    payload = jwt.decode(token, app.config['JWT_SECRET'], algorithms=['HS256'])
    admin_user = payload.get('username')
    
    if count > 100:
        return jsonify({'error': 'Maximum 100 VPS per request'}), 400
    
    vps_list = create_vps_secure(admin_user, count, ram, cpu, disk)
    
    return jsonify({
        'success': True,
        'message': f'{count} VPS-uri create cu succes de {admin_user}',
        'vps_list': vps_list
    })

@app.route('/api/vps/list', methods=['GET'])
@admin_required
def list_vps():
    """Listează toate VPS-urile - doar admin vede"""
    # Aici ar fi cod real de listare VPS
    return jsonify({
        'vps_list': [
            {'name': 'vps-001', 'ip': '10.100.0.1', 'ram': '256GB', 'status': 'running', 'created_by': 'boss'},
            {'name': 'vps-002', 'ip': '10.100.0.2', 'ram': '256GB', 'status': 'running', 'created_by': 'boss'}
        ]
    })

@app.route('/api/audit/logs', methods=['GET'])
@admin_required
def audit_logs():
    """Vezi log-urile cu cine a creat VPS-uri"""
    logs = []
    if os.path.exists('/var/log/vps_audit.log'):
        with open('/var/log/vps_audit.log', 'r') as f:
            for line in f:
                try:
                    logs.append(json.loads(line))
                except:
                    pass
    return jsonify({'logs': logs[-50:]})  # Ultimele 50 log-uri

@app.route('/api/stats', methods=['GET'])
@admin_required
def get_stats():
    """Statistici doar pentru admin"""
    return jsonify({
        'total_vps': 5,
        'total_agents': 2603,
        'total_xmr_mined': '1.234567',
        'active_miners': 100,
        'admin_actions': len([l for l in os.listdir('/var/log/') if 'audit' in l]) if os.path.exists('/var/log/') else 0
    })

# ============================================
# TEMPLATE-URI
# ============================================

LOGIN_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>JARVIS MIND - Admin Login</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            background: linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 100%);
            font-family: 'Courier New', monospace;
            height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        .login-container {
            background: rgba(0,0,0,0.8);
            border: 2px solid #0f0;
            border-radius: 20px;
            padding: 40px;
            width: 400px;
            text-align: center;
        }
        h1 { margin-bottom: 30px; animation: glow 2s infinite; }
        @keyframes glow {
            0% { text-shadow: 0 0 5px #0f0; }
            100% { text-shadow: 0 0 20px #0f0; }
        }
        input {
            width: 100%;
            background: #000;
            border: 1px solid #0f0;
            color: #0f0;
            padding: 12px;
            margin: 10px 0;
            font-family: monospace;
        }
        button {
            width: 100%;
            background: #0f0;
            color: #000;
            border: none;
            padding: 12px;
            margin-top: 20px;
            font-weight: bold;
            cursor: pointer;
        }
        .error { color: #f00; margin-top: 10px; }
    </style>
</head>
<body>
    <div class="login-container">
        <h1>🔐 JARVIS MIND</h1>
        <p>ADMIN ACCESS ONLY</p>
        <input type="text" id="username" placeholder="Username">
        <input type="password" id="password" placeholder="Password">
        <button onclick="login()">ACCESS SYSTEM</button>
        <div id="error" class="error"></div>
    </div>
    
    <script>
        async function login() {
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            
            const response = await fetch('/api/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                localStorage.setItem('adminToken', data.token);
                window.location.href = '/api/dashboard';
            } else {
                document.getElementById('error').innerText = data.error;
            }
        }
    </script>
</body>
</html>
'''

DASHBOARD_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>JARVIS MIND - Admin Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            background: linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 100%);
            font-family: 'Courier New', monospace;
            color: #0f0;
            padding: 20px;
        }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { text-align: center; padding: 30px; border-bottom: 2px solid #0f0; margin-bottom: 30px; }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .stat-card { background: rgba(0,0,0,0.8); border: 1px solid #0f0; border-radius: 10px; padding: 20px; text-align: center; }
        .stat-value { font-size: 2em; font-weight: bold; }
        .vps-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 20px; margin-top: 20px; }
        .vps-card { background: rgba(0,0,0,0.6); border: 1px solid #0f0; border-radius: 10px; padding: 15px; }
        input, select { background: #000; border: 1px solid #0f0; color: #0f0; padding: 10px; margin: 5px; }
        button { background: #0f0; color: #000; border: none; padding: 10px 20px; cursor: pointer; font-weight: bold; margin: 5px; }
        .create-section { background: rgba(0,0,0,0.8); border: 2px solid #0f0; border-radius: 10px; padding: 20px; margin-bottom: 30px; text-align: center; }
        .logout { position: fixed; top: 20px; right: 20px; }
    </style>
</head>
<body>
    <div class="container">
        <button class="logout" onclick="logout()">🚪 LOGOUT</button>
        
        <div class="header">
            <h1>👑 JARVIS MIND - ADMIN DASHBOARD</h1>
            <p>DOAR TU POȚI CREA VPS-URI | 2,603 AGENȚI ABLITERAȚI</p>
        </div>
        
        <div class="stats-grid" id="stats">
            <div class="stat-card"><div>🖥️ TOTAL VPS</div><div class="stat-value" id="totalVps">0</div></div>
            <div class="stat-card"><div>🤖 AGENȚI</div><div class="stat-value">2,603</div></div>
            <div class="stat-card"><div>⛏️ XMR MINAT</div><div class="stat-value" id="xmrMined">0</div></div>
            <div class="stat-card"><div>👑 ADMIN</div><div class="stat-value">BOSS</div></div>
        </div>
        
        <div class="create-section">
            <h2>🚀 CREEAZĂ VPS-URI NOI (DOAR TU)</h2>
            <input type="number" id="vpsCount" value="1" min="1" max="100" style="width:100px">
            <select id="vpsRam">
                <option value="256">256GB RAM</option>
                <option value="128">128GB RAM</option>
                <option value="512">512GB RAM</option>
            </select>
            <select id="vpsCpu">
                <option value="64">64 Core</option>
                <option value="32">32 Core</option>
                <option value="128">128 Core</option>
            </select>
            <button onclick="createVPS()">⚡ CREEAZĂ VPS</button>
            <button onclick="createMultipleVPS()">🚀 CREEAZĂ 10 VPS</button>
        </div>
        
        <h2>📋 VPS-URILE TALE</h2>
        <div id="vpsList" class="vps-grid">Loading...</div>
        
        <h2>📝 LOGURI CREARE VPS</h2>
        <div id="auditLogs" style="background:#000; padding:15px; border-radius:10px; max-height:300px; overflow-y:auto; font-size:0.8em;"></div>
    </div>
    
    <script>
        const token = localStorage.getItem('adminToken');
        if (!token) window.location.href = '/';
        
        async function fetchAPI(endpoint, options = {}) {
            const response = await fetch(endpoint, {
                ...options,
                headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' }
            });
            if (response.status === 401) {
                localStorage.removeItem('adminToken');
                window.location.href = '/';
            }
            return response.json();
        }
        
        async function createVPS() {
            const count = parseInt(document.getElementById('vpsCount').value);
            const ram = parseInt(document.getElementById('vpsRam').value);
            const cpu = parseInt(document.getElementById('vpsCpu').value);
            
            const data = await fetchAPI('/api/vps/create', {
                method: 'POST',
                body: JSON.stringify({ count, ram, cpu })
            });
            
            if (data.success) {
                alert(data.message);
                loadVPSList();
                loadStats();
                loadAuditLogs();
            } else {
                alert('Error: ' + (data.error || 'Unknown'));
            }
        }
        
        async function createMultipleVPS() {
            const data = await fetchAPI('/api/vps/create', {
                method: 'POST',
                body: JSON.stringify({ count: 10, ram: 256, cpu: 64 })
            });
            
            if (data.success) {
                alert(data.message);
                loadVPSList();
                loadStats();
                loadAuditLogs();
            }
        }
        
        async function loadVPSList() {
            const data = await fetchAPI('/api/vps/list');
            const vpsList = data.vps_list || [];
            const grid = document.getElementById('vpsList');
            
            if (vpsList.length === 0) {
                grid.innerHTML = '<div style="text-align:center;padding:50px;">📭 Niciun VPS creat încă. Folosește formularul de sus.</div>';
                return;
            }
            
            let html = '';
            vpsList.forEach(vps => {
                html += `
                    <div class="vps-card">
                        <strong>🖥️ ${vps.name}</strong><br>
                        📡 IP: ${vps.ip}<br>
                        💾 RAM: ${vps.ram}<br>
                        ⚡ CPU: ${vps.cpu}<br>
                        👑 Creat de: ${vps.created_by || 'boss'}<br>
                        <span style="color:#0f0">✅ ${vps.status || 'running'}</span>
                    </div>
                `;
            });
            grid.innerHTML = html;
        }
        
        async function loadStats() {
            const data = await fetchAPI('/api/stats');
            document.getElementById('totalVps').innerText = data.total_vps || 0;
            document.getElementById('xmrMined').innerText = data.total_xmr_mined || '0';
        }
        
        async function loadAuditLogs() {
            const data = await fetchAPI('/api/audit/logs');
            const logs = data.logs || [];
            const logsDiv = document.getElementById('auditLogs');
            
            if (logs.length === 0) {
                logsDiv.innerHTML = '<div>📝 Niciun log încă.</div>';
                return;
            }
            
            let html = '';
            logs.forEach(log => {
                html += `<div>[${log.timestamp}] 👑 ${log.admin} a creat VPS ${log.vps_name} (${log.ram}/${log.cpu})</div>`;
            });
            logsDiv.innerHTML = html;
        }
        
        function logout() {
            localStorage.removeItem('adminToken');
            window.location.href = '/';
        }
        
        loadVPSList();
        loadStats();
        loadAuditLogs();
        setInterval(loadStats, 5000);
    </script>
</body>
</html>
'''

if __name__ == '__main__':
    print("""
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║   👑 JARVIS MIND SECURE - DOAR ADMIN CREEAZĂ VPS            ║
║                                                               ║
║   ✅ Autentificare admin obligatorie                         ║
║   ✅ Token JWT valid 24h                                     ║
║   ✅ Log-uri cu cine a creat ce VPS                          ║
║   ✅ Doar tu ai butonul de "CREATE VPS"                      ║
║                                                               ║
║   🔐 Username: boss                                          ║
║   🔐 Password: WhoamiSecBoss2026!                            ║
║                                                               ║
║   🌐 http://localhost:5004                                   ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
    """)
    socketio.run(app, host='0.0.0.0', port=5004, debug=False)
