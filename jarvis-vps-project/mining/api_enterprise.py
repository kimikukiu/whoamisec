#!/usr/bin/env python3
"""
MONERO BIZ ENTERPRISE - API Monetizare Ollama
Features: rate limiting, auto-ban, anti-ddos, logging, metrics, auto-healing
"""

import os
import sys
import json
import time
import hashlib
import subprocess
import logging
import logging.handlers
from datetime import datetime, timedelta
from functools import wraps
from collections import defaultdict
from threading import Lock

from flask import Flask, request, jsonify, g
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv
from prometheus_client import Counter, Histogram, Gauge, generate_latest, REGISTRY

# Redis pentru rate limiting distribuit (opțional)
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

load_dotenv()

# ============ CONFIGURAȚIE ============
XMR_ADDRESS = os.getenv('XMR_ADDRESS')
XMR_PRICE = float(os.getenv('XMR_PRICE', 0.05))
API_SECRET_KEY = os.getenv('API_SECRET_KEY')
ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'boss')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD')
OLLAMA_HOST = os.getenv('OLLAMA_HOST', 'localhost')
OLLAMA_PORT = os.getenv('OLLAMA_PORT', '11434')
API_PORT = int(os.getenv('API_PORT', 5000))
API_HOST = os.getenv('API_HOST', '0.0.0.0')
MAX_FAILED_ATTEMPTS = int(os.getenv('MAX_FAILED_ATTEMPTS', 10))
BAN_DURATION = int(os.getenv('BAN_DURATION_MINUTES', 60))
RATE_LIMIT_PER_IP = os.getenv('RATE_LIMIT_PER_IP', '100 per minute')
REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT_SECONDS', 30))
MAX_BODY_SIZE = int(os.getenv('MAX_BODY_SIZE_MB', 10)) * 1024 * 1024
ENABLE_AUDIT_LOG = os.getenv('ENABLE_AUDIT_LOG', 'true').lower() == 'true'

# ============ LOGGING ============
class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName
        }
        if hasattr(record, 'client_ip'):
            log_entry['client_ip'] = record.client_ip
        if hasattr(record, 'txid'):
            log_entry['txid'] = record.txid
        return json.dumps(log_entry)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('monero-biz')

# File handlers
log_dir = 'logs'
os.makedirs(log_dir, exist_ok=True)

# JSON log for audit
audit_handler = logging.handlers.RotatingFileHandler(
    f'{log_dir}/audit.json', maxBytes=10*1024*1024, backupCount=5
)
audit_handler.setFormatter(JsonFormatter())
audit_handler.setLevel(logging.INFO)

# Error log
error_handler = logging.handlers.RotatingFileHandler(
    f'{log_dir}/error.log', maxBytes=10*1024*1024, backupCount=5
)
error_handler.setLevel(logging.ERROR)

# Access log
access_handler = logging.handlers.RotatingFileHandler(
    f'{log_dir}/access.log', maxBytes=50*1024*1024, backupCount=10
)
access_handler.setLevel(logging.INFO)

logger.addHandler(audit_handler)
logger.addHandler(error_handler)
logger.addHandler(access_handler)

# ============ RATE LIMITING ============
# In-memory storage (fallback dacă Redis nu e disponibil)
class MemoryRateLimiter:
    def __init__(self):
        self.requests = defaultdict(list)
        self.lock = Lock()
    
    def check(self, key, limit, window_seconds):
        now = time.time()
        with self.lock:
            # Clean old entries
            self.requests[key] = [ts for ts in self.requests[key] if ts > now - window_seconds]
            if len(self.requests[key]) >= limit:
                return False
            self.requests[key].append(now)
            return True

rate_limiter = MemoryRateLimiter()

# Redis rate limiter dacă e disponibil
if REDIS_AVAILABLE:
    try:
        redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
        redis_client.ping()
        USE_REDIS = True
        logger.info("Redis connected - using distributed rate limiting")
    except:
        USE_REDIS = False
        logger.warning("Redis not available - using memory rate limiting")
else:
    USE_REDIS = False

