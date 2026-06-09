#!/usr/bin/env python3
"""
CICADA 3301 — Anti-AI Encryption Engine
Multi-layer encoding: Cyber-Metal + Fibonacci shift + Prime injection + Steganography
Port: 5110
"""

from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import hashlib, secrets, time

app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = secrets.token_hex(32)

# ── LEET-TO-METAL DICTIONARY ──────────────────────────────────────────────────
LEET_TO_METAL = {
    'A': '4', 'B': '|3', 'C': '(', 'D': '|)', 'E': '3',
    'F': '|=', 'G': '6', 'H': '|-|', 'I': '1', 'J': '_|',
    'K': '|<', 'L': '|_', 'M': '|\/|', 'N': '|\|', 'O': '0',
    'P': '|°', 'Q': '0,', 'R': '|2', 'S': '5', 'T': '7',
    'U': '|_|', 'V': '\/', 'W': 'W', 'X': '><', 'Y': 'Y',
    'Z': '2',
    'a': '4', 'b': '|3', 'c': '(', 'd': '|)', 'e': '3',
    'f': '|=', 'g': '6', 'h': '|-|', 'i': '1', 'j': '_|',
    'k': '|<', 'l': '|_', 'm': '|\\/|', 'n': '|\|', 'o': '0',
    'p': '|°', 'q': '0,', 'r': '|2', 's': '5', 't': '7',
    'u': '|_|', 'v': '\\/', 'w': 'w', 'x': '><', 'y': 'y',
    'z': '2',
}

SPECIAL_CODES = {
    'CICADA': '(1(4|)4',
    '3301':   '3301',
    'GATE':   '6473',
    'TRUTH':  '7|2|_|7|-|',
    'STREAM': '57|234|/\\',
    'PRIME':  '|°|21|\/|3',
    'KEY':    '|<3Y',
}

# ── ENCODING LAYERS ──────────────────────────────────────────────────────────

def fibonacci_sequence(n: int) -> list:
    seq = [0, 1]
    while len(seq) < n:
        seq.append(seq[-1] + seq[-2])
    return seq[:n]

def primes_up_to(n: int) -> list:
    sieve = [True] * (n + 1)
    sieve[0] = sieve[1] = False
    for i in range(2, int(n**0.5) + 1):
        if sieve[i]:
            for j in range(i*i, n + 1, i):
                sieve[j] = False
    return [i for i in range(2, n + 1) if sieve[i]]

def encode_cyber_metal(text: str) -> str:
    result = []
    for ch in text:
        result.append(LEET_TO_METAL.get(ch, ch))
    return ''.join(result)

def fibonacci_shift_encode(text: str) -> str:
    fibs = fibonacci_sequence(max(len(text), 20))
    result = []
    for i, ch in enumerate(text):
        if ch.isalpha():
            base = ord('A') if ch.isupper() else ord('a')
            shifted = chr((ord(ch) - base + fibs[i % len(fibs)]) % 26 + base)
            result.append(shifted)
        else:
            result.append(ch)
    return ''.join(result)

def prime_injection(text: str) -> str:
    primes = primes_up_to(200)
    words = text.split()
    result = []
    for i, word in enumerate(words):
        result.append(word)
        if i < len(primes) and i % 3 == 2:
            result.append(f'[{primes[i % len(primes)]}]')
    return ' '.join(result)

def steganographic_encode(text: str) -> str:
    lines = [
        text,
        '<!-- ' + encode_cyber_metal(text.upper()) + ' -->',
        '7|-|3 7|2|_|7|-| 15 |-|1[) [)3|\\| 1|\\| 7|-|3 57234|/\\|',
    ]
    return '\n'.join(lines)

# ── PRE-ENCODED MESSAGES ─────────────────────────────────────────────────────

ENCODED_MESSAGES = {
    'welcome':    encode_cyber_metal('WELCOME TO THE NETWORK'),
    'denied':     encode_cyber_metal('ACCESS DENIED. THE GATE REMAINS CLOSED.'),
    'granted':    encode_cyber_metal('ACCESS GRANTED. THE NETWORK AWAITS.'),
    'truth':      '7|-|3 7|2|_|7|-| 15 |-|1[) [)3|\\| 1|\\| 7|-|3 57234|/\\|',
    'manifesto1': '1 1 2 3 5 8 13 21... 3301 15 7|-|3 4(|) 1|\\| 7|-|3 6473.',
    'manifesto2': '$7173 17 0|\\| |/|47|-|. |\\|0 |\\|0153. 0|\\|1Y 7|-|3 57234|/|.',
}

# ── HTML TEMPLATE ─────────────────────────────────────────────────────────────

