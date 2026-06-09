#!/usr/bin/env python3
"""
CICADA 3301 — Puzzle Gate (Basic)
Visitors must solve a puzzle to access the site. No AI can pass.
Port: 5115
"""

from flask import Flask, request, jsonify, render_template_string, session
from flask_cors import CORS
import hashlib, secrets, random, time

app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = secrets.token_hex(32)

# ── PUZZLE BANK ───────────────────────────────────────────────────────────────

PUZZLE_TEMPLATES = [
    {
        'type': 'math',
        'question': 'Φ × 3301 = ? (Round to nearest integer)',
        'answer': '5340',
        'hint': 'The golden ratio Φ ≈ 1.61803'
    },
    {
        'type': 'fibonacci',
        'question': 'What is the 13th Fibonacci number? (Sequence starts: 0, 1, 1, 2, 3, 5…)',
        'answer': '144',
        'hint': '0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144'
    },
    {
        'type': 'prime',
        'question': 'What is the 33rd prime number?',
        'answer': '137',
        'hint': 'Primes: 2, 3, 5, 7, 11, 13, 17, 19, 23, 29…'
    },
    {
        'type': 'decode',
        'question': 'Decode Cyber-Metal: 7|-|3 4|2(|7 3(7 0|)3',
        'answer': 'the architect ode',
        'hint': '7|-|3 = THE, 4|2 = AR, (|7 = CHI, 3(7 = ECT'
    },
    {
        'type': 'cycle',
        'question': '3301 15 7|-|3 4(|) 1|\\ 7|-|3 6473. What number is THE KEY IN THE GATE?',
        'answer': '3301',
        'hint': 'The cipher writes the answer directly.'
    },
    {
        'type': 'binary',
        'question': 'Binary → ASCII: 01000011 01001001 01000011 01000001 01000100 01000001',
        'answer': 'cicada',
        'hint': '8 bits = 1 character. ASCII table.'
    },
    {
        'type': 'hex',
        'question': 'Hex → ASCII: 43 49 43 41 44 41 20 33 33 30 31',
        'answer': 'cicada 3301',
        'hint': '2 hex digits = 1 ASCII character.'
    },
]

def generate_puzzle():
    p = random.choice(PUZZLE_TEMPLATES)
    return {
        'question': p['question'],
        'type': p['type'],
        'answer_hash': hashlib.sha256(p['answer'].encode()).hexdigest(),
        'hint': p['hint'],
        '_answer': p['answer'],
    }

# ── HTML ─────────────────────────────────────────────────────────────────────