def check_rate_limit(key, limit_str):
    """Parses limit string like '100 per minute' and checks"""
    parts = limit_str.split()
    if len(parts) != 3:
        return True
    
    limit = int(parts[0])
    period = parts[2]
    
    window_map = {
        'second': 1, 'seconds': 1,
        'minute': 60, 'minutes': 60,
        'hour': 3600, 'hours': 3600,
        'day': 86400, 'days': 86400
    }
    window = window_map.get(period, 60)
    
    if USE_REDIS:
        current = redis_client.incr(key)
        if current == 1:
            redis_client.expire(key, window)
        return current <= limit
    else:
        return rate_limiter.check(key, limit, window)

# ============ BAN MANAGEMENT ============
class BanManager:
    def __init__(self):
        self.banned_ips = {}  # ip -> unban_time
        self.suspects = defaultdict(int)  # ip -> failed attempts
        self.lock = Lock()
    
    def is_banned(self, ip):
        with self.lock:
            if ip in self.banned_ips:
                if time.time() < self.banned_ips[ip]:
                    return True
                else:
                    del self.banned_ips[ip]
            return False
    
    def record_failure(self, ip):
        with self.lock:
            self.suspects[ip] += 1
            if self.suspects[ip] >= MAX_FAILED_ATTEMPTS:
                self.banned_ips[ip] = time.time() + BAN_DURATION * 60
                logger.warning(f"IP {ip} banned for {BAN_DURATION} minutes")
                return True
        return False
    
    def clear_suspect(self, ip):
        with self.lock:
            if ip in self.suspects:
                del self.suspects[ip]

ban_manager = BanManager()

# ============ PROMETHEUS METRICS ============
if os.getenv('PROMETHEUS_ENABLED', 'true').lower() == 'true':
    requests_total = Counter('api_requests_total', 'Total API requests', ['method', 'endpoint', 'status'])
    request_duration = Histogram('api_request_duration_seconds', 'Request duration', ['endpoint'])
    active_users = Gauge('api_active_users', 'Active users (paid)')
    xmr_received = Counter('xmr_received_total', 'Total XMR received')
    
    def update_metrics():
        if os.path.exists('whitelist.txt'):
            with open('whitelist.txt', 'r') as f:
                active_users.set(len(f.read().splitlines()))
else:
    # Dummy metrics
    requests_total = None
    request_duration = None
    def update_metrics(): pass

# ============ FLASK APP ============
app = Flask(__name__)
CORS(app)

@app.before_request
def before_request():
    """Pre-processing: size limit, rate limit, ban check"""
    # Size limit
    if request.content_length and request.content_length > MAX_BODY_SIZE:
        logger.warning(f"Request too large: {request.content_length} bytes from {request.remote_addr}")
        return jsonify({'error': 'Request too large'}), 413
    
    # Client IP
    g.client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    
    # Ban check
    if ban_manager.is_banned(g.client_ip):
        logger.warning(f"Blocked banned IP: {g.client_ip}")
        return jsonify({'error': 'Too many failed attempts. Try again later.'}), 429
    
    # Rate limit by IP
    ip_key = f"rate_ip:{g.client_ip}"
    if not check_rate_limit(ip_key, RATE_LIMIT_PER_IP):
        logger.warning(f"Rate limit exceeded for IP: {g.client_ip}")
        return jsonify({'error': 'Rate limit exceeded. Slow down!'}), 429

# ============ HELPER FUNCTIONS ============
WHITELIST_FILE = 'whitelist.txt'
WHITELIST_LOCK = Lock()

def is_paid(txid):
    """Check if TXID is whitelisted"""
    if not os.path.exists(WHITELIST_FILE):
        return False
    with WHITELIST_LOCK:
        with open(WHITELIST_FILE, 'r') as f:
            return txid in f.read().splitlines()

def add_to_whitelist(txid):
    """Add TXID to whitelist"""
    with WHITELIST_LOCK:
        if not os.path.exists(WHITELIST_FILE):
            with open(WHITELIST_FILE, 'w') as f:
                f.write(f"{txid}\n")
        else:
            with open(WHITELIST_FILE, 'r') as f:
                existing = f.read().splitlines()
            if txid not in existing:
                with open(WHITELIST_FILE, 'a') as f:
                    f.write(f"{txid}\n")
        update_metrics()

