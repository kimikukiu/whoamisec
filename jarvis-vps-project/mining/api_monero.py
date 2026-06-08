#!/usr/bin/env python3
import os
import subprocess
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

# Config
XMR_ADDRESS = os.getenv('XMR_ADDRESS')
XMR_PRICE = float(os.getenv('XMR_PRICE', 0.05))
OLLAMA_HOST = os.getenv('OLLAMA_HOST', 'localhost')
OLLAMA_PORT = os.getenv('OLLAMA_PORT', '11434')
API_PORT = int(os.getenv('API_PORT', 5000))
WHITELIST_FILE = 'whitelist.txt'

def is_paid(txid):
    """Verifică dacă un TXID e în whitelist"""
    if not os.path.exists(WHITELIST_FILE):
        return False
    with open(WHITELIST_FILE, 'r') as f:
        return txid in f.read().splitlines()

def call_ollama(prompt, model='llama2'):
    """Apelează Ollama și returnează răspunsul"""
    try:
        result = subprocess.run(
            ['ollama', 'run', model, prompt],
            capture_output=True,
            text=True,
            timeout=60
        )
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        return "Eroare: timeout după 60 secunde"
    except Exception as e:
        return f"Eroare: {str(e)}"

@app.route('/price', methods=['GET'])
def get_price():
    """Returnează prețul și adresa pentru plată"""
    return jsonify({
        'price_xmr': XMR_PRICE,
        'address': XMR_ADDRESS,
        'currency': 'XMR',
        'instructions': f'Trimite exact {XMR_PRICE} XMR la adresa de mai sus. Folosește TXID-ul primit pentru autentificare.'
    })

@app.route('/ask', methods=['POST'])
def ask_ollama():
    """Endpoint principal - verifică plata și răspunde"""
    data = request.json
    
    if not data:
        return jsonify({'error': 'Lipsă JSON body'}), 400
    
    txid = data.get('txid')
    prompt = data.get('prompt')
    model = data.get('model', 'llama2')
    
    if not txid:
        return jsonify({'error': 'Lipsă txid. Plătește întâi la /price'}), 400
    
    if not prompt:
        return jsonify({'error': 'Lipsă prompt'}), 400
    
    # Verifică plata
    if not is_paid(txid):
        return jsonify({
            'error': 'Neplătit',
            'message': f'Trimite {XMR_PRICE} XMR la {XMR_ADDRESS}',
            'price_endpoint': '/price'
        }), 402
    
    # Procesează cererea
    response = call_ollama(prompt, model)
    
    return jsonify({
        'response': response,
        'txid': txid,
        'model': model
    })

@app.route('/health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({'status': 'online', 'service': 'ollama-monero-biz'})

@app.route('/stats', methods=['GET'])
def stats():
    """Statistici (câți au plătit)"""
    if not os.path.exists(WHITELIST_FILE):
        return jsonify({'paid_users': 0})
    
    with open(WHITELIST_FILE, 'r') as f:
        users = f.read().splitlines()
    
    return jsonify({
        'paid_users': len(users),
        'price_xmr': XMR_PRICE
    })

if __name__ == '__main__':
    print(f"🚀 API Monero + Ollama pornit pe http://{os.getenv('API_HOST', '0.0.0.0')}:{API_PORT}")
    print(f"💰 Preț: {XMR_PRICE} XMR per acces")
    print(f"🏦 Adresa: {XMR_ADDRESS}")
    app.run(host=os.getenv('API_HOST', '0.0.0.0'), port=API_PORT, debug=False)
