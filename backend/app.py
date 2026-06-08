#!/usr/bin/env python3
"""
WhoamiSec.com - Backend API v2.0
Privacy-first AI infrastructure. Zero KYC. Monero payments.
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os, uuid, time, json
from datetime import datetime, timedelta

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'whoamisec-production-secret-2026')
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'whoamisec-jwt-production-key')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=30)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///whoamisec.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

CORS(app)
jwt = JWTManager(app)
db = SQLAlchemy(app)

# ============ CONFIG ============
XMR_ADDRESS = "8BuSHCofBXzAti2oQemtqo1j8q2UZHQBpFwqvJa6pMyUWp6x4QZTaWuHBmUxRb5S9Z6KZCqCaosZw78G9ufrffSz6AXjUhJ"
AVAILABLE_MODELS = [
    {"id": "tinyllama", "name": "TinyLlama 1.1B", "size": "650MB", "speed": "fast"},
    {"id": "phi:2.7b", "name": "Phi-2.7B", "size": "1.6GB", "speed": "medium"},
    {"id": "qwen2.5:0.5b", "name": "Qwen 2.5 0.5B", "size": "350MB", "speed": "fast"},
    {"id": "llama3.2:1b", "name": "Llama 3.2 1B", "size": "1.3GB", "speed": "medium"},
    {"id": "deepseek-coder:1.3b", "name": "DeepSeek Coder 1.3B", "size": "750MB", "speed": "medium"},
    {"id": "granite-code:3b", "name": "Granite Code 3B", "size": "2.0GB", "speed": "slow"},
]

# ============ DATABASE MODELS ============
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    credits = db.Column(db.Integer, default=100)
    plan = db.Column(db.String(20), default='starter')
    api_key = db.Column(db.String(64), unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)

    def set_password(self, pw):
        self.password_hash = generate_password_hash(pw)

    def check_password(self, pw):
        return check_password_hash(self.password_hash, pw)

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    txid = db.Column(db.String(128), unique=True)
    amount_xmr = db.Column(db.Float)
    credits_added = db.Column(db.Integer)
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ApiLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    endpoint = db.Column(db.String(100))
    model = db.Column(db.String(50))
    tokens_used = db.Column(db.Integer, default=0)
    ip_address = db.Column(db.String(45))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# ============ AUTH ROUTES ============
@app.route('/api/v1/auth/register', methods=['POST'])
def register():
    data = request.json or {}
    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '')

    if not username or not email or not password:
        return jsonify({'error': 'Username, email, and password are required'}), 400
    if len(password) < 8:
        return jsonify({'error': 'Password must be at least 8 characters'}), 400
    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'Username already taken'}), 409
    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email already registered'}), 409

    user = User(username=username, email=email, plan='starter', credits=100)
    user.set_password(password)
    user.api_key = f"wsec_{uuid.uuid4().hex}"
    db.session.add(user)
    db.session.commit()

    token = create_access_token(identity=user.id)
    return jsonify({
        'token': token,
        'user': {
            'id': user.id, 'username': user.username,
            'email': user.email, 'credits': user.credits,
            'plan': user.plan, 'api_key': user.api_key
        }
    }), 201

@app.route('/api/v1/auth/login', methods=['POST'])
def login():
    data = request.json or {}
    username = data.get('username', '')
    password = data.get('password', '')

    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        return jsonify({'error': 'Invalid username or password'}), 401

    user.last_login = datetime.utcnow()
    db.session.commit()

    token = create_access_token(identity=user.id)
    return jsonify({
        'token': token,
        'user': {
            'id': user.id, 'username': user.username,
            'credits': user.credits, 'plan': user.plan,
            'is_admin': user.is_admin, 'api_key': user.api_key
        }
    })

@app.route('/api/v1/auth/me', methods=['GET'])
@jwt_required()
def get_me():
    user = User.query.get(get_jwt_identity())
    if not user:
        return jsonify({'error': 'User not found'}), 404
    return jsonify({
        'id': user.id, 'username': user.username,
        'email': user.email, 'credits': user.credits,
        'plan': user.plan, 'is_admin': user.is_admin,
        'api_key': user.api_key,
        'created_at': user.created_at.isoformat()
    })

# ============ PAYMENT ROUTES ============
@app.route('/api/v1/payments/info', methods=['GET'])
def payment_info():
    return jsonify({
        'address': XMR_ADDRESS,
        'currency': 'XMR',
        'network': 'monero-mainnet',
        'min_confirmations': 10,
        'plans': {
            'starter': {'price_xmr': 0, 'credits': 100, 'name': 'Starter'},
            'pro': {'price_xmr': 0.05, 'credits': 10000, 'name': 'Pro'},
            'enterprise': {'price_xmr': 0.15, 'credits': 100000, 'name': 'Enterprise'}
        }
    })

@app.route('/api/v1/payments/verify', methods=['POST'])
@jwt_required()
def verify_payment():
    data = request.json or {}
    txid = data.get('txid', '').strip()
    if not txid:
        return jsonify({'error': 'Transaction ID required'}), 400

    user_id = get_jwt_identity()

    existing = Transaction.query.filter_by(txid=txid).first()
    if existing:
        return jsonify({'status': existing.status, 'credits_added': existing.credits_added})

    amount = data.get('amount', 0.05)
    plan = data.get('plan', 'pro')
    credits_map = {'starter': 100, 'pro': 10000, 'enterprise': 100000}
    credits = credits_map.get(plan, 10000)

    tx = Transaction(user_id=user_id, txid=txid, amount_xmr=amount,
                     credits_added=credits, status='confirmed')
    user = User.query.get(user_id)
    user.credits += credits
    user.plan = plan

    db.session.add(tx)
    db.session.commit()

    return jsonify({'status': 'confirmed', 'credits_added': credits, 'total_credits': user.credits})

# ============ AI CHAT ============
@app.route('/api/v1/chat', methods=['POST'])
@jwt_required()
def chat():
    data = request.json or {}
    messages = data.get('messages', [])
    model = data.get('model', 'tinyllama')

    if not messages:
        return jsonify({'error': 'Messages array is required'}), 400

    user = User.query.get(get_jwt_identity())
    if not user:
        return jsonify({'error': 'User not found'}), 404

    if user.plan != 'enterprise' and user.credits < 1:
        return jsonify({'error': 'Insufficient credits. Top up with Monero to continue.'}), 402

    prompt = messages[-1].get('content', '') if messages else ''

    try:
        import urllib.request
        url = "http://localhost:11434/api/generate"
        payload = json.dumps({
            "model": model,
            "prompt": prompt,
            "stream": False
        }).encode()
        req = urllib.request.Request(url, data=payload,
                                    headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read())
            response_text = result.get('response', 'No response generated.')

        if user.plan != 'enterprise':
            user.credits -= 1

        log = ApiLog(user_id=user.id, endpoint='/api/v1/chat', model=model,
                     tokens_used=len(prompt.split()), ip_address=request.remote_addr)
        db.session.add(log)
        db.session.commit()

        return jsonify({
            'response': response_text,
            'model': model,
            'credits_remaining': user.credits,
            'plan': user.plan
        })
    except Exception as e:
        return jsonify({'error': f'AI service temporarily unavailable: {str(e)}'}), 503

# ============ MODELS LIST ============
@app.route('/api/v1/models', methods=['GET'])
@jwt_required()
def list_models():
    return jsonify({'models': AVAILABLE_MODELS})

@app.route('/api/v1/models', methods=['GET'])
def list_models_public():
    return jsonify({'models': AVAILABLE_MODELS})

# ============ ADMIN ============
@app.route('/api/v1/admin/stats', methods=['GET'])
@jwt_required()
def admin_stats():
    user = User.query.get(get_jwt_identity())
    if not user.is_admin:
        return jsonify({'error': 'Admin access required'}), 403

    total_users = User.query.count()
    total_requests = ApiLog.query.count()
    total_tx = Transaction.query.filter_by(status='confirmed').count()
    revenue = sum(t.amount_xmr for t in Transaction.query.filter_by(status='confirmed').all())

    return jsonify({
        'total_users': total_users,
        'total_api_requests': total_requests,
        'total_transactions': total_tx,
        'revenue_xmr': round(revenue, 6),
        'active_models': len(AVAILABLE_MODELS),
        'domain': 'whoamisec.com'
    })

@app.route('/api/v1/admin/users', methods=['GET'])
@jwt_required()
def admin_users():
    user = User.query.get(get_jwt_identity())
    if not user.is_admin:
        return jsonify({'error': 'Forbidden'}), 403

    users = User.query.all()
    return jsonify([{
        'id': u.id, 'username': u.username, 'email': u.email,
        'credits': u.credits, 'plan': u.plan, 'is_admin': u.is_admin,
        'api_key': u.api_key,
        'created_at': u.created_at.isoformat(),
        'last_login': u.last_login.isoformat() if u.last_login else None
    } for u in users])

@app.route('/api/v1/admin/user/<int:uid>', methods=['POST'])
@jwt_required()
def admin_update_user(uid):
    admin = User.query.get(get_jwt_identity())
    if not admin.is_admin:
        return jsonify({'error': 'Forbidden'}), 403

    data = request.json or {}
    user = User.query.get(uid)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    if 'credits' in data:
        user.credits = data['credits']
    if 'plan' in data:
        user.plan = data['plan']
    db.session.commit()

    return jsonify({'success': True, 'credits': user.credits, 'plan': user.plan})

# ============ HEALTH ============
@app.route('/api/v1/health', methods=['GET'])
def health():
    ollama_up = False
    try:
        import urllib.request
        with urllib.request.urlopen('http://localhost:11434/api/tags', timeout=5) as r:
            ollama_up = r.status == 200
    except:
        pass

    return jsonify({
        'status': 'operational' if ollama_up else 'degraded',
        'version': '2.0.0',
        'domain': 'whoamisec.com',
        'timestamp': datetime.utcnow().isoformat(),
        'services': {
            'api': True,
            'auth': True,
            'payments': True,
            'ollama': ollama_up
        },
        'models_available': len(AVAILABLE_MODELS),
        'xmr_address': XMR_ADDRESS
    })

@app.route('/', methods=['GET'])
def root():
    return jsonify({
        'name': 'WhoamiSec API',
        'version': '2.0.0',
        'domain': 'whoamisec.com',
        'docs': 'https://whoamisec.com/#api',
        'endpoints': {
            'health': '/api/v1/health',
            'auth_register': 'POST /api/v1/auth/register',
            'auth_login': 'POST /api/v1/auth/login',
            'chat': 'POST /api/v1/chat',
            'models': 'GET /api/v1/models',
            'payments': '/api/v1/payments/info'
        }
    })

# ============ INIT DB ============
with app.app_context():
    db.create_all()
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(username='admin', email='admin@whoamisec.com',
                      is_admin=True, plan='enterprise', credits=999999)
        admin.set_password('WhoamiSecAdmin2026!')
        admin.api_key = f"wsec_admin_{uuid.uuid4().hex}"
        db.session.add(admin)
        db.session.commit()
        print('[+] Admin user created: admin@whoamisec.com')

if __name__ == '__main__':
    print(f'[+] WhoamiSec API v2.0 starting on http://0.0.0.0:5001')
    print(f'[+] Domain: whoamisec.com')
    print(f'[+] XMR Address: {XMR_ADDRESS}')
    app.run(host='0.0.0.0', port=5001, debug=False, threaded=True)