def call_ollama(prompt, model='llama2'):
    """Call Ollama with timeout"""
    try:
        result = subprocess.run(
            ['ollama', 'run', model, prompt],
            capture_output=True,
            text=True,
            timeout=REQUEST_TIMEOUT
        )
        return result.stdout.strip() if result.returncode == 0 else f"Error: {result.stderr}"
    except subprocess.TimeoutExpired:
        return f"Error: Request timeout after {REQUEST_TIMEOUT} seconds"
    except Exception as e:
        return f"Error: {str(e)}"

def log_audit(event, ip, txid=None, details=None):
    """Audit logging"""
    if not ENABLE_AUDIT_LOG:
        return
    log_data = {
        'event': event,
        'ip': ip,
        'txid': txid,
        'details': details,
        'timestamp': datetime.utcnow().isoformat()
    }
    logger.info(json.dumps(log_data))

# ============ ENDPOINTS ============

@app.route('/health', methods=['GET'])
def health():
    """Advanced health check"""
    health_status = {
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'services': {
            'ollama': False,
            'redis': USE_REDIS,
            'monero_wallet': False,
            'api': True
        },
        'stats': {
            'paid_users': 0,
            'banned_ips': len(ban_manager.banned_ips),
            'uptime_seconds': time.time() - app.start_time if hasattr(app, 'start_time') else 0
        }
    }
    
    # Check Ollama
    try:
        result = subprocess.run(['curl', '-s', f'http://{OLLAMA_HOST}:{OLLAMA_PORT}/api/tags'], 
                               capture_output=True, timeout=5)
        if result.returncode == 0:
            health_status['services']['ollama'] = True
    except:
        pass
    
    # Check whitelist count
    if os.path.exists(WHITELIST_FILE):
        with open(WHITELIST_FILE, 'r') as f:
            health_status['stats']['paid_users'] = len(f.read().splitlines())
    
    status_code = 200 if health_status['services']['ollama'] else 503
    return jsonify(health_status), status_code

@app.route('/price', methods=['GET'])
def get_price():
    """Get pricing and payment address"""
    log_audit('price_request', g.client_ip)
    return jsonify({
        'price_xmr': XMR_PRICE,
        'address': XMR_ADDRESS,
        'currency': 'XMR',
        'instructions': f'Trimite exact {XMR_PRICE} XMR la adresa de mai sus. Salvează TXID-ul.',
        'endpoints': {
            'ask': '/ask (POST)',
            'stats': '/stats (GET)',
            'health': '/health (GET)'
        }
    })

