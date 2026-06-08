"""
WHOAMI.SEC - JARVIS OMNI Backend
Next-Gen AI Security Platform
Flask API with SQLite, JWT Auth, AI Chat, Monero Payments
"""

import os
import datetime
import hashlib
import requests
from functools import wraps

from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    jwt_required,
    get_jwt_identity,
)

app = Flask(__name__)

# ── Config ──────────────────────────────────────────────────────────────────
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
    "DATABASE_URL", "sqlite:///whoamisec.db"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "whoamisec-super-secret-2026")
app.config["JWT_SECRET_KEY"] = os.getenv(
    "JWT_SECRET_KEY", "jwt-whoamisec-secret"
)
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = datetime.timedelta(days=7)

CORS(app)
db = SQLAlchemy(app)
jwt = JWTManager(app)

# ── Monero Config ────────────────────────────────────────────────────────────
XMR_DAEMON_RPC = os.getenv("XMR_DAEMON_RPC", "http://127.0.0.1:18081/json_rpc")
XMR_WALLET_RPC = os.getenv("XMR_WALLET_RPC", "http://127.0.0.1:18083/json_rpc")
XMR_WALLET_ADDRESS = os.getenv(
    "XMR_WALLET_ADDRESS",
    "46BeJeHmQQ6czjXH2vKSe8V7PbaEtfM3ekuJMFc9BBYhMZym43VWLqPhKYsVfkBB1Jc3RYpUK1jhCcxvFKMn3uTDQzmzDfk",
)
XMR_CREDITS_PER_XMR = float(os.getenv("XMR_CREDITS_PER_XMR", 1000))

# ── Ollama Config ──────────────────────────────────────────────────────────
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")

# ── Models ──────────────────────────────────────────────────────────────────


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=True)
    password_hash = db.Column(db.String(256), nullable=False)
    credits = db.Column(db.Integer, default=100)
    api_calls = db.Column(db.Integer, default=0)
    xmr_balance = db.Column(db.Float, default=0.0)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(
        db.DateTime, default=datetime.datetime.utcnow
    )

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "credits": self.credits,
            "api_calls": self.api_calls,
            "xmr_balance": self.xmr_balance,
            "is_admin": self.is_admin,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Transaction(db.Model):
    __tablename__ = "transactions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    tx_hash = db.Column(db.String(256), nullable=True)
    amount_xmr = db.Column(db.Float, default=0.0)
    credits_added = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default="pending")  # pending, confirmed
    created_at = db.Column(
        db.DateTime, default=datetime.datetime.utcnow
    )

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "tx_hash": self.tx_hash,
            "amount_xmr": self.amount_xmr,
            "credits_added": self.credits_added,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class APIKey(db.Model):
    __tablename__ = "api_keys"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    key_hash = db.Column(db.String(256), nullable=False)
    key_prefix = db.Column(db.String(16), nullable=False)
    name = db.Column(db.String(100), default="default")
    created_at = db.Column(
        db.DateTime, default=datetime.datetime.utcnow
    )


# ── Helpers ──────────────────────────────────────────────────────────────────


def hash_password(password: str) -> str:
    salt = "whoamisec_salt_2026"
    return hashlib.sha256(f"{salt}{password}".encode()).hexdigest()


def admin_required(f):
    @wraps(f)
    @jwt_required()
    def decorated(*args, **kwargs):
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        if not user or not user.is_admin:
            return jsonify({"error": "Admin access required"}), 403
        return f(*args, **kwargs)

    return decorated


# ── Auth Routes ─────────────────────────────────────────────────────────────


@app.route("/api/auth/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    email = (data.get("email") or "").strip()
    password = data.get("password") or ""

    if not username or len(username) < 3:
        return jsonify({"error": "Username must be at least 3 characters"}), 400
    if not password or len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400
    if User.query.filter_by(username=username).first():
        return jsonify({"error": "Username already taken"}), 409
    if email and User.query.filter_by(email=email).first():
        return jsonify({"error": "Email already registered"}), 409

    user = User(
        username=username,
        email=email or None,
        password_hash=hash_password(password),
        credits=50,  # Welcome credits
    )
    db.session.add(user)
    db.session.commit()

    token = create_access_token(identity=user.id)
    return jsonify({"access_token": token, "user": user.to_dict()}), 201


@app.route("/api/auth/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""

    user = User.query.filter_by(username=username).first()
    if not user or user.password_hash != hash_password(password):
        return jsonify({"error": "Invalid username or password"}), 401

    token = create_access_token(identity=user.id)
    return jsonify({"access_token": token, "user": user.to_dict()}), 200


@app.route("/api/auth/me", methods=["GET"])
@jwt_required()
def me():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify({"user": user.to_dict()}), 200


# ── AI Chat ────────────────────────────────────────────────────────────────


@app.route("/api/ai/chat", methods=["POST"])
@jwt_required()
def ai_chat():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    if user.credits < 1:
        return jsonify({"error": "Insufficient credits"}), 402

    data = request.get_json(silent=True) or {}
    message = data.get("message", "").strip()
    model = data.get("model", "deepseek-coder:6.7b")

    if not message:
        return jsonify({"error": "Message is required"}), 400

    # Call Ollama
    try:
        resp = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": model,
                "prompt": message,
                "stream": False,
                "options": {"num_predict": 512},
            },
            timeout=60,
        )
        if resp.status_code == 200:
            result = resp.json()
            response_text = result.get("response", "No response from model")
        else:
            response_text = f"Ollama error: {resp.status_code} - {resp.text[:200]}"
    except requests.exceptions.ConnectionError:
        response_text = (
            "AI backend unavailable. Please ensure Ollama is running on "
            f"{OLLAMA_URL}. Install with: curl -fsSL https://ollama.com/install.sh | sh"
        )
    except Exception as e:
        response_text = f"AI error: {str(e)}"

    # Deduct credits
    user.credits -= 1
    user.api_calls += 1
    db.session.commit()

    return jsonify({"response": response_text, "model": model}), 200


