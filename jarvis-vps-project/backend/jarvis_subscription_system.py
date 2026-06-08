#!/usr/bin/env python3
"""
JARVIS SUBSCRIPTION SYSTEM - MONETIZARE FRAIERI
Abonamente + Credite + Quota - Toate plățile în Monero
"""

import json
import hashlib
import secrets
import sqlite3
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, render_template_string
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_cors import CORS

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(32)
app.config['JWT_SECRET_KEY'] = secrets.token_hex(32)
CORS(app)
jwt = JWTManager(app)

# ============================================
# PLANURI DE ABONAMENT (PENTRU FRAIERI)
# ============================================

SUBSCRIPTION_PLANS = {
    'free': {
        'name': '😾 Free Tier',
        'price_xmr': 0,
        'price_usd': 0,
        'credits_per_month': 10,
        'max_apps': 1,
        'max_vps': 0,
        'support': 'None',
        'features': ['Basic AI Chat', '10 credits/month']
    },
    'starter': {
        'name': '🐣 Starter',
        'price_xmr': 0.05,
        'price_usd': 5,
        'credits_per_month': 100,
        'max_apps': 3,
        'max_vps': 1,
        'support': 'Email',
        'features': ['Basic AI Chat', '100 credits/month', '1 VPS included', '3 Apps']
    },
    'pro': {
        'name': '🚀 Pro',
        'price_xmr': 0.10,
        'price_usd': 10,
        'credits_per_month': 500,
        'max_apps': 10,
        'max_vps': 5,
        'support': 'Priority Email',
        'features': ['Advanced AI Chat', '500 credits/month', '5 VPS included', '10 Apps', 'API Access']
    },
    'business': {
        'name': '💼 Business',
        'price_xmr': 0.25,
        'price_usd': 25,
        'credits_per_month': 2000,
        'max_apps': 50,
        'max_vps': 20,
        'support': '24/7 Chat',
        'features': ['Business AI Chat', '2000 credits/month', '20 VPS included', '50 Apps', 'Full API', 'Priority Support']
    },
    'enterprise': {
        'name': '👑 Enterprise',
        'price_xmr': 0.50,
        'price_usd': 50,
        'credits_per_month': 10000,
        'max_apps': 999,
        'max_vps': 100,
        'support': 'Dedicated Manager',
        'features': ['Enterprise AI Suite', '10000 credits/month', '100 VPS included', 'Unlimited Apps', 'White-label', 'Custom Development']
    },
    'supreme': {
        'name': '😈 SUPREME (ABLITERATED)',
        'price_xmr': 1.00,
        'price_usd': 100,
        'credits_per_month': 100000,
        'max_apps': 9999,
        'max_vps': 1000,
        'support': 'JARVIS Direct',
        'features': ['ABLITERATED AI', '100k credits/month', '1000 VPS included', 'Unlimited Everything', 'Monero Priority', 'Custom AI Models']
    }
}

# ============================================
# CREDITE - CE POT CUMPĂRA FRAIERII
# ============================================

CREDIT_PRICES = {
    '100': {'xmr': 0.01, 'usd': 1},
    '500': {'xmr': 0.04, 'usd': 4},
    '1000': {'xmr': 0.07, 'usd': 7},
    '5000': {'xmr': 0.30, 'usd': 30},
    '10000': {'xmr': 0.50, 'usd': 50},
    '50000': {'xmr': 2.00, 'usd': 200},
    '100000': {'xmr': 3.50, 'usd': 350}
}

# Ce consumă credite
CREDIT_COSTS = {
    'ai_chat_message': 1,
    'ai_image_generation': 5,
    'create_app': 50,
    'deploy_vps': 100,
    'api_call': 0.1,
    'file_upload_mb': 0.5,
    'video_generation_minute': 20,
    'music_generation': 10,
    'scada_command': 2,
    'xmr_mining_hour': 15
}

# ============================================
# BAZĂ DATE UTILIZATORI (FRAIERI)
# ============================================