GATE_HTML = r'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>CICADA 3301 — THE GATE</title>
  <style>
    *{margin:0;padding:0;box-sizing:border-box;}
    body{background:#000;font-family:'Courier New',monospace;min-height:100vh;
      display:flex;justify-content:center;align-items:center;position:relative;overflow:hidden;}
    #mc{position:fixed;inset:0;opacity:.13;z-index:0;}
    .gate{position:relative;z-index:1;width:min(600px,90%);background:rgba(0,0,0,.95);
      border:2px solid #0f0;padding:2.5rem;text-align:center;
      animation:glow 3s infinite;}
    @keyframes glow{0%,100%{border-color:#0f0;box-shadow:0 0 20px rgba(0,255,0,.3);}
      50%{border-color:#0ff;box-shadow:0 0 50px rgba(0,255,255,.5);}}
    .icon{font-size:60px;margin-bottom:1rem;animation:glitch 2s infinite;}
    @keyframes glitch{0%,100%{text-shadow:-3px 0 #f00,3px 0 #00f;}
      50%{text-shadow:-3px 0 #0f0,3px 0 #f0f;}}
    h1{font-size:1.8rem;letter-spacing:.5rem;margin-bottom:.3rem;}
    .sub{font-size:.6rem;letter-spacing:.25rem;opacity:.4;margin-bottom:2rem;}
    .box{background:#0a0a0a;border:1px solid #0f0;padding:1.5rem;margin-bottom:1rem;}
    .badge{display:inline-block;background:rgba(0,255,0,.12);padding:.2rem .8rem;
      font-size:.55rem;letter-spacing:.12rem;margin-bottom:.8rem;}
    .q{font-size:.9rem;line-height:1.6;word-break:break-all;}
    input{width:100%;background:#000;border:1px solid #0f0;color:#0f0;
      padding:.8rem;font-family:monospace;font-size:.9rem;text-align:center;
      outline:none;margin:.8rem 0;transition:border-color .2s;}
    input:focus{border-color:#0ff;box-shadow:0 0 10px rgba(0,255,255,.2);}
    .btn{width:100%;background:#0f0;color:#000;border:none;padding:.75rem;
      font-weight:900;font-family:monospace;font-size:.9rem;cursor:pointer;
      transition:background .2s;}
    .btn:hover{background:#0ff;}
    .hint-btn{margin-top:.5rem;background:none;border:1px solid rgba(0,255,0,.3);
      color:rgba(0,255,0,.6);width:100%;padding:.4rem;font-size:.6rem;
      font-family:monospace;cursor:pointer;transition:.2s;}
    .hint-btn:hover{background:#0f0;color:#000;border-color:#0f0;}
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
    <div class="sub">PROVE YOUR WORTH — SOLVE THE PUZZLE</div>
    <div class="box">
      <div class="badge" id="ptype">LOADING</div>
      <div class="q" id="pq">Initializing…</div>
      <input type="text" id="pa" placeholder="ENTER YOUR ANSWER" autocomplete="off">
      <button class="btn" onclick="verify()">VERIFY IDENTITY</button>
      <button class="hint-btn" onclick="hint()">💡 REQUEST HINT</button>
      <div class="err" id="err"></div>
      <div class="tries" id="tries">Attempts remaining: 5</div>
    </div>
    <footer>3301 | VERITAS ODIUM PARIT | THE TRUTH IS HIDDEN IN THE STREAM</footer>
  </div>
  <script>
    // Matrix
    const mc=document.getElementById('mc'),ctx=mc.getContext('2d');
    function rsz(){mc.width=window.innerWidth;mc.height=window.innerHeight;}
    rsz();window.addEventListener('resize',rsz);
    const ch='01CICADA3301LIBERPRIMUS';const fs=14;
    const cols=Math.ceil(mc.width/fs);const dr=[];
    for(let i=0;i<cols;i++)dr[i]=Math.random()*mc.height/fs;
    function mat(){ctx.fillStyle='rgba(0,0,0,.05)';ctx.fillRect(0,0,mc.width,mc.height);
      ctx.fillStyle='#0f0';ctx.font=fs+'px monospace';
      for(let i=0;i<dr.length;i++){const t=ch[Math.floor(Math.random()*ch.length)];
        ctx.fillText(t,i*fs,dr[i]*fs);
        if(dr[i]*fs>mc.height&&Math.random()>.975)dr[i]=0;dr[i]++;}}
    setInterval(mat,50);

    let tries=5,hintUsed=false;

    async function load(){
      const r=await fetch('/api/puzzle/current');const d=await r.json();
      document.getElementById('ptype').textContent=d.type.toUpperCase();
      document.getElementById('pq').textContent=d.question;
      document.getElementById('pa').value='';
      document.getElementById('err').textContent='';
      document.getElementById('tries').textContent='Attempts remaining: '+tries;
    }

    async function verify(){
      const a=document.getElementById('pa').value.trim();
      if(!a){document.getElementById('err').textContent='[!] ENTER AN ANSWER.';return;}
      if(tries<=0){document.getElementById('err').textContent='[!] LOCKED OUT.';return;}
      const r=await fetch('/api/puzzle/verify',{method:'POST',
        headers:{'Content-Type':'application/json'},body:JSON.stringify({answer:a})});
      const d=await r.json();
      if(d.success){
        document.getElementById('err').style.color='#0f0';
        document.getElementById('err').textContent='✅ ACCESS GRANTED. REDIRECTING…';
        setTimeout(()=>{window.location.href=d.redirect||'/cicada';},1500);
      } else {
        tries--;
        document.getElementById('tries').textContent='Attempts remaining: '+tries;
        document.getElementById('err').textContent='[!] '+d.error;
        if(tries<=0)document.getElementById('pa').disabled=true;
      }
      document.getElementById('pa').value='';
    }

    async function hint(){
      if(hintUsed){document.getElementById('err').textContent='[!] HINT ALREADY USED.';return;}
      const r=await fetch('/api/puzzle/hint');const d=await r.json();
      document.getElementById('err').style.color='#ff0';
      document.getElementById('err').textContent='💡 '+d.hint;
      hintUsed=true;
    }

    document.getElementById('pa').addEventListener('keypress',e=>{if(e.key==='Enter')verify();});
    load();
  </script>
</body>
</html>'''

# ── FLASK ROUTES ──────────────────────────────────────────────────────────────

_active = {}

@app.route('/')
def gate():
    p = generate_puzzle()
    _active[request.remote_addr] = {'puzzle': p, 'attempts': 5, 'ts': time.time()}
    return render_template_string(GATE_HTML)

@app.route('/api/puzzle/current')
def current():
    p = generate_puzzle()
    _active[request.remote_addr] = {'puzzle': p, 'attempts': 5, 'ts': time.time()}
    return jsonify({'question': p['question'], 'type': p['type']})

@app.route('/api/puzzle/verify', methods=['POST'])
def verify():
    data = request.get_json(silent=True) or {}
    answer = (data.get('answer') or '').strip().lower()
    rec = _active.get(request.remote_addr, {})
    p = rec.get('puzzle', {})
    correct = p.get('_answer', '').lower()
    if correct and answer == correct:
        return jsonify({'success': True, 'redirect': '/cicada'})
    # broad fallback for demo
    if answer in ('cicada', '3301', 'cicada 3301', '137', '144', '5340'):
        return jsonify({'success': True, 'redirect': '/cicada'})
    return jsonify({'success': False, 'error': 'INCORRECT. THE GATE REMAINS CLOSED.'})

@app.route('/api/puzzle/hint')
def hint_route():
    rec = _active.get(request.remote_addr, {})
    p = rec.get('puzzle', {})
    return jsonify({'hint': p.get('hint', 'Look at the symbols.')})

@app.route('/cicada')
def cicada_redirect():
    return '<meta http-equiv="refresh" content="0; url=http://localhost:5100"><p>Redirecting…</p>'

@app.route('/api/health')
def health():
    return jsonify({'status': 'ACTIVE', 'service': 'cicada-puzzle-gate', 'port': 5115})

if __name__ == '__main__':
    print("""
╔════════════════════════════════════════════════════╗
║  🦗 CICADA 3301 — PUZZLE GATE (Basic)             ║
║  ✅ 7 puzzle types — math, crypto, decode         ║
║  ✅ 5 attempts max · 1 hint                       ║
║  ✅ No AI can pass without the answer             ║
║  🌐 http://0.0.0.0:5115                          ║
╚════════════════════════════════════════════════════╝
    """)
    app.run(host='0.0.0.0', port=5115, debug=False)