# ── Payments ────────────────────────────────────────────────────────────────


@app.route("/api/payments/monero", methods=["GET"])
@jwt_required()
def get_monero_address():
    """Return the platform Monero address for deposits."""
    return jsonify({
        "address": XMR_WALLET_ADDRESS,
        "credits_per_xmr": XMR_CREDITS_PER_XMR,
        "network": "monero-mainnet",
    })


@app.route("/api/payments/check", methods=["GET"])
@jwt_required()
def check_payments():
    """
    Check for new Monero payments to the platform wallet.
    In production, this would query the monero-wallet-rpc for incoming transfers.
    """
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    # Simulated check - in production, query wallet RPC
    try:
        resp = requests.post(
            XMR_WALLET_RPC,
            json={
                "jsonrpc": "2.0",
                "id": "0",
                "method": "get_transfers",
                "params": {"in": True, "pool": True},
            },
            timeout=10,
        )
        if resp.status_code == 200:
            transfers = resp.json().get("result", {}).get("pool", [])
            credits_added = 0
            for tx in transfers:
                tx_hash = tx.get("txid")
                amount = tx.get("amount", 0)
                # Check if we already processed this tx
                existing = Transaction.query.filter_by(tx_hash=tx_hash).first()
                if not existing:
                    xmr_amount = amount / 1e12  # atomic units to XMR
                    new_credits = int(xmr_amount * XMR_CREDITS_PER_XMR)
                    transaction = Transaction(
                        user_id=user_id,
                        tx_hash=tx_hash,
                        amount_xmr=xmr_amount,
                        credits_added=new_credits,
                        status="confirmed",
                    )
                    db.session.add(transaction)
                    user.credits += new_credits
                    user.xmr_balance += xmr_amount
                    credits_added += new_credits
            db.session.commit()
            return jsonify({"credits_added": credits_added})
    except Exception:
        pass

    return jsonify({"credits_added": 0, "message": "No new payments detected"})


# ── Admin Routes ────────────────────────────────────────────────────────────


@app.route("/api/admin/users", methods=["GET"])
@admin_required
def admin_list_users():
    users = User.query.order_by(User.id.asc()).all()
    return jsonify([u.to_dict() for u in users]), 200


@app.route("/api/admin/user/<int:user_id>/credits", methods=["PUT"])
@admin_required
def admin_update_credits(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    data = request.get_json(silent=True) or {}
    new_credits = data.get("credits")
    if new_credits is None or not isinstance(new_credits, int) or new_credits < 0:
        return jsonify({"error": "Valid credits value required"}), 400

    user.credits = new_credits
    db.session.commit()

    return jsonify({"user": user.to_dict(), "message": "Credits updated"}), 200


# ── Health Check ────────────────────────────────────────────────────────────


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({
        "status": "online",
        "service": "whoamisec",
        "mode": "abliterated",
        "jarvis_omni": True,
    }), 200


@app.route("/api/models", methods=["GET"])
def list_models():
    """List available Ollama models."""
    try:
        resp = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        if resp.status_code == 200:
            models = resp.json().get("models", [])
            return jsonify({
                "models": [m.get("name") for m in models],
            })
    except Exception:
        pass

    return jsonify({
        "models": [
            "llama3.2:1b",
            "phi:2.7b",
            "tinyllama:1.1b",
            "deepseek-coder:6.7b",
        ],
        "note": "Ollama not connected, showing default model list",
    })


# ── Create Default Admin ───────────────────────────────────────────────────


def create_admin():
    admin = User.query.filter_by(username="admin").first()
    if not admin:
        admin = User(
            username="admin",
            email="admin@whoamisec.com",
            password_hash=hash_password("WhoamiSecAdmin2026!"),
            credits=99999,
            is_admin=True,
        )
        db.session.add(admin)
        db.session.commit()
        print("[WHOAMI.SEC] Admin user created: admin / WhoamiSecAdmin2026!")
    else:
        print("[WHOAMI.SEC] Admin user already exists")


# ── Init & Run ──────────────────────────────────────────────────────────────


with app.app_context():
    db.create_all()
    create_admin()


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  WHOAMI.SEC - JARVIS OMNI ABLITERATED")
    print("  Backend API Server")
    print("  SQLite Database: whoamisec.db")
    print("=" * 60 + "\n")
    app.run(host="0.0.0.0", port=5001, debug=True)