@app.route('/ask', methods=['POST'])
def ask_ollama():
    """Main endpoint - with rate limiting per TXID"""
    start_time = time.time()
    client_ip = g.client_ip
    
    # Rate limit by TXID
    txid = request.json.get('txid') if request.json else None
    
    if txid:
        txid_key = f"rate_txid:{txid}"
        if not check_rate_limit(txid_key, os.getenv('RATE_LIMIT_PER_TXID', '1000 per hour')):
            return jsonify({'error': 'TXID rate limit exceeded'}), 429
    
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'Missing JSON body'}), 400
        
        txid = data.get('txid')
        prompt = data.get('prompt')
        model = data.get('model', os.getenv('OLLAMA_MODEL', 'llama2'))
        
        if not txid:
            log_audit('missing_txid', client_ip)
            return jsonify({'error': 'Missing txid', 'solution': 'First pay at /price'}), 400
        
        if not prompt:
            return jsonify({'error': 'Missing prompt'}), 400
        
        # Check payment
        if not is_paid(txid):
            # Record failed attempt
            should_ban = ban_manager.record_failure(client_ip)
            log_audit('unpaid_request', client_ip, txid)
            
            if should_ban:
                return jsonify({'error': 'Too many attempts. You are banned.'}), 429
            
            return jsonify({
                'error': 'unpaid',
                'message': f'No payment found for TXID: {txid}',
                'required_payment': XMR_PRICE,
                'payment_address': XMR_ADDRESS
            }), 402
        
        # Clear suspect records on success
        ban_manager.clear_suspect(client_ip)
        
        # Process the request
        log_audit('ask_request', client_ip, txid, {'prompt_length': len(prompt), 'model': model})
        response = call_ollama(prompt, model)
        
        # Update metrics
        if requests_total:
            requests_total.labels(method='POST', endpoint='/ask', status=200).inc()
        if request_duration:
            request_duration.labels(endpoint='/ask').observe(time.time() - start_time)
        
        return jsonify({
            'response': response,
            'txid': txid,
            'model': model,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/stats', methods=['GET'])
def get_stats():
    """Statistics endpoint"""
    paid_users = 0
    if os.path.exists(WHITELIST_FILE):
        with open(WHITELIST_FILE, 'r') as f:
            paid_users = len(f.read().splitlines())
    
    return jsonify({
        'paid_users': paid_users,
        'price_xmr': XMR_PRICE,
        'banned_ips': len(ban_manager.banned_ips),
        'total_attempts': sum(ban_manager.suspects.values()),
        'rate_limit': RATE_LIMIT_PER_IP,
        'address': XMR_ADDRESS[:20] + '...'  # truncated for privacy
    })

@app.route('/metrics', methods=['GET'])
def metrics():
    """Prometheus metrics endpoint"""
    if os.getenv('PROMETHEUS_ENABLED', 'true').lower() == 'true':
        update_metrics()
        return generate_latest(REGISTRY), 200, {'Content-Type': 'text/plain'}
    return jsonify({'error': 'Metrics disabled'}), 404

@app.route('/admin/ban/<ip>', methods=['POST'])
def admin_ban_ip(ip):
    """Admin endpoint to ban IP"""
    auth = request.authorization
    if not auth or auth.username != ADMIN_USERNAME or auth.password != ADMIN_PASSWORD:
        return jsonify({'error': 'Unauthorized'}), 401
    
    ban_manager.banned_ips[ip] = time.time() + BAN_DURATION * 60
    log_audit('admin_ban', g.client_ip, None, {'banned_ip': ip})
    return jsonify({'message': f'IP {ip} banned'}), 200

# ============ AUTO-HEALING THREAD ============
import threading

def auto_heal():
    """Background thread for auto-healing"""
    while True:
        try:
            # Check Ollama
            result = subprocess.run(['curl', '-s', f'http://{OLLAMA_HOST}:{OLLAMA_PORT}/api/tags'],
                                   capture_output=True, timeout=5)
            if result.returncode != 0:
                logger.warning("Ollama not responding, attempting restart...")
                subprocess.run(['pkill', '-f', 'ollama serve'])
                time.sleep(2)
                subprocess.Popen(['nohup', 'ollama', 'serve'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                logger.info("Ollama restarted")
            
            # Backup whitelist
            if os.getenv('BACKUP_ENABLED', 'true').lower() == 'true':
                backup_interval = int(os.getenv('BACKUP_INTERVAL_HOURS', 6)) * 3600
                # Implementation in backup.sh script
            
        except Exception as e:
            logger.error(f"Auto-heal error: {e}")
        
        time.sleep(60)  # Check every minute

# Start auto-healing thread
heal_thread = threading.Thread(target=auto_heal, daemon=True)
heal_thread.start()

# ============ MAIN ============
if __name__ == '__main__':
    app.start_time = time.time()
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║     MONERO BIZ ENTERPRISE - Ollama API Monetizare           ║
╠══════════════════════════════════════════════════════════════╣
║  🚀 API running on: http://{API_HOST}:{API_PORT}                      
║  💰 Price: {XMR_PRICE} XMR per access                                   
║  🏦 Address: {XMR_ADDRESS[:30]}...                    
║  🔒 Rate limiting: {RATE_LIMIT_PER_IP}                                  
║  🛡️ Auto-ban: {MAX_FAILED_ATTEMPTS} attempts → {BAN_DURATION} min ban     
║  📊 Metrics: http://{API_HOST}:{API_PORT}/metrics                        
╚══════════════════════════════════════════════════════════════╝
    """)
    app.run(host=API_HOST, port=API_PORT, debug=False, threaded=True)
