#!/usr/bin/env python3
"""
CICADA 3301 - THE LIBER PRIMUS
Design identic cu modelul nostru (small cicada badge, flying cicadas, glitch, color cycling)
+ Flask backend cu DB, leaderboard, user system, puzzle verification
"""

from flask import Flask, request, jsonify, render_template_string
import hashlib
import secrets
import json
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(32)

# ============================================
# BAZĂ DATE
# ============================================

DB_PATH = '/var/lib/jarvis/cicada_3301.db'

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS cicada_users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        wallet TEXT,
        total_points INTEGER DEFAULT 0,
        total_rewards_xmr REAL DEFAULT 0.0,
        solved_puzzles TEXT DEFAULT '[]',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS cicada_solves (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        puzzle_id TEXT,
        solved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    conn.commit()
    conn.close()

init_db()

# ============================================
# PUZZLE-URI (8 levels, Beginner -> Mythic)
# ============================================

PUZZLES = {
    'initiation': {
        'id': 1, 'name': 'Initiation', 'difficulty': 'Beginner',
        'reward_xmr': 0.01, 'points': 100, 'time': '24h', 'category': 'Cryptography',
        'description': 'Decode: "01001101 01101111 01101110 01100101 01110010 01101111"',
        'hint': 'Binary to text',
        'answer_hash': hashlib.sha256(b'Monero').hexdigest()
    },
    'caesar': {
        'id': 2, 'name': "Caesar's Truth", 'difficulty': 'Easy',
        'reward_xmr': 0.02, 'points': 200, 'time': '48h', 'category': 'Classical Cipher',
        'description': 'L FDPH, L VDZ, L FRQTXHUHG. Cipher: VQREWLVDQD',
        'hint': 'ROT13 is everywhere. 3301.',
        'answer_hash': hashlib.sha256(b'I came, I saw, I conquered').hexdigest()
    },
    'primus': {
        'id': 3, 'name': 'Liber Primus', 'difficulty': 'Medium',
        'reward_xmr': 0.05, 'points': 500, 'time': '72h', 'category': 'Runes',
        'description': 'Runestones: F U Th A R Ka G W H N I J P I X S T B E M L Ng D O',
        'hint': 'Elder Futhark runes. The answer is 3 words.',
        'answer_hash': hashlib.sha256(b'We are everywhere').hexdigest()
    },
    'rsa': {
        'id': 4, 'name': 'RSA Secret', 'difficulty': 'Hard',
        'reward_xmr': 0.10, 'points': 1000, 'time': '120h', 'category': 'Modern Crypto',
        'description': 'n = 3233, e = 17, ciphertext = 2790. Decrypt the message.',
        'hint': 'p = 53, q = 61',
        'answer_hash': hashlib.sha256(b'rsa').hexdigest()
    },
    'stegano': {
        'id': 5, 'name': 'Hidden Image', 'difficulty': 'Expert',
        'reward_xmr': 0.25, 'points': 2500, 'time': '168h', 'category': 'Steganography',
        'description': 'The image contains a secret. LSB steganography. Extract from blue channel.',
        'hint': 'Least significant bits.',
        'answer_hash': hashlib.sha256(b'cicada3301').hexdigest()
    },
    'chain': {
        'id': 6, 'name': 'Blockchain Trail', 'difficulty': 'Expert',
        'reward_xmr': 0.50, 'points': 5000, 'time': '240h', 'category': 'Blockchain',
        'description': 'Follow the Monero trail through the darknet nodes.',
        'hint': 'The answer is in the blockchain comments.',
        'answer_hash': hashlib.sha256(b'privacy is freedom').hexdigest()
    },
    'quantum': {
        'id': 7, 'name': 'Quantum Maze', 'difficulty': 'Legendary',
        'reward_xmr': 1.00, 'points': 10000, 'time': '336h', 'category': 'Quantum',
        'description': 'Qubit states: |0>, |1>, |+>, |->. Circuit: H, CNOT, H. Measure.',
        'hint': 'Bell state. 4-letter word.',
        'answer_hash': hashlib.sha256(b'bell').hexdigest()
    },
    'prophecy': {
        'id': 8, "name": "Cicada's Prophecy", 'difficulty': 'Mythic',
        'reward_xmr': 2.50, 'points': 25000, 'time': '720h', 'category': 'Mystery',
        'description': 'LK2@#8$n!9$#KJ@!$#@L:>{">?<L":{P{">?<L":@!$#KJ@!$#LK@LK@LK@3301',
        'hint': 'XOR with 3301.',
        'answer_hash': hashlib.sha256(b'liber primus').hexdigest()
    }
}

# ============================================
# ENDPOINT-URI
# ============================================

@app.route('/')
def index():
    return render_template_string(CICADA_HTML)

@app.route('/api/puzzles', methods=['GET'])
def get_puzzles():
    return jsonify(PUZZLES)

@app.route('/api/submit', methods=['POST'])
def submit_answer():
    data = request.json
    puzzle_id = data.get('puzzle_id', '')
    answer = data.get('answer', '').strip()
    username = data.get('username', '').strip()
    wallet = data.get('wallet', '').strip()

    if puzzle_id not in PUZZLES:
        return jsonify({'error': 'Puzzle not found'}), 404
    if not username:
        return jsonify({'error': 'Username required'}), 400

    puzzle = PUZZLES[puzzle_id]
    answer_hash = hashlib.sha256(answer.encode()).hexdigest()

    if answer_hash == puzzle['answer_hash']:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        c.execute("SELECT id, total_points, total_rewards_xmr, solved_puzzles FROM cicada_users WHERE username = ?", (username,))
        user = c.fetchone()

        if user:
            user_id, pts, xmr, solved_json = user
            solved = json.loads(solved_json)
            if puzzle_id not in solved:
                solved.append(puzzle_id)
                c.execute("UPDATE cicada_users SET total_points=?, total_rewards_xmr=?, solved_puzzles=? WHERE id=?",
                          (pts + puzzle['points'], xmr + puzzle['reward_xmr'], json.dumps(solved), user_id))
                c.execute("INSERT INTO cicada_solves (user_id, puzzle_id) VALUES (?, ?)", (user_id, puzzle_id))
                conn.commit()
                conn.close()
                return jsonify({
                    'success': True,
                    'message': f'{puzzle["name"]} solved! +{puzzle["points"]} pts, +{puzzle["reward_xmr"]} XMR',
                    'points': puzzle['points'],
                    'xmr': puzzle['reward_xmr'],
                    'total_points': pts + puzzle['points']
                })
            else:
                conn.close()
                return jsonify({'error': 'Already solved!'}), 400
        else:
            solved = [puzzle_id]
            c.execute("INSERT INTO cicada_users (username, wallet, total_points, total_rewards_xmr, solved_puzzles) VALUES (?,?,?,?,?)",
                      (username, wallet, puzzle['points'], puzzle['reward_xmr'], json.dumps(solved)))
            user_id = c.lastrowid
            c.execute("INSERT INTO cicada_solves (user_id, puzzle_id) VALUES (?, ?)", (user_id, puzzle_id))
            conn.commit()
            conn.close()
            return jsonify({
                'success': True,
                'message': f'Welcome, {username}! {puzzle["name"]} solved! +{puzzle["points"]} pts, +{puzzle["reward_xmr"]} XMR',
                'points': puzzle['points'],
                'xmr': puzzle['reward_xmr'],
                'total_points': puzzle['points']
            })

    return jsonify({'error': 'Incorrect answer. The code awaits decryption.'}), 400

@app.route('/api/leaderboard', methods=['GET'])
def leaderboard():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT username, total_points, total_rewards_xmr, solved_puzzles FROM cicada_users ORDER BY total_points DESC LIMIT 50")
    leaders = []
    for i, row in enumerate(c.fetchall()):
        solved = json.loads(row[3]) if row[3] else []
        leaders.append({'rank': i+1, 'username': row[0], 'points': row[1], 'xmr': round(row[2], 4), 'solved': len(solved)})
    conn.close()
    return jsonify(leaders)

@app.route('/api/stats', methods=['GET'])
def stats():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*), SUM(total_points), SUM(total_rewards_xmr) FROM cicada_users")
    row = c.fetchone()
    conn.close()
    return jsonify({
        'total_solvers': row[0] or 0,
        'total_points': row[1] or 0,
        'total_xmr': round(row[2] or 0, 4)
    })

