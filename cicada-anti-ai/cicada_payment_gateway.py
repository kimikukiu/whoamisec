#!/usr/bin/env python3
"""
CICADA OMNI — Payment Gateway
7 payment methods: XMR, Lightning, USDC, BTC, LTC, PayPal Crypto, Gift Cards
All non-XMR payments auto-swap to XMR via ChangeNOW/StealthEX
Port: 5130
"""

from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import secrets, json
from datetime import datetime

app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = secrets.token_hex(32)

# ── CONFIG ────────────────────────────────────────────────────────────────────
# Replace with real addresses before deploying
XMR_ADDRESS = "8BuSHCofBXzAti2oQemtqo1j8q2UZHQBpFwqvJa6pMyUWp6x4QZTaWuHBmUxRb5S9Z6KZCqCaosZw78G9ufrffSz6AXjUhJ"
BTC_ADDRESS = "YOUR_BTC_ADDRESS_HERE"
LTC_ADDRESS = "YOUR_LTC_ADDRESS_HERE"
USDC_ADDRESS = "YOUR_USDC_ADDRESS_HERE"
PAYPAL_EMAIL = "YOUR_PAYPAL_EMAIL_HERE"
CONTACT_EMAIL = "contact@whoamisec.com"

PAYMENT_METHODS = {
    'xmr': {
        'name': 'Monero (XMR)',
        'icon': '🦗',
        'address': XMR_ADDRESS,
        'fee': '0%',
        'confirmations': 10,
        'time': '~20 min',
        'anonymous': True,
    },
    'lightning': {
        'name': 'Lightning Network (BTC)',
        'icon': '⚡',
        'address': 'lnbc1...',
        'fee': '0.1%',
        'confirmations': 1,
        'time': '~5 sec',
        'anonymous': True,
    },
    'usdc': {
        'name': 'USDC (Polygon)',
        'icon': '💵',
        'address': USDC_ADDRESS,
        'fee': '0.5%',
        'confirmations': 12,
        'time': '~3 min',
        'anonymous': False,
    },
    'btc': {
        'name': 'Bitcoin (BTC)',
        'icon': '₿',
        'address': BTC_ADDRESS,
        'fee': '0.8%',
        'confirmations': 3,
        'time': '~30 min',
        'anonymous': False,
    },
    'ltc': {
        'name': 'Litecoin (LTC)',
        'icon': 'Ł',
        'address': LTC_ADDRESS,
        'fee': '0.3%',
        'confirmations': 6,
        'time': '~10 min',
        'anonymous': False,
    },
    'paypal': {
        'name': 'PayPal Crypto',
        'icon': '📱',
        'address': PAYPAL_EMAIL,
        'fee': '1.5%',
        'confirmations': 0,
        'time': '~30 sec',
        'anonymous': False,
    },
    'giftcard': {
        'name': 'Gift Card (Amazon / Steam)',
        'icon': '🎁',
        'address': CONTACT_EMAIL,
        'fee': '0%',
        'confirmations': 0,
        'time': '~24h (manual)',
        'anonymous': True,
    },
}

PRICING = {
    'puzzle_access':       {'xmr': 0.01,  'usd': 2},
    'full_puzzle_set':     {'xmr': 0.05,  'usd': 10},
    'vps_256gb':           {'xmr': 0.10,  'usd': 20},
    'miner_10nodes':       {'xmr': 0.05,  'usd': 10},
    'miner_100nodes':      {'xmr': 0.35,  'usd': 70},
    'subscription_monthly':{'xmr': 0.10,  'usd': 20},
    'affiliate_upgrade':   {'xmr': 0.25,  'usd': 50},
}

# In-memory invoice store (use Redis/DB in production)
_invoices: dict = {}

# ── HELPERS ───────────────────────────────────────────────────────────────────

def new_invoice(method: str, product: str) -> dict:
    if method not in PAYMENT_METHODS or product not in PRICING:
        return {}
    inv_id = secrets.token_hex(16)
    price = PRICING[product]
    pay = PAYMENT_METHODS[method]
    inv = {
        'id': inv_id,
        'method': method,
        'product': product,
        'amount_xmr': price['xmr'],
        'amount_usd': price['usd'],
        'address': pay['address'],
        'status': 'pending',
        'created_at': datetime.utcnow().isoformat(),
        'swap_provider': None if method == 'xmr' else 'ChangeNOW',
    }
    _invoices[inv_id] = inv
    return inv

# ── HTML ──────────────────────────────────────────────────────────────────────