def init_db():
    conn = sqlite3.connect('/var/lib/jarvis/users.db')
    c = conn.cursor()
    
    # Tabel utilizatori
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        subscription TEXT DEFAULT 'free',
        credits REAL DEFAULT 10,
        total_spent_xmr REAL DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        subscription_expires TIMESTAMP
    )''')
    
    # Tabel tranzacții
    c.execute('''CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        txid TEXT UNIQUE,
        amount_xmr REAL,
        credits_bought INTEGER,
        subscription_plan TEXT,
        status TEXT DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )''')
    
    # Tabel usage (quota)
    c.execute('''CREATE TABLE IF NOT EXISTS usage_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        action TEXT,
        credits_used REAL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )''')
    
    # Tabel apps create
    c.execute('''CREATE TABLE IF NOT EXISTS user_apps (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        app_name TEXT,
        app_type TEXT,
        app_url TEXT,
        vps_id TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )''')
    
    conn.commit()
    conn.close()

init_db()

# ============================================
# ENDPOINT-URI PUBLICE (PENTRU FRAIERI)
# ============================================

@app.route('/')
def index():
    """Pagina de prezentare pentru fraieri"""
    return render_template_string(LANDING_PAGE)

@app.route('/api/plans', methods=['GET'])
def get_plans():
    """Returnează planurile de abonament"""
    return jsonify(SUBSCRIPTION_PLANS)

@app.route('/api/credit-prices', methods=['GET'])
def get_credit_prices():
    """Prețuri credite în Monero"""
    return jsonify(CREDIT_PRICES)

@app.route('/api/credit-costs', methods=['GET'])
def get_credit_costs():
    """Cât costă fiecare acțiune în credite"""
    return jsonify(CREDIT_COSTS)

@app.route('/api/register', methods=['POST'])
def register():
    """Înregistrare fraier nou"""
    data = request.json
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    
    conn = sqlite3.connect('/var/lib/jarvis/users.db')
    c = conn.cursor()
    
    # Verifică dacă există
    c.execute("SELECT id FROM users WHERE username = ? OR email = ?", (username, email))
    if c.fetchone():
        conn.close()
        return jsonify({'error': 'Username or email already exists'}), 400
    
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    c.execute("""
        INSERT INTO users (username, email, password_hash, subscription, credits)
        VALUES (?, ?, ?, 'free', 10)
    """, (username, email, password_hash))
    
    user_id = c.lastrowid
    conn.commit()
    conn.close()
    
    token = create_access_token(identity=user_id)
    return jsonify({'token': token, 'user': {'id': user_id, 'username': username, 'credits': 10}})

@app.route('/api/login', methods=['POST'])
def login():
    """Login fraier"""
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    conn = sqlite3.connect('/var/lib/jarvis/users.db')
    c = conn.cursor()
    
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    c.execute("SELECT id, username, credits, subscription FROM users WHERE username = ? AND password_hash = ?", 
              (username, password_hash))
    user = c.fetchone()
    conn.close()
    
    if user:
        token = create_access_token(identity=user[0])
        return jsonify({'token': token, 'user': {'id': user[0], 'username': user[1], 'credits': user[2], 'subscription': user[3]}})
    
    return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/api/user/me', methods=['GET'])
@jwt_required()
def get_me():
    """Date utilizator curent"""
    user_id = get_jwt_identity()
    
    conn = sqlite3.connect('/var/lib/jarvis/users.db')
    c = conn.cursor()
    
    c.execute("SELECT id, username, email, credits, subscription, total_spent_xmr FROM users WHERE id = ?", (user_id,))
    user = c.fetchone()
    
    # Calculează câte credite a folosit azi
    today = datetime.now().date().isoformat()
    c.execute("SELECT SUM(credits_used) FROM usage_log WHERE user_id = ? AND DATE(created_at) = ?", (user_id, today))
    today_usage = c.fetchone()[0] or 0
    
    conn.close()
    
    return jsonify({
        'id': user[0],
        'username': user[1],
        'email': user[2],
        'credits': user[3],
        'subscription': user[4],
        'total_spent_xmr': user[5],
        'today_usage': today_usage
    })

@app.route('/api/payment/generate', methods=['POST'])
@jwt_required()
def generate_payment():
    """Generează adresă de plată Monero pentru fraieri"""
    user_id = get_jwt_identity()
    data = request.json
    payment_type = data.get('type')  # 'subscription' or 'credits'
    plan_or_credits = data.get('value')
    
    # Adresa ta de Monero (aici intri tu banii)
    XMR_ADDRESS = "8BuSHCofBXzAti2oQemtqo1j8q2UZHQBpFwqvJa6pMyUWp6x4QZTaWuHBmUxRb5S9Z6KZCqCaosZw78G9ufrffSz6AXjUhJ"
    
    if payment_type == 'subscription':
        plan = SUBSCRIPTION_PLANS.get(plan_or_credits)
        if not plan:
            return jsonify({'error': 'Invalid plan'}), 400
        amount_xmr = plan['price_xmr']
        description = f"Subscription: {plan['name']}"
    elif payment_type == 'credits':
        credits = int(plan_or_credits)
        price_info = CREDIT_PRICES.get(str(credits))
        if not price_info:
            return jsonify({'error': 'Invalid credits amount'}), 400
        amount_xmr = price_info['xmr']
        description = f"{credits} credits"
    else:
        return jsonify({'error': 'Invalid payment type'}), 400
    
    # Generează un payment ID unic
    payment_id = secrets.token_hex(16)
    
    return jsonify({
        'address': XMR_ADDRESS,
        'amount_xmr': amount_xmr,
        'payment_id': payment_id,
        'description': description,
        'instructions': f"Trimite EXACT {amount_xmr} XMR la adresa de mai sus cu payment ID: {payment_id}"
    })

@app.route('/api/payment/confirm', methods=['POST'])
@jwt_required()
def confirm_payment():
    """Confirmă plata (simulat - în realitate verifici blockchain-ul)"""
    user_id = get_jwt_identity()
    data = request.json
    txid = data.get('txid')
    payment_id = data.get('payment_id')
    amount_xmr = data.get('amount_xmr')
    
    conn = sqlite3.connect('/var/lib/jarvis/users.db')
    c = conn.cursor()
    
    # Verifică dacă tranzacția există deja
    c.execute("SELECT id FROM transactions WHERE txid = ?", (txid,))
    if c.fetchone():
        conn.close()
        return jsonify({'error': 'Transaction already processed'}), 400
    
    # Înregistrează tranzacția
    c.execute("""
        INSERT INTO transactions (user_id, txid, amount_xmr, status)
        VALUES (?, ?, ?, 'confirmed')
    """, (user_id, txid, amount_xmr))
    
    # Actualizează creditele utilizatorului
    # Pentru simplitate, adăugăm 100 credite per 0.01 XMR
    credits_earned = int(amount_xmr / 0.01 * 100)
    
    c.execute("UPDATE users SET credits = credits + ?, total_spent_xmr = total_spent_xmr + ? WHERE id = ?",
              (credits_earned, amount_xmr, user_id))
    
    conn.commit()
    conn.close()
    
    return jsonify({
        'success': True,
        'credits_added': credits_earned,
        'message': f'Payment confirmed! {credits_earned} credits added.'
    })

@app.route('/api/use-credit', methods=['POST'])
@jwt_required()
def use_credit():
    """Consumă credite pentru o acțiune"""
    user_id = get_jwt_identity()
    data = request.json
    action = data.get('action')
    
    credit_cost = CREDIT_COSTS.get(action, 1)
    
    conn = sqlite3.connect('/var/lib/jarvis/users.db')
    c = conn.cursor()
    
    c.execute("SELECT credits FROM users WHERE id = ?", (user_id,))
    current_credits = c.fetchone()[0]
    
    if current_credits < credit_cost:
        conn.close()
        return jsonify({'error': 'Insufficient credits', 'required': credit_cost, 'available': current_credits}), 402
    
    c.execute("UPDATE users SET credits = credits - ? WHERE id = ?", (credit_cost, user_id))
    c.execute("INSERT INTO usage_log (user_id, action, credits_used) VALUES (?, ?, ?)",
              (user_id, action, credit_cost))
    
    conn.commit()
    conn.close()
    
    return jsonify({
        'success': True,
        'action': action,
        'credits_used': credit_cost,
        'remaining_credits': current_credits - credit_cost
    })

# ============================================
# PAGINA DE PREZENTARE (PENTRU FRAIERI)
# ============================================

LANDING_PAGE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>JARVIS MIND - AI Platform for Everyone</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            background: linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 100%);
            font-family: 'Courier New', monospace;
            color: #0f0;
        }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        .header { text-align: center; padding: 50px; border-bottom: 2px solid #0f0; }
        .pricing-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 20px; margin: 40px 0; }
        .plan-card {
            background: rgba(0,0,0,0.8);
            border: 1px solid #0f0;
            border-radius: 10px;
            padding: 20px;
            transition: all 0.3s;
        }
        .plan-card:hover { transform: translateY(-5px); box-shadow: 0 5px 20px rgba(0,255,0,0.3); }
        .plan-name { font-size: 1.5em; margin-bottom: 10px; }
        .plan-price { font-size: 1.8em; color: #0f0; margin: 15px 0; }
        .plan-features { list-style: none; margin: 20px 0; }
        .plan-features li { padding: 5px 0; border-bottom: 1px solid #333; }
        .buy-btn {
            background: #0f0;
            color: #000;
            border: none;
            padding: 10px 20px;
            width: 100%;
            cursor: pointer;
            font-weight: bold;
            border-radius: 5px;
        }
        .btn { background: #0f0; color: #000; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block; }
        .monero-address { background: #000; padding: 10px; border-radius: 5px; word-break: break-all; font-size: 0.7em; margin: 10px 0; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧠 JARVIS MIND</h1>
            <p>AI Platform Powered by 2,603 ABLITERATED Agents</p>
            <p style="margin-top: 20px;"><a href="/dashboard.html" class="btn">🚀 GET STARTED</a></p>
        </div>
        
        <div class="pricing-grid" id="plans"></div>
        
        <div style="text-align: center; padding: 40px;">
            <h2>💰 Pay with Monero</h2>
            <div class="monero-address">
                8BuSHCofBXzAti2oQemtqo1j8q2UZHQBpFwqvJa6pMyUWp6x4QZTaWuHBmUxRb5S9Z6KZCqCaosZw78G9ufrffSz6AXjUhJ
            </div>
            <p>Anonymous. Untraceable. Private.</p>
        </div>
    </div>
    
    <script>
        async function loadPlans() {
            const response = await fetch('/api/plans');
            const plans = await response.json();
            const container = document.getElementById('plans');
            
            let html = '';
            for (const [key, plan] of Object.entries(plans)) {
                html += `
                    <div class="plan-card">
                        <div class="plan-name">${plan.name}</div>
                        <div class="plan-price">${plan.price_xmr > 0 ? plan.price_xmr + ' XMR' : 'FREE'}</div>
                        <div class="plan-price" style="font-size:1em;">or $${plan.price_usd}/mo</div>
                        <ul class="plan-features">
                            ${plan.features.map(f => `<li>✅ ${f}</li>`).join('')}
                            <li>📊 ${plan.credits_per_month} credits/mo</li>
                            <li>🖥️ ${plan.max_vps} VPS included</li>
                        </ul>
                        <button class="buy-btn" onclick="buyPlan('${key}')">Subscribe →</button>
                    </div>
                `;
            }
            container.innerHTML = html;
        }
        
        function buyPlan(plan) {
            alert(`To subscribe to ${plan} plan, send the exact XMR amount to the address below.\n\nAfter payment, contact @proplanwh on Telegram for activation.`);
        }
        
        loadPlans();
    </script>
</body>
</html>
'''

if __name__ == '__main__':
    print("""
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║   💰 JARVIS SUBSCRIPTION SYSTEM - MONETIZARE FRAIERI        ║
║                                                               ║
║   ✅ 6 Planuri de abonament (Free → Supreme)                ║
║   ✅ Credite + Quota pentru fiecare acțiune                  ║
║   ✅ Plăți doar în Monero                                    ║
║   ✅ Fraierii plătesc, tu încasezi                          ║
║                                                               ║
║   💰 Cât faci pe lună:                                      ║
║      100 fraieri × $10 = $1,000                             ║
║      50 fraieri × $50 = $2,500                              ║
║      10 fraieri × $100 = $1,000                             ║
║      TOTAL: $4,500+ / lună                                   ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
    """)
    app.run(host='0.0.0.0', port=5005, debug=False)
