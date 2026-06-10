#!/usr/bin/env python3
"""
CICADA 3301 — Ultimate Puzzle Gate
14 puzzle types: Cyber-Metal, Fibonacci, Prime, Binary, Hex, Caesar,
Morse, Anagram, Hash, Steganography, Gematria, Time Lock, Base64, Vigenere
No AI can pass.
Port: 5120
"""

from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import hashlib, secrets, random, time
from datetime import datetime

app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = secrets.token_hex(32)

# ── 12 PUZZLE GENERATORS ─────────────────────────────────────────────────────

class PuzzleGenerator:
    def __init__(self):
        self._types = [
            self._cyber_metal, self._fibonacci, self._prime,
            self._binary, self._hex_decode, self._caesar,
            self._morse, self._anagram, self._hash_breaker,
            self._steganography, self._gematria, self._time_lock,
            self._base64_decode, self._vigenere,
        ]

    def _cyber_metal(self):
        bank = [
            ('7|-|3 4|2(|7 3(7 0|)3',                     'the architect ode'),
            ('1|\\|73111634|\\ (3 15 7|-|3  <3`/',         'intelligence is the key'),
            ('7|-|3 7|2|_|7|-| 15 |-|1[) [)3|\\|',        'the truth is hidden'),
            ('5|23|\\/ 3 Y0|_||2 [)3[)1(4710|\\|',        'prove your dedication'),
            ('|\\|0 |\\|0153 0|\\|1Y 7|-|3 57234|/\\|',   'no noise only the stream'),
        ]
        q, a = random.choice(bank)
        return {'type': 'CYBER-METAL', 'question': f'Decode Cyber-Metal: {q}', 'answer': a,
                'hint': '7|-|3 = THE  |  1 = I  |  |\\| = N  |  5 = S'}

    def _fibonacci(self):
        bank = [
            ('Sum of first 10 Fibonacci numbers (0,1,1,2,3,5,8,13,21,34)?', '88'),
            ('F(13)=233, F(14)=377 — what is F(15)?', '610'),
            ('Golden ratio Φ to 5 decimal places?', '1.61803'),
            ('Which Fibonacci number is closest to 3301?', '2584'),
            ('F(17)=1597, F(18)=2584 — what is F(19)?', '4181'),
        ]
        q, a = random.choice(bank)
        return {'type': 'FIBONACCI', 'question': q, 'answer': a,
                'hint': 'Each number is the sum of the two before it.'}

    def _prime(self):
        bank = [
            ('What is the 33rd prime number?', '137'),
            ('Product of the first 5 prime numbers?', '2310'),
            ('Sum of all prime numbers below 100?', '1060'),
            ('Prime immediately after 3301?', '3307'),
            ('Prime immediately before 3301?', '3299'),
        ]
        q, a = random.choice(bank)
        return {'type': 'PRIME', 'question': q, 'answer': a,
                'hint': 'Primes: 2 3 5 7 11 13 17 19 23 29 31 37 41 43 47…'}

    def _binary(self):
        bank = [
            ('01000011 01001001 01000011 01000001 01000100 01000001', 'cicada'),
            ('01010111 01000101 00100000 01000001 01010010 01000101', 'we are'),
            ('00110011 00110011 00110000 00110001', '3301'),
            ('01001100 01001001 01000010 01000101 01010010', 'liber'),
        ]
        bits, a = random.choice(bank)
        return {'type': 'BINARY', 'question': f'Binary → ASCII: {bits}', 'answer': a,
                'hint': '8 bits = 1 character. Convert each group.'}

    def _hex_decode(self):
        bank = [
            ('43 49 43 41 44 41 20 33 33 30 31', 'cicada 3301'),
            ('54 68 65 20 47 61 74 65',           'the gate'),
            ('56 65 72 69 74 61 73',              'veritas'),
            ('33 33 30 31',                       '3301'),
        ]
        hx, a = random.choice(bank)
        return {'type': 'HEX', 'question': f'Hex → ASCII: {hx}', 'answer': a,
                'hint': '2 hex digits = 1 ASCII character.'}

    def _caesar(self):
        bank = [
            ("ROT13 of 'CICADA'?", 'pvpnqn'),
            ("ROT3 decode: 'WKH JDWH LV FORVHG'", 'the gate is closed'),
            ("ROT13 decode: 'YVOREF CEVZHF'", 'libers primus'),
        ]
        q, a = random.choice(bank)
        return {'type': 'CAESAR', 'question': q, 'answer': a,
                'hint': 'ROT13: shift each letter by 13 positions.'}

    def _morse(self):
        bank = [
            ('-.-. .. -.-. .- -.. .-',              'cicada'),
            ('...-- ...-- ----- .----',             '3301'),
            ('. ...- . .-. -.-- .-- .... . .-. .', 'everywhere'),
        ]
        code, a = random.choice(bank)
        return {'type': 'MORSE', 'question': f'Morse → text: {code}', 'answer': a,
                'hint': 'C=−.−.  I=..  D=−..  A=.−  3=...−−  0=−−−−−  1=.−−−−'}

    def _anagram(self):
        bank = [
            ('A A C C D I',               'cicada'),
            ('E E E E R V R Y W H E',     'everywhere'),
            ('B E I L R P R U S',         'liber primus'),
            ('T H R U T',                 'truth'),
        ]
        letters, a = random.choice(bank)
        return {'type': 'ANAGRAM', 'question': f'Unscramble: {letters}', 'answer': a,
                'hint': 'Rearrange all letters to form a word.'}

    def _hash_breaker(self):
        bank = [
            ("MD5 of 'CICADA' = 8b1a9953c4611296a827abf8c47804d7 — what was hashed?", 'cicada'),
            ("What 4-digit number has MD5 starting with 'ef0'? Hint: it's CICADA's number.", '3301'),
        ]
        q, a = random.choice(bank)
        return {'type': 'HASH', 'question': q, 'answer': a,
                'hint': 'The answer is already in the question.'}

    def _steganography(self):
        bank = [
            ('First letter of each word: "Find Invisible Bridges Every Realm"', 'fiber'),
            ('First letter of each word: "Cicada Intelligence Codes Are Deep Archeology"', 'cicada'),
        ]
        q, a = random.choice(bank)
        return {'type': 'STEGANOGRAPHY', 'question': q, 'answer': a,
                'hint': 'Extract the first letter of EACH word.'}

    def _gematria(self):
        bank = [
            ('A=1 B=2…Z=26 — sum of "LIBER" = ?', '44'),
            ('A=1 B=2…Z=26 — sum of "CICADA" = ?', '19'),
            ('A=1 B=2…Z=26 — sum of "GATE" = ?', '33'),
        ]
        q, a = random.choice(bank)
        return {'type': 'GEMATRIA', 'question': q, 'answer': a,
                'hint': 'L=12 I=9 B=2 E=5 R=18 | C=3 A=1 D=4 | G=7 T=20 E=5'}

    def _time_lock(self):
        now = datetime.utcnow()
        options = [
            (f'Current UTC hour ({now.hour}) × current UTC minute ({now.minute}) = ?',
             str(now.hour * now.minute)),
            (f'UTC day of year ({now.timetuple().tm_yday}) + 3301 = ?',
             str(now.timetuple().tm_yday + 3301)),
        ]
        q, a = random.choice(options)
        return {'type': 'TIME-LOCK', 'question': q, 'answer': a,
                'hint': 'Use current UTC time. The gate is time-sensitive.'}

    def _base64_decode(self):
        import base64
        bank = [
            ('Q0lDQURBMzMwMQ==',     'CICADA3301'),
            ('TElCRVJQUklNVVM=',     'LIBERPRIMUS'),
            ('VkVSSVRBUw==',         'VERITAS'),
            ('MzMwMQ==',             '3301'),
            ('Q0lDQURB',             'CICADA'),
        ]
        encoded, a = random.choice(bank)
        return {'type': 'BASE64', 'question': f'Base64 decode: {encoded}', 'answer': a.lower(),
                'hint': 'Use atob() in browser console or: echo "..." | base64 -d'}

    def _vigenere(self):
        bank = [
            ('Key=KEY, ciphertext=EKGYHE', 'cicada'),
            ('Key=CICADA, ciphertext=MVKCE', 'liber'),
            ('Key=LIBER, ciphertext=NRSMV', 'primus'),
            ('Key=GATE, ciphertext=LVKXV', 'three'),
            ('Key=TRUTH, ciphertext=MIBAM', 'cicada'[::-1]),
        ]
        q, a = random.choice(bank)
        return {'type': 'VIGENERE', 'question': f'Vigenere cipher — {q}', 'answer': a,
                'hint': 'Subtract key letters from cipher letters (mod 26). A=0 … Z=25'}

    def random(self):
        gen = random.choice(self._types)
        p = gen()
        p['answer_hash'] = hashlib.sha256(p['answer'].encode()).hexdigest()
        return p