# ============================================
# HTML - MODELUL NOSTRU EXACT
# (small cicada badge, flying cicadas, glitch, color cycling, slow rain, original sound)
# ============================================

CICADA_HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CICADA 3301</title>
    <meta name="description" content="Cicada 3301 — We are everywhere.">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;600;700;800;900&family=Share+Tech+Mono&display=swap" rel="stylesheet">
    <style>
        *{margin:0;padding:0;box-sizing:border-box}
        html,body{width:100%;height:100%;overflow-x:hidden;background:#000;font-family:'Share Tech Mono',monospace}

        /* ── COLOR CYCLING ── */
        :root{
            --neon:#ff0033;
            --neon-glow:rgba(255,0,51,0.5);
            --neon-dim:rgba(255,0,51,0.25);
            --neon-soft:rgba(255,0,51,0.08);
            --neon-rgb:255,0,51;
        }

        /* Digital Rain Canvas */
        #rain{position:fixed;top:0;left:0;width:100%;height:100%;z-index:0}

        /* Scanline overlay */
        body::after{
            content:'';position:fixed;top:0;left:0;width:100%;height:100%;
            background:repeating-linear-gradient(0deg,transparent,transparent 2px,rgba(255,255,255,0.012) 2px,rgba(255,255,255,0.012) 4px);
            pointer-events:none;z-index:9998;
        }

        /* Subtle grid */
        body::before{
            content:'';position:fixed;top:0;left:0;width:100%;height:100%;
            background-image:linear-gradient(rgba(255,255,255,0.02) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,0.02) 1px,transparent 1px);
            background-size:40px 40px;pointer-events:none;z-index:0;opacity:0.4;
        }

        /* ── GLITCH ── */
        @keyframes glitch{
            0%  {text-shadow:0.05em 0 0 var(--neon),-0.05em -0.025em 0 #ff0033}
            10% {text-shadow:-0.03em 0.02em 0 var(--neon),0.04em -0.01em 0 #ff0033}
            20% {text-shadow:0.02em -0.03em 0 var(--neon),-0.04em 0.01em 0 #ff0033}
            30% {text-shadow:-0.04em 0.01em 0 var(--neon),0.03em -0.02em 0 #ff0033}
            40% {text-shadow:0.03em 0.02em 0 var(--neon),-0.02em -0.03em 0 #ff0033}
            50% {text-shadow:-0.02em -0.01em 0 var(--neon),0.05em 0.03em 0 #ff0033}
            60% {text-shadow:0.04em -0.02em 0 var(--neon),-0.03em 0.01em 0 #ff0033}
            70% {text-shadow:-0.01em 0.03em 0 var(--neon),0.02em -0.04em 0 #ff0033}
            80% {text-shadow:0.05em 0.01em 0 var(--neon),-0.04em -0.02em 0 #ff0033}
            90% {text-shadow:-0.03em -0.03em 0 var(--neon),0.01em 0.02em 0 #ff0033}
            100%{text-shadow:0.02em 0.01em 0 var(--neon),-0.05em -0.025em 0 #ff0033}
        }
        @keyframes glitch-skew{
            0%  {transform:translate(0);clip-path:inset(40% 0 61% 0)}
            20% {transform:translate(-2px,2px);clip-path:inset(92% 0 1% 0)}
            40% {transform:translate(2px,-1px);clip-path:inset(43% 0 1% 0)}
            60% {transform:translate(-1px,-2px);clip-path:inset(25% 0 58% 0)}
            80% {transform:translate(1px,1px);clip-path:inset(54% 0 7% 0)}
            100%{transform:translate(0);clip-path:inset(58% 0 43% 0)}
        }
        @keyframes flicker{0%,100%{opacity:1}92%{opacity:1}93%{opacity:0.4}94%{opacity:1}96%{opacity:0.2}97%{opacity:1}}
        @keyframes pulse-glow{
            0%,100%{box-shadow:0 0 8px var(--neon-dim),inset 0 0 5px var(--neon-soft)}
            50%{box-shadow:0 0 20px var(--neon-glow),inset 0 0 10px var(--neon-dim)}
        }

        /* ── FLYING CICADA ── */
        @keyframes cicada-fly-1{
            0%   {transform:translate(-120px,-80px) rotate(-5deg) scale(0.6);opacity:0}
            8%   {opacity:0.9}
            25%  {transform:translate(25vw,15vh) rotate(3deg) scale(0.8);opacity:1}
            50%  {transform:translate(55vw,40vh) rotate(-8deg) scale(0.7);opacity:0.8}
            75%  {transform:translate(80vw,20vh) rotate(5deg) scale(0.9);opacity:0.6}
            92%  {opacity:0.3}
            100% {transform:translate(110vw,-50px) rotate(-3deg) scale(0.5);opacity:0}
        }
        @keyframes cicada-fly-2{
            0%   {transform:translate(110vw,30vh) rotate(8deg) scale(0.5);opacity:0}
            8%   {opacity:0.7}
            25%  {transform:translate(75vw,50vh) rotate(-5deg) scale(0.7);opacity:0.9}
            50%  {transform:translate(40vw,25vh) rotate(10deg) scale(0.8);opacity:0.7}
            75%  {transform:translate(15vw,55vh) rotate(-6deg) scale(0.6);opacity:0.5}
            92%  {opacity:0.2}
            100% {transform:translate(-120px,10vh) rotate(4deg) scale(0.4);opacity:0}
        }
        @keyframes wing-flap{0%,100%{transform:scaleY(1)}25%{transform:scaleY(0.85)}50%{transform:scaleY(1.1)}75%{transform:scaleY(0.9)}}
        .flying-cicada{position:fixed;z-index:100;pointer-events:none;filter:drop-shadow(0 0 6px var(--neon-glow));transition:filter 0.6s}
        .flying-cicada svg{width:60px;height:60px}
        .flying-cicada .wing-l,.flying-cicada .wing-r{animation:wing-flap 0.12s ease-in-out infinite;transform-origin:center top}
        #flyCicada1{top:5%;left:0;animation:cicada-fly-1 18s linear infinite;animation-delay:2s}
        #flyCicada2{top:10%;right:0;animation:cicada-fly-2 22s linear infinite;animation-delay:8s}

        /* ── HERO ── */
        .hero{position:relative;z-index:1;display:flex;flex-direction:column;align-items:center;justify-content:center;min-height:100vh;padding:20px;text-align:center}
        .tag{position:fixed;top:16px;left:20px;z-index:10;font-size:0.7rem;color:var(--neon-dim);letter-spacing:2px;text-transform:uppercase;opacity:0.7;transition:color 0.6s}

        /* ── CICADA 3301 GLITCH TITLE ── */
        .hero h1{
            font-family:'Orbitron',sans-serif;font-size:clamp(1.6rem,5vw,3rem);font-weight:900;
            color:var(--neon);letter-spacing:clamp(6px,1.5vw,14px);text-transform:uppercase;
            text-shadow:0 0 8px var(--neon-glow),0 0 20px var(--neon-glow),0 0 40px var(--neon-dim),0 0 80px var(--neon-soft);
            animation:glitch 3s infinite,flicker 5s infinite;margin-bottom:8px;position:relative;
            transition:color 0.6s,text-shadow 0.6s;
        }
        .hero h1::before,.hero h1::after{
            content:'CICADA 3301';position:absolute;top:0;left:0;width:100%;height:100%;
            font-family:inherit;font-size:inherit;font-weight:inherit;letter-spacing:inherit;text-transform:inherit;transition:color 0.6s;
        }
        .hero h1::before{color:#ff0033;animation:glitch-skew 4s infinite linear alternate-reverse;clip-path:inset(20% 0 80% 0);opacity:0.6}
        .hero h1::after{color:var(--neon);animation:glitch-skew 3s infinite linear alternate;clip-path:inset(60% 0 10% 0);opacity:0.4}

        .hero .sub{font-size:clamp(0.55rem,1.2vw,0.75rem);color:var(--neon-dim);letter-spacing:3px;text-transform:uppercase;margin-bottom:20px;line-height:1.6;transition:color 0.6s}
        .good-luck{font-family:'Orbitron',sans-serif;font-size:clamp(1.4rem,4vw,2.8rem);font-weight:800;color:#ff0033;letter-spacing:clamp(6px,1.5vw,12px);text-transform:uppercase;-webkit-text-stroke:1px #000;text-shadow:0 0 15px rgba(255,0,51,0.6),0 0 30px rgba(255,0,51,0.3),2px 2px 0 #000,-1px -1px 0 #000;animation:flicker 6s infinite;margin-bottom:20px}
        .everywhere-box{display:inline-block;border:1.5px solid var(--neon);border-radius:6px;padding:10px 35px;margin-bottom:15px;background:rgba(0,0,0,0.3);animation:pulse-glow 4s ease-in-out infinite;transition:border-color 0.6s,box-shadow 0.6s}
        .everywhere-box span{font-family:'Orbitron',sans-serif;font-size:clamp(0.9rem,2.5vw,1.6rem);font-weight:700;color:#fff;letter-spacing:clamp(6px,2vw,15px);text-transform:uppercase}
        .three-three-oh-one{font-family:'Orbitron',sans-serif;font-size:clamp(0.9rem,2vw,1.4rem);font-weight:700;color:var(--neon);letter-spacing:clamp(8px,2vw,14px);text-shadow:0 0 12px var(--neon-glow),0 0 25px var(--neon-dim);margin-bottom:25px;transition:color 0.6s,text-shadow 0.6s}

        /* ── STATS BAR ── */
        .stats-bar{position:relative;z-index:1;display:flex;justify-content:center;gap:40px;padding:20px;margin:0 auto;max-width:800px;flex-wrap:wrap}
        .stat{text-align:center}
        .stat-label{font-size:0.6rem;color:var(--neon-dim);letter-spacing:3px;text-transform:uppercase;margin-bottom:5px;transition:color 0.6s}
        .stat-value{font-family:'Orbitron',sans-serif;font-size:1.4rem;font-weight:700;color:var(--neon);text-shadow:0 0 10px var(--neon-glow);transition:color 0.6s}

        /* ── SMALL CICADA BADGE ── */
        .cicada-badge{position:fixed;bottom:30px;right:30px;z-index:10;width:80px;height:80px;border:1.5px solid var(--neon-dim);border-radius:50%;display:flex;justify-content:center;align-items:center;background:rgba(0,0,0,0.6);box-shadow:0 0 15px var(--neon-soft),inset 0 0 8px var(--neon-soft);animation:pulse-glow 5s ease-in-out infinite;transition:border-color 0.6s,box-shadow 0.6s}
        .cicada-badge svg{width:55px;height:55px;filter:drop-shadow(0 0 4px var(--neon-glow));transition:filter 0.6s}
        .cicada-badge svg *{transition:stroke 0.6s,fill 0.6s}

        /* ── LOGIN ── */
        .login-section{position:relative;z-index:1;text-align:center;padding:30px;max-width:600px;margin:0 auto 20px;border:1px solid var(--neon-dim);border-radius:5px;background:rgba(0,0,0,0.5);transition:border-color 0.6s}
        .login-section input{background:rgba(0,0,0,0.6);border:1px solid var(--neon-dim);color:var(--neon);padding:10px 14px;font-family:'Share Tech Mono',monospace;font-size:0.85rem;border-radius:3px;margin:5px;outline:none;width:260px;transition:border-color 0.3s}
        .login-section input:focus{border-color:var(--neon);box-shadow:0 0 6px var(--neon-soft)}
        .login-section input::placeholder{color:rgba(255,255,255,0.12)}
        .btn-enter{background:var(--neon);color:#000;border:none;font-family:'Orbitron',sans-serif;font-size:0.7rem;font-weight:700;letter-spacing:2px;cursor:pointer;border-radius:3px;padding:12px 30px;margin-top:8px;transition:all 0.3s}
        .btn-enter:hover{box-shadow:0 0 15px var(--neon-glow);transform:translateY(-1px)}
        .user-info{position:relative;z-index:1;text-align:center;padding:10px;font-size:0.8rem;color:var(--neon);letter-spacing:2px;transition:color 0.6s}
        .btn-logout{background:transparent;color:#ff6600;border:1px solid #ff6600;font-family:'Share Tech Mono',monospace;font-size:0.65rem;cursor:pointer;border-radius:3px;padding:6px 12px;margin-left:10px;transition:all 0.3s}
        .btn-logout:hover{background:#ff6600;color:#000}

        /* ── PUZZLES ── */
        .puzzles{position:relative;z-index:1;max-width:1100px;margin:0 auto;padding:20px 20px 50px}
        .sec-label{font-family:'Orbitron',sans-serif;font-size:0.85rem;color:var(--neon);letter-spacing:5px;text-transform:uppercase;text-align:center;margin-bottom:25px;text-shadow:0 0 8px var(--neon-glow);transition:color 0.6s}
        .pgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:14px}
        .pcard{background:rgba(0,0,0,0.7);border:1px solid var(--neon-dim);border-radius:5px;padding:18px;cursor:pointer;transition:all 0.3s;position:relative;overflow:hidden}
        .pcard::before{content:'';position:absolute;top:0;left:0;width:100%;height:2px;background:linear-gradient(90deg,transparent,var(--neon),transparent);opacity:0;transition:opacity 0.3s}
        .pcard:hover{border-color:var(--neon);transform:translateY(-2px);box-shadow:0 4px 20px var(--neon-soft)}
        .pcard:hover::before{opacity:1}
        .pcard.solved{border-color:#ffd700;background:rgba(255,215,0,0.03)}
        .pc-lvl{font-family:'Orbitron',sans-serif;font-size:0.5rem;color:var(--neon-dim);letter-spacing:3px;text-transform:uppercase;margin-bottom:5px}
        .pc-nm{font-family:'Orbitron',sans-serif;font-size:0.85rem;font-weight:700;color:var(--neon);margin-bottom:5px;text-shadow:0 0 5px var(--neon-glow);transition:color 0.6s}
        .pc-df{display:inline-block;font-size:0.55rem;padding:2px 7px;border-radius:10px;margin-bottom:7px;font-weight:600;letter-spacing:1px;text-transform:uppercase}
        .df-beginner{background:rgba(0,255,102,0.1);color:#00ff66;border:1px solid rgba(0,255,102,0.2)}
        .df-easy{background:rgba(0,255,255,0.08);color:#00ffff;border:1px solid rgba(0,255,255,0.15)}
        .df-medium{background:rgba(255,204,0,0.08);color:#ffcc00;border:1px solid rgba(255,204,0,0.15)}
        .df-hard{background:rgba(255,102,0,0.08);color:#ff6600;border:1px solid rgba(255,102,0,0.15)}
        .df-expert{background:rgba(255,0,51,0.08);color:#ff0033;border:1px solid rgba(255,0,51,0.15)}
        .df-legendary{background:rgba(204,0,255,0.08);color:#cc00ff;border:1px solid rgba(204,0,255,0.15)}
        .df-mythic{background:rgba(204,0,255,0.12);color:#cc00ff;border:1px solid rgba(204,0,255,0.25);text-shadow:0 0 4px rgba(204,0,255,0.4)}
        .pc-ds{font-size:0.68rem;color:rgba(255,255,255,0.4);line-height:1.4;margin-bottom:8px}
        .pc-rw{font-size:0.65rem;color:#ffd700}
        .pc-mt{display:flex;justify-content:space-between;margin-top:6px;font-size:0.55rem;color:var(--neon-dim);opacity:0.5}

        /* ── LEADERBOARD ── */
        .lb{max-width:700px;margin:30px auto;background:rgba(0,0,0,0.6);border:1px solid var(--neon-dim);border-radius:5px;padding:18px;max-height:280px;overflow-y:auto;transition:border-color 0.6s}
        .lb h3{font-family:'Orbitron',sans-serif;color:#ffd700;font-size:0.75rem;letter-spacing:3px;text-align:center;margin-bottom:10px}
        .lbr{display:flex;justify-content:space-between;padding:5px 8px;border-bottom:1px solid rgba(255,255,255,0.02);font-size:0.7rem}
        .lbr:hover{background:rgba(255,255,255,0.02)}
        .lbr-r{font-weight:700;min-width:30px}
        .lbr-1{color:#ffd700;text-shadow:0 0 5px rgba(255,215,0,0.4)}
        .lbr-2{color:#c0c0c0}.lbr-3{color:#cd7f32}
        .lbr-n{flex:1;color:rgba(255,255,255,0.6)}
        .lbr-p{color:var(--neon);transition:color 0.6s}

        /* ── TELEGRAM ── */
        .tgb{text-align:center;margin:25px auto;max-width:460px;padding:18px;border:1px solid var(--neon-dim);border-radius:5px;background:rgba(0,0,0,0.5);transition:border-color 0.6s}
        .tgb p{font-size:0.7rem;color:rgba(255,255,255,0.35);margin-bottom:10px;letter-spacing:2px;text-transform:uppercase}
        .tgl{display:inline-flex;align-items:center;gap:7px;padding:9px 22px;border:1px solid var(--neon);color:var(--neon);font-family:'Orbitron',sans-serif;font-size:0.7rem;font-weight:600;letter-spacing:2px;text-decoration:none;border-radius:3px;transition:all 0.3s}
        .tgl:hover{background:var(--neon);color:#000;box-shadow:0 0 15px var(--neon-glow)}

        /* ── FOOTER ── */
        .ft{text-align:center;padding:25px 20px;font-family:'Orbitron',sans-serif;font-size:0.5rem;color:var(--neon-dim);letter-spacing:2px;opacity:0.4;transition:color 0.6s}
        .ft .xmr{font-size:0.45rem;color:rgba(255,255,255,0.12);margin-top:6px;word-break:break-all}

        /* ── MODAL ── */
        .mbg{display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.95);z-index:5000;justify-content:center;align-items:center}
        .mbg.active{display:flex}
        .mbox{background:#050505;border:1px solid var(--neon);border-radius:6px;padding:24px;max-width:480px;width:90%;box-shadow:0 0 30px var(--neon-dim);transition:border-color 0.6s}
        .mbox h3{font-family:'Orbitron',sans-serif;color:var(--neon);font-size:0.8rem;letter-spacing:3px;margin-bottom:10px;text-shadow:0 0 6px var(--neon-glow);transition:color 0.6s}
        .mbox .md{color:rgba(255,255,255,0.45);font-size:0.75rem;line-height:1.5;margin-bottom:6px;padding:8px;background:rgba(0,0,0,0.5);border:1px solid rgba(255,255,255,0.04);border-radius:3px}
        .mbox .mr{color:#ffd700;font-size:0.75rem;margin-bottom:10px}
        .mbox input,.mbox textarea{width:100%;background:rgba(0,0,0,0.6);border:1px solid var(--neon-dim);color:var(--neon);padding:8px 10px;font-family:'Share Tech Mono',monospace;font-size:0.78rem;border-radius:3px;margin-bottom:6px;outline:none;transition:border-color 0.3s}
        .mbox input:focus,.mbox textarea:focus{border-color:var(--neon);box-shadow:0 0 6px var(--neon-soft)}
        .mbox input::placeholder,.mbox textarea::placeholder{color:rgba(255,255,255,0.12)}
        .mbs{display:flex;gap:6px;margin-top:3px}
        .btn-s{flex:1;padding:9px;background:var(--neon);color:#000;border:none;font-family:'Orbitron',sans-serif;font-size:0.65rem;font-weight:700;letter-spacing:2px;cursor:pointer;border-radius:3px;transition:all 0.3s}
        .btn-s:hover{box-shadow:0 0 12px var(--neon-glow);transform:translateY(-1px)}
        .btn-h{padding:9px 12px;background:transparent;color:#ff6600;border:1px solid #ff6600;font-family:'Orbitron',sans-serif;font-size:0.55rem;font-weight:600;letter-spacing:1px;cursor:pointer;border-radius:3px;transition:all 0.3s}
        .btn-h:hover{background:#ff6600;color:#000}
        .btn-c{padding:9px 12px;background:transparent;color:rgba(255,255,255,0.25);border:1px solid rgba(255,255,255,0.08);font-size:0.65rem;cursor:pointer;border-radius:3px}

        /* ── SOUND TOGGLE ── */
        .st{position:fixed;bottom:16px;right:120px;z-index:500;width:34px;height:34px;background:rgba(0,0,0,0.8);border:1px solid var(--neon-dim);border-radius:50%;display:flex;justify-content:center;align-items:center;cursor:pointer;transition:all 0.3s;font-size:1rem}
        .st:hover{border-color:var(--neon);box-shadow:0 0 10px var(--neon-dim)}
        .st.muted{opacity:0.3}

        /* ── RESPONSIVE ── */
        @media(max-width:768px){
            .pgrid{grid-template-columns:1fr}
            .lb,.tgb{margin:18px 12px}
            .cicada-badge{width:60px;height:60px;bottom:15px;right:15px}
            .cicada-badge svg{width:40px;height:40px}
            .tag{font-size:0.55rem;top:8px;left:10px}
            .st{right:90px}
            .flying-cicada svg{width:40px;height:40px}
            .stats-bar{gap:20px}
        }
    </style>
</head>
<body>

<canvas id="rain"></canvas>
<div class="tag">@proplanwh</div>
<div class="st" id="sndBtn" onclick="toggleSound()">&#x1F997;</div>

<!-- FLYING CICADA 1 -->
<div class="flying-cicada" id="flyCicada1">
    <svg viewBox="0 0 200 200" fill="none" xmlns="http://www.w3.org/2000/svg">
        <circle cx="100" cy="55" r="12" stroke="var(--neon)" stroke-width="1.5" fill="none" opacity="0.9"/>
        <circle cx="94" cy="52" r="3" fill="var(--neon)" opacity="0.85"/><circle cx="106" cy="52" r="3" fill="var(--neon)" opacity="0.85"/>
        <path d="M94 46 Q80 25 65 15" stroke="var(--neon)" stroke-width="1" fill="none" opacity="0.65"/>
        <path d="M106 46 Q120 25 135 15" stroke="var(--neon)" stroke-width="1" fill="none" opacity="0.65"/>
        <g class="wing-l"><path d="M75 80 Q30 50 15 80 Q20 110 75 120" stroke="var(--neon)" stroke-width="1.3" fill="none" opacity="0.7"/><path d="M75 85 Q40 65 30 85" stroke="var(--neon)" stroke-width="0.7" fill="none" opacity="0.4"/><path d="M75 95 Q35 80 25 100" stroke="var(--neon)" stroke-width="0.7" fill="none" opacity="0.35"/></g>
        <g class="wing-r"><path d="M125 80 Q170 50 185 80 Q180 110 125 120" stroke="var(--neon)" stroke-width="1.3" fill="none" opacity="0.7"/><path d="M125 85 Q160 65 170 85" stroke="var(--neon)" stroke-width="0.7" fill="none" opacity="0.4"/><path d="M125 95 Q165 80 175 100" stroke="var(--neon)" stroke-width="0.7" fill="none" opacity="0.35"/></g>
        <ellipse cx="100" cy="75" rx="20" ry="9" stroke="var(--neon)" stroke-width="1.2" fill="none" opacity="0.7"/>
        <ellipse cx="100" cy="100" rx="24" ry="11" stroke="var(--neon)" stroke-width="1.1" fill="none" opacity="0.65"/>
        <ellipse cx="100" cy="122" rx="22" ry="10" stroke="var(--neon)" stroke-width="1.0" fill="none" opacity="0.6"/>
        <ellipse cx="100" cy="142" rx="18" ry="9" stroke="var(--neon)" stroke-width="0.9" fill="none" opacity="0.55"/>
    </svg>
</div>

<!-- FLYING CICADA 2 -->
<div class="flying-cicada" id="flyCicada2" style="transform:scaleX(-1)">
    <svg viewBox="0 0 200 200" fill="none" xmlns="http://www.w3.org/2000/svg">
        <circle cx="100" cy="55" r="12" stroke="var(--neon)" stroke-width="1.5" fill="none" opacity="0.9"/>
        <circle cx="94" cy="52" r="3" fill="var(--neon)" opacity="0.85"/><circle cx="106" cy="52" r="3" fill="var(--neon)" opacity="0.85"/>
        <path d="M94 46 Q80 25 65 15" stroke="var(--neon)" stroke-width="1" fill="none" opacity="0.65"/>
        <path d="M106 46 Q120 25 135 15" stroke="var(--neon)" stroke-width="1" fill="none" opacity="0.65"/>
        <g class="wing-l"><path d="M75 80 Q30 50 15 80 Q20 110 75 120" stroke="var(--neon)" stroke-width="1.3" fill="none" opacity="0.7"/><path d="M75 85 Q40 65 30 85" stroke="var(--neon)" stroke-width="0.7" fill="none" opacity="0.4"/></g>
        <g class="wing-r"><path d="M125 80 Q170 50 185 80 Q180 110 125 120" stroke="var(--neon)" stroke-width="1.3" fill="none" opacity="0.7"/><path d="M125 85 Q160 65 170 85" stroke="var(--neon)" stroke-width="0.7" fill="none" opacity="0.4"/></g>
        <ellipse cx="100" cy="75" rx="20" ry="9" stroke="var(--neon)" stroke-width="1.2" fill="none" opacity="0.7"/>
        <ellipse cx="100" cy="100" rx="24" ry="11" stroke="var(--neon)" stroke-width="1.1" fill="none" opacity="0.65"/>
        <ellipse cx="100" cy="122" rx="22" ry="10" stroke="var(--neon)" stroke-width="1.0" fill="none" opacity="0.6"/>
    </svg>
</div>

<!-- SMALL CICADA BADGE -->
<div class="cicada-badge">
    <svg viewBox="0 0 200 200" fill="none" xmlns="http://www.w3.org/2000/svg">
        <circle cx="100" cy="50" r="14" stroke="var(--neon)" stroke-width="1.8" fill="none" opacity="0.9"/>
        <circle cx="93" cy="47" r="3.5" fill="var(--neon)" opacity="0.9"/><circle cx="107" cy="47" r="3.5" fill="var(--neon)" opacity="0.9"/>
        <circle cx="93" cy="47" r="1.5" fill="#fff" opacity="0.8"/><circle cx="107" cy="47" r="1.5" fill="#fff" opacity="0.8"/>
        <path d="M92 40 Q78 22 62 10" stroke="var(--neon)" stroke-width="1.2" fill="none" opacity="0.6"/>
        <path d="M108 40 Q122 22 138 10" stroke="var(--neon)" stroke-width="1.2" fill="none" opacity="0.6"/>
        <circle cx="62" cy="10" r="1.5" fill="var(--neon)" opacity="0.5"/><circle cx="138" cy="10" r="1.5" fill="var(--neon)" opacity="0.5"/>
        <path d="M72 72 Q25 42 10 72 Q15 105 72 115" stroke="var(--neon)" stroke-width="1.5" fill="none" opacity="0.75"/>
        <path d="M72 78 Q38 58 28 78" stroke="var(--neon)" stroke-width="0.8" fill="none" opacity="0.45"/>
        <path d="M72 88 Q33 72 22 92" stroke="var(--neon)" stroke-width="0.8" fill="none" opacity="0.4"/>
        <path d="M72 98 Q36 86 26 104" stroke="var(--neon)" stroke-width="0.6" fill="none" opacity="0.35"/>
        <path d="M128 72 Q175 42 190 72 Q185 105 128 115" stroke="var(--neon)" stroke-width="1.5" fill="none" opacity="0.75"/>
        <path d="M128 78 Q162 58 172 78" stroke="var(--neon)" stroke-width="0.8" fill="none" opacity="0.45"/>
        <path d="M128 88 Q167 72 178 92" stroke="var(--neon)" stroke-width="0.8" fill="none" opacity="0.4"/>
        <path d="M128 98 Q164 86 174 104" stroke="var(--neon)" stroke-width="0.6" fill="none" opacity="0.35"/>
        <ellipse cx="100" cy="70" rx="22" ry="10" stroke="var(--neon)" stroke-width="1.3" fill="none" opacity="0.7"/>
        <ellipse cx="100" cy="95" rx="26" ry="12" stroke="var(--neon)" stroke-width="1.2" fill="none" opacity="0.65"/>
        <ellipse cx="100" cy="118" rx="24" ry="11" stroke="var(--neon)" stroke-width="1.1" fill="none" opacity="0.6"/>
        <ellipse cx="100" cy="138" rx="20" ry="10" stroke="var(--neon)" stroke-width="1.0" fill="none" opacity="0.55"/>
        <ellipse cx="100" cy="155" rx="14" ry="7" stroke="var(--neon)" stroke-width="0.8" fill="none" opacity="0.45"/>
        <path d="M78 75 Q58 95 50 112" stroke="var(--neon)" stroke-width="0.9" fill="none" opacity="0.4"/>
        <path d="M76 92 Q53 112 46 130" stroke="var(--neon)" stroke-width="0.9" fill="none" opacity="0.35"/>
        <path d="M80 108 Q58 128 53 148" stroke="var(--neon)" stroke-width="0.8" fill="none" opacity="0.3"/>
        <path d="M122 75 Q142 95 150 112" stroke="var(--neon)" stroke-width="0.9" fill="none" opacity="0.4"/>
        <path d="M124 92 Q147 112 154 130" stroke="var(--neon)" stroke-width="0.9" fill="none" opacity="0.35"/>
        <path d="M120 108 Q142 128 147 148" stroke="var(--neon)" stroke-width="0.8" fill="none" opacity="0.3"/>
    </svg>
</div>

<!-- HERO -->
<div class="hero">
    <h1>CICADA 3301</h1>
    <p class="sub">We are everywhere.<br>Decode to prove yourself.</p>
    <div class="good-luck">GOOD LUCK!</div>
    <div class="everywhere-box"><span>EVERYWHERE</span></div>
    <div class="three-three-oh-one">3 3 0 1</div>
</div>

<!-- STATS -->
<div class="stats-bar" id="statsBar">
    <div class="stat"><div class="stat-label">SOLVERS</div><div class="stat-value" id="solverCount">0</div></div>
    <div class="stat"><div class="stat-label">TOTAL POINTS</div><div class="stat-value" id="totalPoints">0</div></div>
    <div class="stat"><div class="stat-label">XMR REWARDED</div><div class="stat-value" id="totalXMR">0</div></div>
</div>

<!-- LOGIN -->
<div class="login-section" id="loginSection">
    <input type="text" id="username" placeholder="Username / Alias" maxlength="20">
    <br>
    <input type="text" id="wallet" placeholder="Monero Wallet (for XMR reward)">
    <br>
    <button class="btn-enter" onclick="login()">ENTER THE CICADA NETWORK</button>
</div>
<div class="user-info" id="userInfo" style="display:none">
    <span id="displayUsername"></span>
    <button class="btn-logout" onclick="logout()">LOGOUT</button>
</div>

<!-- PUZZLES -->
<div class="puzzles">
    <div class="sec-label">Available Puzzles</div>
    <div class="pgrid" id="puzzleGrid"></div>

    <div class="lb"><h3>Top Solvers</h3><div id="lbList"></div></div>

    <div class="tgb">
        <p>Join the Inner Circle</p>
        <a href="https://t.me/proplanwh" target="_blank" class="tgl">@proplanwh</a>
    </div>

    <div class="ft">
        <p>3301 &bull; Liber Primus &bull; Veritas Odium Parit</p>
        <p class="xmr">XMR: 8BuSHCofBXzAti2oQemtqo1j8q2UZHQBpFwqvJa6pMyUWp6x4QZTaWuHBmUxRb5S9Z6KZCqCaosZw78G9ufrffSz6AXjUhJ</p>
    </div>
</div>

<!-- MODAL -->
<div class="mbg" id="modal">
    <div class="mbox">
        <h3 id="mT">Submit Answer</h3>
        <div class="md" id="mD"></div>
        <div class="mr" id="mR"></div>
        <textarea id="iA" rows="3" placeholder="Your decoded answer..."></textarea>
        <div class="mbs">
            <button class="btn-s" onclick="submitAnswer()">Submit</button>
            <button class="btn-h" onclick="buyHint()">Hint</button>
            <button class="btn-c" onclick="closeModal()">Close</button>
        </div>
    </div>
</div>

<script>
/* ── 1. DIGITAL RAIN (SLOW, color-cycling) ── */
(function(){
    const c=document.getElementById('rain'),x=c.getContext('2d');
    let W,H,cols,dr,fs=14;
    function rz(){W=c.width=innerWidth;H=c.height=innerHeight;cols=Math.floor(W/fs);dr=Array.from({length:cols},()=>Math.random()*H/fs|0)}
    rz();addEventListener('resize',rz);
    let frameCount=0;
    function draw(){
        /* Slow rain: higher alpha fade = slower trail */
        x.fillStyle='rgba(0,0,0,0.04)';x.fillRect(0,0,W,H);
        x.font=fs+'px Share Tech Mono,monospace';
        const rgb=getComputedStyle(document.documentElement).getPropertyValue('--neon-rgb').trim();
        for(let i=0;i<cols;i++){
            /* Drop 1 char every 3 frames = slower */
            if(frameCount%3!==0){continue}
            const ch=String.fromCharCode(0x30A0+Math.random()*96),px=i*fs,py=dr[i]*fs;
            x.fillStyle='rgba('+rgb+',0.85)';x.fillText(ch,px,py);
            x.fillStyle='rgba('+rgb+',0.25)';x.fillText(ch,px,py-fs);
            if(py>H&&Math.random()>0.98)dr[i]=0;
            dr[i]++;
        }
        frameCount++;
        requestAnimationFrame(draw);
    }
    draw();
})();

/* ── 2. COLOR CYCLING: red -> green -> lime -> purple -> red ── */
(function(){
    const C=[
        {n:'#ff0033',g:'rgba(255,0,51,',d:'rgba(255,0,51,0.25)',s:'rgba(255,0,51,0.08)',rgb:'255,0,51'},
        {n:'#00ff41',g:'rgba(0,255,65,',d:'rgba(0,255,65,0.25)',s:'rgba(0,255,65,0.08)',rgb:'0,255,65'},
        {n:'#39ff14',g:'rgba(57,255,20,',d:'rgba(57,255,20,0.25)',s:'rgba(57,255,20,0.08)',rgb:'57,255,20'},
        {n:'#bf00ff',g:'rgba(191,0,255,',d:'rgba(191,0,255,0.25)',s:'rgba(191,0,255,0.08)',rgb:'191,0,255'},
    ];
    let i=0;const r=document.documentElement.style;
    function sc(i){const c=C[i%C.length];r.setProperty('--neon',c.n);r.setProperty('--neon-glow',c.g+'0.5)');r.setProperty('--neon-dim',c.d);r.setProperty('--neon-soft',c.s);r.setProperty('--neon-rgb',c.rgb)}
    sc(0);setInterval(()=>{i++;sc(i%C.length)},2000);
})();

/* ── 3. CICADA SOUND (Web Audio API — original) ── */
let audioCtx=null,cicadaNodes=[],sndPlaying=false,sndMuted=false;
function createCicadaSound(){
    if(!audioCtx)audioCtx=new(window.AudioContext||window.webkitAudioContext)();
    const now=audioCtx.currentTime;
    const osc1=audioCtx.createOscillator();osc1.type='sawtooth';osc1.frequency.setValueAtTime(5500,now);
    const lfo1=audioCtx.createOscillator();lfo1.frequency.setValueAtTime(35,now);
    const lfoG1=audioCtx.createGain();lfoG1.gain.setValueAtTime(800,now);
    lfo1.connect(lfoG1);lfoG1.connect(osc1.frequency);
    const lfo2=audioCtx.createOscillator();lfo2.frequency.setValueAtTime(18,now);
    const lfoG2=audioCtx.createGain();lfoG2.gain.setValueAtTime(0.3,now);lfo2.connect(lfoG2);
    const osc2=audioCtx.createOscillator();osc2.type='square';osc2.frequency.setValueAtTime(8200,now);
    const lfo3=audioCtx.createOscillator();lfo3.frequency.setValueAtTime(28,now);
    const lfoG3=audioCtx.createGain();lfoG3.gain.setValueAtTime(600,now);
    lfo3.connect(lfoG3);lfoG3.connect(osc2.frequency);
    const master=audioCtx.createGain();master.gain.setValueAtTime(0.06,now);
    const filt=audioCtx.createBiquadFilter();filt.type='bandpass';filt.frequency.setValueAtTime(6000,now);filt.Q.setValueAtTime(2,now);
    osc1.connect(filt);osc2.connect(filt);lfo2.connect(lfoG2);lfoG2.connect(master.gain);
    filt.connect(master);master.connect(audioCtx.destination);
    [osc1,osc2,lfo1,lfo2,lfo3].forEach(n=>n.start(now));
    cicadaNodes=[osc1,osc2,lfo1,lfo2,lfo3];sndPlaying=true;
}
function stopCicadaSound(){cicadaNodes.forEach(n=>{try{n.stop()}catch(e){}});cicadaNodes=[];sndPlaying=false}
function toggleSound(){const b=document.getElementById('sndBtn');if(sndMuted){if(!sndPlaying)createCicadaSound();sndMuted=false;b.classList.remove('muted')}else{stopCicadaSound();sndMuted=true;b.classList.add('muted')}}
function startOnInteract(){createCicadaSound();document.removeEventListener('click',startOnInteract);document.removeEventListener('touchstart',startOnInteract)}
document.addEventListener('click',startOnInteract);document.addEventListener('touchstart',startOnInteract);

/* ── 4. AUTH & APP STATE ── */
let currentUser=null,currentUserWallet=null,solvedPuzzles=[];

function login(){
    const u=document.getElementById('username').value.trim();
    const w=document.getElementById('wallet').value.trim();
    if(!u||!w){alert('Enter username and Monero wallet');return}
    currentUser=u;currentUserWallet=w;
    localStorage.setItem('cicada_user',u);localStorage.setItem('cicada_wallet',w);
    document.getElementById('loginSection').style.display='none';
    document.getElementById('userInfo').style.display='block';
    document.getElementById('displayUsername').textContent='\\u{1F997} '+u;
    solvedPuzzles=JSON.parse(localStorage.getItem('cicada_solved_'+u)||'[]');
    loadPuzzles();loadLeaderboard();loadStats();
}
function logout(){
    currentUser=null;solvedPuzzles=[];
    localStorage.removeItem('cicada_user');localStorage.removeItem('cicada_wallet');
    document.getElementById('loginSection').style.display='block';
    document.getElementById('userInfo').style.display='none';
}
/* Restore session */
const savedU=localStorage.getItem('cicada_user'),savedW=localStorage.getItem('cicada_wallet');
if(savedU&&savedW){
    currentUser=savedU;currentUserWallet=savedW;
    document.getElementById('loginSection').style.display='none';
    document.getElementById('userInfo').style.display='block';
    document.getElementById('displayUsername').textContent='\\u{1F997} '+savedU;
    solvedPuzzles=JSON.parse(localStorage.getItem('cicada_solved_'+savedU)||'[]');
}

/* ── 5. PUZZLES (load from backend) ── */
async function loadPuzzles(){
    try{
        const res=await fetch('/api/puzzles');const data=await res.json();
        const grid=document.getElementById('puzzleGrid');
        let html='';
        const entries=Object.entries(data);
        entries.forEach(([id,p],i)=>{
            const solved=solvedPuzzles.includes(id);
            html+=`<div class="pcard ${solved?'solved':''}" onclick="openPuzzle('${id}')">
                <div class="pc-lvl">Level ${i+1}</div>
                <div class="pc-nm">${p.name}</div>
                <span class="pc-df df-${p.difficulty.toLowerCase()}">${p.difficulty}</span>
                <div class="pc-ds">${p.description}</div>
                <div class="pc-rw">\\u{1F4B0} ${p.reward_xmr} XMR | \\u{1F3AF} ${p.points} pts</div>
                <div class="pc-mt"><span>\\u23F1 ${p.time}</span><span>\\u{1F517} ${p.category}</span></div>
                ${solved?'<div style="color:#ffd700;margin-top:6px;font-size:0.7rem">\\u2705 SOLVED</div>':''}
            </div>`;
        });
        grid.innerHTML=html;
    }catch(e){console.error('Failed to load puzzles',e)}
}

/* ── 6. MODAL ── */
let cur=null;
async function openPuzzle(id){
    if(!currentUser){alert('Login first to participate');return}
    try{
        const res=await fetch('/api/puzzles');const data=await res.json();
        cur={id,...data[id]};
        if(solvedPuzzles.includes(id)){alert('Already solved!');return}
        document.getElementById('mT').textContent='\\u{1F511} '+cur.name;
        document.getElementById('mD').textContent=cur.description;
        document.getElementById('mR').innerHTML='\\u{1F4B0} '+cur.reward_xmr+' XMR | \\u{1F3AF} '+cur.points+' pts';
        document.getElementById('iA').value='';
        document.getElementById('modal').classList.add('active');
    }catch(e){console.error(e)}
}
function closeModal(){document.getElementById('modal').classList.remove('active');cur=null}
async function submitAnswer(){
    if(!cur||!currentUser)return;
    const a=document.getElementById('iA').value.trim();
    if(!a){alert('Enter your decoded answer.');return}
    try{
        const res=await fetch('/api/submit',{
            method:'POST',headers:{'Content-Type':'application/json'},
            body:JSON.stringify({puzzle_id:cur.id,answer:a,username:currentUser,wallet:currentUserWallet})
        });
        const data=await res.json();
        if(data.success){
            solvedPuzzles.push(cur.id);
            localStorage.setItem('cicada_solved_'+currentUser,JSON.stringify(solvedPuzzles));
            alert('\\u2705 '+data.message);
            closeModal();loadPuzzles();loadLeaderboard();loadStats();
        }else{alert('\\u274C '+data.error)}
    }catch(e){alert('Network error. Try again.');console.error(e)}
}
function buyHint(){if(cur)alert('\\u{1F4A1} HINT: '+cur.hint+'\\n\\nCost: 0.005 XMR')}

/* ── 7. LEADERBOARD ── */
async function loadLeaderboard(){
    try{
        const res=await fetch('/api/leaderboard');const leaders=await res.json();
        document.getElementById('lbList').innerHTML=leaders.map(e=>
            `<div class="lbr"><span class="lbr-r lbr-${e.rank<=3?e.rank:''}">#${e.rank}</span><span class="lbr-n">${e.username}</span><span class="lbr-p">${e.points.toLocaleString()} pts | ${e.xmr} XMR</span></div>`
        ).join('');
    }catch(e){console.error(e)}
}

/* ── 8. STATS ── */
async function loadStats(){
    try{
        const res=await fetch('/api/stats');const s=await res.json();
        document.getElementById('solverCount').textContent=s.total_solvers;
        document.getElementById('totalPoints').textContent=s.total_points.toLocaleString();
        document.getElementById('totalXMR').textContent=s.total_xmr;
    }catch(e){console.error(e)}
}

/* ── INIT ── */
loadPuzzles();loadLeaderboard();loadStats();
setInterval(()=>{loadLeaderboard();loadStats()},15000);
</script>
</body>
</html>
'''

if __name__ == '__main__':
    print("""
    CICADA 3301 - THE LIBER PRIMUS
    ================================================
    8 Puzzles (Beginner -> Mythic)
    Color cycling + Glitch + Flying Cicadas
    Original Web Audio cicada sound
    SQLite Database + Leaderboard + User System
    ================================================
    Port: 5060
    """)
    app.run(host='0.0.0.0', port=5060, debug=False)
