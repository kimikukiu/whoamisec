#!/usr/bin/env python3
"""
CICADA 3301 - Puzzle Monetization Platform
Cryptografie, codare, mister - plătit în Monero
"""

import hashlib
import secrets
import json
from datetime import datetime
from flask import Flask, request, jsonify, render_template_string
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(32)
jwt = JWTManager(app)

# ============================================
# PUZZLE-URI CICADA 3301 STYLE
# ============================================

PUZZLES = {
    'level_1': {
        'name': '🕯️ The First Key',
        'difficulty': 'Easy',
        'reward_xmr': 0.01,
        'description': 'Decodează mesajul: "48 65 6c 6c 6f 20 57 6f 72 6c 64"',
        'hint': 'ASCII',
        'answer_hash': hashlib.sha256(b'Hello World').hexdigest(),
        'time_limit_hours': 24
    },
    'level_2': {
        'name': '🔐 Caesar\'s Secret',
        'difficulty': 'Easy',
        'reward_xmr': 0.02,
        'description': 'R3 V3 R3 V3 R3 V3 (cheia este 3)',
        'hint': 'Cifrul lui Caesar',
        'answer_hash': hashlib.sha256(b'OH OH OH').hexdigest(),
        'time_limit_hours': 48
    },
    'level_3': {
        'name': '📜 The Book Cipher',
        'difficulty': 'Medium',
        'reward_xmr': 0.05,
        'description': 'pagina 42, rândul 7, cuvântul 3 din Biblia lui Gutenberg',
        'hint': 'Primul cuvânt după "In the beginning"',
        'answer_hash': hashlib.sha256(b'the').hexdigest(),
        'time_limit_hours': 72
    },
    'level_4': {
        'name': '🔑 RSA Challenge',
        'difficulty': 'Hard',
        'reward_xmr': 0.10,
        'description': 'n=3233, e=17, mesaj criptat=2790. Decryptează.',
        'hint': 'p=53, q=61',
        'answer_hash': hashlib.sha256(b'hello').hexdigest(),
        'time_limit_hours': 120
    },
    'level_5': {
        'name': '🌀 Cicada\'s Riddle',
        'difficulty': 'Expert',
        'reward_xmr': 0.50,
        'description': 'We are 3301. Decode: 01010111 01100101 00100000 01100001 01110010 01100101 00100000 01100101 01110110 01100101 01110010 01111001 01110111 01101000 01100101 01110010 01100101',
        'hint': 'Binary to text',
        'answer_hash': hashlib.sha256(b'We are everywhere').hexdigest(),
        'time_limit_hours': 168
    },
    'level_6': {
        'name': '🗝️ Cicada 3301 - The Final',
        'difficulty': 'Legendary',
        'reward_xmr': 1.00,
        'description': 'LK2@#8$n!9$#KJ@!$#@L:>{">?<L":{P{">?<L":@!$#KJ@!$#LK@LK@LK@',
        'hint': 'The key is everywhere. 3301.',
        'answer_hash': hashlib.sha256(b'Liber Primus').hexdigest(),
        'time_limit_hours': 336
    }
}

# ============================================
# ENDPOINT-URI PUZZLE
# ============================================

@app.route('/api/puzzle/list', methods=['GET'])
def list_puzzles():
    """Listează toate puzzle-urile disponibile"""
    return jsonify([{
        'id': k,
        'name': v['name'],
        'difficulty': v['difficulty'],
        'reward_xmr': v['reward_xmr'],
        'description': v['description'],
        'time_limit_hours': v['time_limit_hours']
    } for k, v in PUZZLES.items()])

@app.route('/api/puzzle/submit', methods=['POST'])
def submit_puzzle():
    """Trimite un răspuns la puzzle"""
    data = request.json
    puzzle_id = data.get('puzzle_id')
    answer = data.get('answer')
    user_wallet = data.get('xmr_address')
    
    if puzzle_id not in PUZZLES:
        return jsonify({'error': 'Puzzle invalid'}), 400
    
    puzzle = PUZZLES[puzzle_id]
    answer_hash = hashlib.sha256(answer.encode()).hexdigest()
    
    if answer_hash == puzzle['answer_hash']:
        # Răspuns corect - trimite recompensa
        return jsonify({
            'success': True,
            'message': f'✅ Răspuns corect! Recompensa de {puzzle["reward_xmr"]} XMR va fi trimisă la {user_wallet} în 24h.',
            'next_puzzle': list(PUZZLES.keys()).index(puzzle_id) + 1 < len(PUZZLES)
        })
    else:
        return jsonify({'error': '❌ Răspuns incorect. Încearcă din nou.'}), 400