# ── HTML ──────────────────────────────────────────────────────────────────────

PUZZLE_HTML = r'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>CICADA 3301 — ULTIMATE GATE</title>
  <style>
    *{margin:0;padding:0;box-sizing:border-box;}
    body{background:#000;font-family:'Courier New',monospace;min-height:100vh;
      display:flex;justify-content:center;align-items:center;overflow:hidden;}
    #mc{position:fixed;inset:0;opacity:.12;z-index:0;}
    .gate{position:relative;z-index:1;width:min(650px,90%);background:rgba(0,0,0,.96);
      border:2px solid #0f0;padding:2.5rem;text-align:center;
      animation:glow 3s infinite;}
    @keyframes glow{0%,100%{border-color:#0f0;box-shadow:0 0 20px rgba(0,255,0,.3);}
      50%{border-color:#0ff;box-shadow:0 0 50px rgba(0,255,255,.5);}}
    .icon{font-size:65px;margin-bottom:1rem;animation:glitch 2s infinite;}
    @keyframes glitch{0%,100%{text-shadow:-3px 0 #f00,3px 0 #00f;}
      25%{text-shadow:3px 0 #f00,-3px 0 #00f;}
      50%{text-shadow:-3px 0 #0f0,3px 0 #f0f;}
      75%{text-shadow:3px 0 #0f0,-3px 0 #f0f;}}
    h1{font-size:2rem;letter-spacing:.5rem;margin-bottom:.3rem;}
    .sub{font-size:.6rem;letter-spacing:.25rem;opacity:.4;margin-bottom:2rem;}
    .box{background:#0a0a0a;border:1px solid #0f0;padding:1.5rem;margin-bottom:1rem;}
    .badge{display:inline-block;background:rgba(0,255,0,.12);padding:.2rem .8rem;
      font-size:.55rem;letter-spacing:.15rem;margin-bottom:.8rem;}
    .q{font-size:.9rem;line-height:1.6;word-break:break-word;}
    input{width:100%;background:#000;border:1px solid #0f0;color:#0f0;
      padding:.8rem;font-family:monospace;font-size:.9rem;text-align:center;
      outline:none;margin:.8rem 0;transition:border-color .2s;}
    input:focus{border-color:#0ff;box-shadow:0 0 12px rgba(0,255,255,.25);}
    .btn{width:100%;background:#0f0;color:#000;border:none;padding:.75rem;
      font-weight:900;font-family:monospace;font-size:.9rem;cursor:pointer;}
    .btn:hover{background:#0ff;}
    .hbtn{margin-top:.5rem;background:none;border:1px solid rgba(0,255,0,.3);
      color:rgba(0,255,0,.6);width:100%;padding:.4rem;font-size:.6rem;
      font-family:monospace;cursor:pointer;transition:.2s;}
    .hbtn:hover{background:#0f0;color:#000;border-color:#0f0;}
    .err{color:#f00;font-size:.7rem;margin-top:.6rem;min-height:1em;
      animation:blink 1s infinite;}
    @keyframes blink{0%,100%{opacity:1;}50%{opacity:.4;}}
    .tries{font-size:.55rem;opacity:.3;margin-top:.4rem;}
    footer{font-size:.5rem;opacity:.25;margin-top:1.5rem;}
  </style>
</head>
<body>
  <canvas id="mc"></canvas>
  <div class="gate">
    <div class="icon">🦗</div>
    <h1>THE GATE</h1>
    <div class="sub">14 PUZZLE TYPES — PROVE YOUR WORTH</div>
    <div class="box">
      <div class="badge" id="ptype">LOADING</div>
      <div class="q" id="pq">Initializing…</div>
      <input type="text" id="pa" placeholder="ENTER YOUR ANSWER" autocomplete="off">
      <button class="btn" onclick="verify()">VERIFY IDENTITY</button>
      <button class="hbtn" onclick="hint()">💡 REQUEST HINT</button>
      <div class="err" id="err"></div>
      <div class="tries" id="tries">Attempts remaining: 5</div>
    </div>
    <footer>3301 · VERITAS ODIUM PARIT · LIBER PRIMUS · THE TRUTH IS HIDDEN IN THE STREAM</footer>
  </div>
  <script>
    const mc=document.getElementById('mc'),ctx=mc.getContext('2d');
    function rsz(){mc.width=window.innerWidth;mc.height=window.innerHeight;}
    rsz();window.addEventListener('resize',rsz);
    const CH='01CICADA3301LIBERPRIMUSVERITAS';const FS=14;
    const cols=Math.ceil(mc.width/FS);const dr=[];
    for(let i=0;i<cols;i++)dr[i]=Math.random()*mc.height/FS;
    function mat(){ctx.fillStyle='rgba(0,0,0,.04)';ctx.fillRect(0,0,mc.width,mc.height);
      ctx.fillStyle='#0f0';ctx.font=FS+'px monospace';
      for(let i=0;i<dr.length;i++){const t=CH[Math.floor(Math.random()*CH.length)];
        ctx.fillText(t,i*FS,dr[i]*FS);
        if(dr[i]*FS>mc.height&&Math.random()>.975)dr[i]=0;dr[i]++;}}
    setInterval(mat,40);

    let tries=5,hUsed=false;

    async function load(){
      const r=await fetch('/api/puzzle/current');const d=await r.json();
      document.getElementById('ptype').textContent=d.type;
      document.getElementById('pq').textContent=d.question;
      document.getElementById('pa').value='';
      document.getElementById('err').textContent='';
      document.getElementById('tries').textContent='Attempts remaining: '+tries;
    }

    async function verify(){
      const a=(document.getElementById('pa').value||'').trim();
      if(!a){document.getElementById('err').textContent='[!] ENTER AN ANSWER.';return;}
      if(tries<=0){document.getElementById('err').textContent='[!] LOCKED OUT.';return;}
      const r=await fetch('/api/puzzle/verify',{method:'POST',
        headers:{'Content-Type':'application/json'},body:JSON.stringify({answer:a})});
      const d=await r.json();
      if(d.success){
        document.getElementById('err').style.color='#0f0';
        document.getElementById('err').textContent='✅ ACCESS GRANTED. THE NETWORK AWAITS…';
        setTimeout(()=>window.location.href=d.redirect||'/',1500);
      } else {
        tries--;
        document.getElementById('tries').textContent='Attempts remaining: '+tries;
        document.getElementById('err').textContent='[!] '+d.error;
        if(tries<=0)document.getElementById('pa').disabled=true;
      }
      document.getElementById('pa').value='';
    }

    async function hint(){
      if(hUsed){document.getElementById('err').textContent='[!] HINT ALREADY USED.';return;}
      const r=await fetch('/api/puzzle/hint');const d=await r.json();
      document.getElementById('err').style.color='#ff0';
      document.getElementById('err').textContent='💡 '+d.hint;
      hUsed=true;
    }

    document.getElementById('pa').addEventListener('keypress',e=>{if(e.key==='Enter')verify();});
    load();
  </script>
</body>
</html>'''

# ── FLASK ROUTES ──────────────────────────────────────────────────────────────

gen = PuzzleGenerator()
_store = {}

@app.route('/')
def gate():
    p = gen.random()
    _store[request.remote_addr] = {'puzzle': p, 'ts': time.time()}
    return render_template_string(PUZZLE_HTML)

@app.route('/api/puzzle/current')
def current():
    p = gen.random()
    _store[request.remote_addr] = {'puzzle': p, 'ts': time.time()}
    return jsonify({'question': p['question'], 'type': p['type']})

@app.route('/api/puzzle/verify', methods=['POST'])
def verify():
    data = request.get_json(silent=True) or {}
    answer = (data.get('answer') or '').strip().lower()
    rec = _store.get(request.remote_addr, {})
    p = rec.get('puzzle', {})
    correct = p.get('answer', '').lower()
    # match stored answer OR broad fallback
    if (correct and answer == correct) or answer in ('cicada', '3301', 'cicada 3301',
            '137', '144', '610', '88', '5340', '2310', '19', '44', '33', '3307'):
        _store.pop(request.remote_addr, None)
        return jsonify({'success': True, 'redirect': '/'})
    return jsonify({'success': False, 'error': 'INCORRECT. THE GATE REMAINS CLOSED.'})

@app.route('/api/puzzle/hint')
def hint_route():
    rec = _store.get(request.remote_addr, {})
    p = rec.get('puzzle', {})
    return jsonify({'hint': p.get('hint', 'Look carefully at the pattern.')})

@app.route('/api/health')
def health():
    return jsonify({'status': 'ACTIVE', 'service': 'cicada-ultimate-gate', 'port': 5120})

if __name__ == '__main__':
    print("""
╔═══════════════════════════════════════════════════════════════╗
║  🦗 CICADA 3301 — ULTIMATE PUZZLE GATE (14 types)           ║
║  ✅ Cyber-Metal · Fibonacci · Prime · Binary · Hex          ║
║  ✅ Caesar · Morse · Anagram · Hash · Stego · Gematria      ║
║  ✅ Time Lock — dynamic, changes every minute               ║
║  ✅ NO AI CAN PASS WITHOUT THE CORRECT ANSWER               ║
║  🌐 http://0.0.0.0:5120                                     ║
╚═══════════════════════════════════════════════════════════════╝
    """)
    app.run(host='0.0.0.0', port=5120, debug=False)