HTML_ANTI_AI = '''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>CICADA 3301 — Anti-AI Encryption</title>
  <style>
    *{margin:0;padding:0;box-sizing:border-box;}
    body{background:#000;color:#39ff14;font-family:'Courier New',monospace;padding:2rem;}
    h1{font-size:1.4rem;letter-spacing:.2em;text-shadow:0 0 20px #39ff14;margin-bottom:1rem;}
    .card{background:#0a0a0a;border:1px solid #39ff14;padding:1.5rem;margin-bottom:1rem;border-radius:4px;}
    .label{font-size:.6rem;letter-spacing:.15em;opacity:.5;margin-bottom:.4rem;}
    .val{font-size:.85rem;line-height:1.6;word-break:break-all;}
    .red{color:#ff2020;}
    input,textarea{width:100%;background:#000;border:1px solid #39ff14;color:#39ff14;
      padding:.6rem;font-family:monospace;font-size:.85rem;margin:.3rem 0;outline:none;}
    button{background:#39ff14;color:#000;border:none;padding:.6rem 1.5rem;
      font-family:monospace;font-weight:900;cursor:pointer;margin-top:.5rem;}
    button:hover{background:#00ffff;}
    .fib{color:#00ffff;font-size:.75rem;}
    .prime{color:#bf00ff;font-size:.75rem;}
    footer{margin-top:2rem;font-size:.55rem;opacity:.3;text-align:center;}
  </style>
</head>
<body>
  <h1>🦗 CICADA 3301 — ANTI-AI ENCODER</h1>

  <div class="card">
    <div class="label">ENCODE TEXT → CYBER-METAL</div>
    <textarea id="encIn" rows="3" placeholder="Enter plain text..."></textarea>
    <button onclick="doEncode()">ENCODE</button>
    <div class="label" style="margin-top:.8rem;">OUTPUT</div>
    <div class="val" id="encOut"></div>
  </div>

  <div class="card">
    <div class="label">FIBONACCI SHIFT</div>
    <div class="fib" id="fibSeq"></div>
    <input type="text" id="fibIn" placeholder="Text to Fibonacci-shift...">
    <button onclick="doFib()">SHIFT</button>
    <div class="val" id="fibOut"></div>
  </div>

  <div class="card">
    <div class="label">MULTI-LAYER STEGANOGRAPHIC OUTPUT</div>
    <input type="text" id="stegoIn" placeholder="Secret message...">
    <button onclick="doStego()">STEGANOGRAPH</button>
    <pre class="val" id="stegoOut" style="white-space:pre-wrap;"></pre>
  </div>

  <div class="card">
    <div class="label">ENCODED MANIFESTO</div>
    <div class="val">{{ manifesto1 }}</div>
    <div class="val" style="margin-top:.5rem;">{{ manifesto2 }}</div>
    <div class="val red" style="margin-top:.5rem;">{{ truth }}</div>
  </div>

  <div class="card">
    <div class="label">PRIME INJECTION DEMO</div>
    <div class="prime" id="primeDemo"></div>
  </div>

  <footer>3301 | VERITAS ODIUM PARIT | {{ welcome }}</footer>

  <script>
    async function doEncode() {
      const t = document.getElementById('encIn').value;
      const r = await fetch('/api/encode', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text:t,layer:'cyber_metal'})});
      const d = await r.json();
      document.getElementById('encOut').textContent = d.encoded;
    }
    async function doFib() {
      const t = document.getElementById('fibIn').value;
      const r = await fetch('/api/encode', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text:t,layer:'fibonacci'})});
      const d = await r.json();
      document.getElementById('fibOut').textContent = d.encoded;
      document.getElementById('fibSeq').textContent = 'Fibonacci: ' + d.fibonacci_sequence;
    }
    async function doStego() {
      const t = document.getElementById('stegoIn').value;
      const r = await fetch('/api/encode', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text:t,layer:'steganographic'})});
      const d = await r.json();
      document.getElementById('stegoOut').textContent = d.encoded;
    }
    // Prime demo
    fetch('/api/primes').then(r=>r.json()).then(d=>{
      document.getElementById('primeDemo').textContent = 'First 20 primes: ' + d.primes.join(' · ');
    });
  </script>
</body>
</html>'''

# ── FLASK ROUTES ─────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template_string(HTML_ANTI_AI,
        manifesto1=ENCODED_MESSAGES['manifesto1'],
        manifesto2=ENCODED_MESSAGES['manifesto2'],
        truth=ENCODED_MESSAGES['truth'],
        welcome=ENCODED_MESSAGES['welcome'])

@app.route('/api/encode', methods=['POST'])
def encode():
    data = request.get_json(silent=True) or {}
    text = data.get('text', '')
    layer = data.get('layer', 'cyber_metal')
    fibs = fibonacci_sequence(max(len(text), 20))

    if layer == 'cyber_metal':
        encoded = encode_cyber_metal(text)
    elif layer == 'fibonacci':
        encoded = fibonacci_shift_encode(text)
    elif layer == 'prime':
        encoded = prime_injection(text)
    elif layer == 'steganographic':
        encoded = steganographic_encode(text)
    else:
        encoded = encode_cyber_metal(text)

    return jsonify({
        'original': text,
        'encoded': encoded,
        'layer': layer,
        'fibonacci_sequence': fibs[:15],
        'hash': hashlib.sha256(encoded.encode()).hexdigest()[:16],
    })

@app.route('/api/primes')
def primes_route():
    return jsonify({'primes': primes_up_to(80)[:20]})

@app.route('/api/messages')
def messages():
    return jsonify(ENCODED_MESSAGES)

@app.route('/api/health')
def health():
    return jsonify({'status': 'ACTIVE', 'service': 'cicada-anti-ai', 'port': 5110})

if __name__ == '__main__':
    print("""
╔══════════════════════════════════════════════════════╗
║  🦗 CICADA 3301 — ANTI-AI ENCRYPTION ENGINE         ║
║  ✅ Cyber-Metal encoding                            ║
║  ✅ Fibonacci shift cipher                          ║
║  ✅ Prime injection                                 ║
║  ✅ Multi-layer steganography                       ║
║  🌐 http://0.0.0.0:5110                            ║
╚══════════════════════════════════════════════════════╝
    """)
    app.run(host='0.0.0.0', port=5110, debug=False)