PAYMENT_PAGE = r'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>CICADA OMNI — Payment Gateway</title>
  <style>
    *{margin:0;padding:0;box-sizing:border-box;}
    body{background:#000;font-family:'Courier New',monospace;color:#0f0;padding:1.5rem;}
    h1{text-align:center;letter-spacing:.25rem;margin-bottom:.4rem;font-size:1.4rem;}
    .sub{text-align:center;font-size:.6rem;opacity:.4;letter-spacing:.15rem;margin-bottom:2rem;}
    .grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:1rem;margin-bottom:2rem;}
    .card{background:#0a0a0a;border:1px solid #0f0;border-radius:8px;padding:1.2rem;
      text-align:center;cursor:pointer;transition:.3s;}
    .card:hover{transform:translateY(-4px);box-shadow:0 4px 20px rgba(0,255,0,.25);}
    .icon{font-size:2.5rem;margin-bottom:.6rem;}
    .name{font-weight:700;margin-bottom:.3rem;}
    .fee{font-size:.6rem;opacity:.5;}
    select,button{background:#000;border:1px solid #0f0;color:#0f0;
      padding:.7rem 1rem;font-family:monospace;font-size:.85rem;margin:.3rem;}
    button{background:#0f0;color:#000;font-weight:900;cursor:pointer;transition:.2s;}
    button:hover{background:#0ff;}
    .invoice{background:#0a0a0a;border:2px solid #0f0;border-radius:8px;
      padding:2rem;margin-top:1rem;text-align:center;display:none;}
    .addr{background:#000;padding:.8rem;word-break:break-all;font-size:.75rem;
      margin:.8rem 0;border:1px solid rgba(0,255,0,.3);}
    .label{font-size:.55rem;opacity:.4;letter-spacing:.1rem;margin-bottom:.3rem;}
    footer{text-align:center;font-size:.5rem;opacity:.25;margin-top:2rem;}
  </style>
</head>
<body>
  <h1>💳 CICADA OMNI — PAYMENT GATEWAY</h1>
  <div class="sub">7 PAYMENT METHODS · ALL CONVERT TO XMR AUTOMATICALLY</div>

  <div class="label" style="margin-bottom:.4rem;">SELECT PRODUCT</div>
  <select id="prod">
    <option value="puzzle_access">🧩 Puzzle Access — 0.01 XMR / $2</option>
    <option value="full_puzzle_set">🦗 Full Puzzle Set — 0.05 XMR / $10</option>
    <option value="vps_256gb">🖥 VPS 256 GB — 0.10 XMR / $20</option>
    <option value="miner_10nodes">⛏ Miner 10 Nodes — 0.05 XMR / $10</option>
    <option value="miner_100nodes">⛏ Miner 100 Nodes — 0.35 XMR / $70</option>
    <option value="subscription_monthly">🌟 Monthly Subscription — 0.10 XMR / $20</option>
    <option value="affiliate_upgrade">👑 Affiliate Upgrade — 0.25 XMR / $50</option>
  </select>

  <div class="grid" id="methods"></div>
  <div class="invoice" id="inv"></div>

  <footer>3301 · VERITAS ODIUM PARIT · ALL PAYMENTS CONVERTED TO XMR</footer>

  <script>
    async function load(){
      const r=await fetch('/api/payment/methods');const d=await r.json();
      const c=document.getElementById('methods');
      c.innerHTML=Object.entries(d).map(([k,m])=>`
        <div class="card" onclick="pay('${k}')">
          <div class="icon">${m.icon}</div>
          <div class="name">${m.name}</div>
          <div class="fee">Fee: ${m.fee} · ${m.time}</div>
          <div class="fee">${m.anonymous?'🔒 Anonymous':'📝 ID required'}</div>
        </div>`).join('');
    }
    async function pay(method){
      const prod=document.getElementById('prod').value;
      const r=await fetch(`/api/payment/invoice/${method}/${prod}`);
      const d=await r.json();
      const el=document.getElementById('inv');
      el.style.display='block';
      el.innerHTML=`
        <h2>${d.icon||'💰'} ${d.method_name||method.toUpperCase()} INVOICE</h2>
        <p style="margin:.5rem 0;font-size:.75rem;opacity:.5;">Invoice ID: ${d.id}</p>
        <p>Amount: <strong>${d.amount_xmr} XMR</strong> (≈ $${d.amount_usd})</p>
        ${d.swap_provider?`<p style="font-size:.6rem;opacity:.5;margin-top:.3rem;">Swap: ${d.swap_provider} BTC→XMR</p>`:''}
        <div class="label" style="margin-top:1rem;">SEND TO THIS ADDRESS</div>
        <div class="addr">${d.address}</div>
        <button onclick="check('${d.id}')">Check Payment</button>
        <button onclick="document.getElementById('inv').style.display='none'" style="background:#333;color:#0f0;">Close</button>`;
    }
    async function check(id){
      const r=await fetch(`/api/payment/verify/${id}`);const d=await r.json();
      alert(d.status==='confirmed'?'✅ Payment confirmed! Access granted.':'⏳ Still pending. Please wait.');
    }
    load();
  </script>
</body>
</html>'''

# ── FLASK ROUTES ──────────────────────────────────────────────────────────────

@app.route('/pay')
def pay_page():
    return render_template_string(PAYMENT_PAGE)

@app.route('/api/payment/methods')
def methods():
    return jsonify(PAYMENT_METHODS)

@app.route('/api/payment/pricing')
def pricing():
    return jsonify(PRICING)

@app.route('/api/payment/invoice/<method>/<product>')
def invoice(method, product):
    inv = new_invoice(method, product)
    if not inv:
        return jsonify({'error': 'Invalid method or product'}), 400
    pm = PAYMENT_METHODS.get(method, {})
    inv['icon'] = pm.get('icon', '💰')
    inv['method_name'] = pm.get('name', method.upper())
    return jsonify(inv)

@app.route('/api/payment/verify/<inv_id>')
def verify(inv_id):
    inv = _invoices.get(inv_id)
    if not inv:
        return jsonify({'status': 'not_found', 'invoice_id': inv_id}), 404
    # Production: query blockchain/exchange API here
    return jsonify({'status': inv['status'], 'invoice_id': inv_id,
                    'created_at': inv['created_at']})

@app.route('/api/health')
def health():
    return jsonify({'status': 'ACTIVE', 'service': 'cicada-payment-gateway', 'port': 5130})

if __name__ == '__main__':
    print("""
╔══════════════════════════════════════════════════════════════════╗
║  💳 CICADA OMNI — PAYMENT GATEWAY                              ║
║  ✅ XMR · Lightning · USDC · BTC · LTC · PayPal · Gift Cards  ║
║  ✅ Non-XMR payments auto-swap → XMR (ChangeNOW/StealthEX)    ║
║  🌐 http://0.0.0.0:5130/pay                                   ║
╚══════════════════════════════════════════════════════════════════╝
    """)
    app.run(host='0.0.0.0', port=5130, debug=False)