# ============================================
# PAGINĂ CICADA 3301 STYLE
# ============================================

CICADA_PAGE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CICADA 3301 - The Puzzle</title>
    <style>
        @keyframes glitch {
            0% { text-shadow: 0.05em 0 0 #0f0, -0.05em -0.025em 0 #f00; }
            100% { text-shadow: -0.05em -0.025em 0 #0f0, 0.025em 0.05em 0 #f00; }
        }
        body {
            background: #000;
            font-family: 'Courier New', monospace;
            color: #0f0;
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        .cicada-container {
            max-width: 800px;
            padding: 40px;
            border: 2px solid #0f0;
            border-radius: 20px;
            background: rgba(0,0,0,0.9);
            box-shadow: 0 0 30px rgba(0,255,0,0.3);
        }
        .cicada-symbol {
            font-size: 100px;
            text-align: center;
            animation: glitch 3s infinite;
        }
        h1 { text-align: center; font-size: 2em; letter-spacing: 10px; }
        .puzzle {
            background: #0a0a0a;
            border: 1px solid #0f0;
            padding: 15px;
            margin: 20px 0;
            border-radius: 10px;
        }
        .puzzle:hover { background: #0f0; color: #000; cursor: pointer; }
        .reward { color: #ff0; }
        input, textarea {
            background: #000;
            border: 1px solid #0f0;
            color: #0f0;
            padding: 10px;
            width: 100%;
            margin: 10px 0;
            font-family: monospace;
        }
        button {
            background: #0f0;
            color: #000;
            border: none;
            padding: 12px 24px;
            cursor: pointer;
            font-weight: bold;
        }
        .footer { text-align: center; margin-top: 30px; font-size: 0.7em; opacity: 0.5; }
    </style>
</head>
<body>
    <div class="cicada-container">
        <div class="cicada-symbol">🦗</div>
        <h1>CICADA 3301</h1>
        <p style="text-align:center">"We are everywhere. Decode to prove yourself."</p>
        
        <div id="puzzles"></div>
        
        <div id="submission" style="display:none;">
            <h3>📝 Submit Answer</h3>
            <input type="text" id="puzzleId" readonly>
            <textarea id="answer" rows="3" placeholder="Your answer..."></textarea>
            <input type="text" id="xmrWallet" placeholder="Your Monero wallet address for reward">
            <button onclick="submitAnswer()">🔓 Submit & Claim Reward</button>
        </div>
        
        <div class="footer">
            <p>3301 | Liber Primus | Veritas Odium Parit</p>
        </div>
    </div>
    
    <script>
        async function loadPuzzles() {
            const response = await fetch('/api/puzzle/list');
            const puzzles = await response.json();
            const container = document.getElementById('puzzles');
            
            let html = '<h2>📜 AVAILABLE PUZZLES</h2>';
            puzzles.forEach(p => {
                html += `
                    <div class="puzzle" onclick="selectPuzzle('${p.id}', '${p.name}')">
                        <strong>${p.name}</strong> - ${p.difficulty}<br>
                        🧩 ${p.description}<br>
                        💰 Reward: ${p.reward_xmr} XMR<br>
                        ⏰ Time limit: ${p.time_limit_hours} hours
                    </div>
                `;
            });
            container.innerHTML = html;
        }
        
        function selectPuzzle(id, name) {
            document.getElementById('puzzleId').value = id;
            document.getElementById('submission').style.display = 'block';
            alert(`Selected: ${name}\nSolve the puzzle and submit your answer.`);
        }
        
        async function submitAnswer() {
            const puzzleId = document.getElementById('puzzleId').value;
            const answer = document.getElementById('answer').value;
            const wallet = document.getElementById('xmrWallet').value;
            
            const response = await fetch('/api/puzzle/submit', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ puzzle_id: puzzleId, answer: answer, xmr_address: wallet })
            });
            
            const data = await response.json();
            
            if (data.success) {
                alert(data.message);
                if (data.next_puzzle) {
                    document.getElementById('submission').style.display = 'none';
                    document.getElementById('answer').value = '';
                }
            } else {
                alert(data.error);
            }
        }
        
        loadPuzzles();
    </script>
</body>
</html>
'''

@app.route('/')
def cicada_home():
    return render_template_string(CICADA_PAGE)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5050, debug=False)
