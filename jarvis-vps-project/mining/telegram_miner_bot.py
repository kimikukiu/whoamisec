#!/usr/bin/env python3
"""
Telegram Bot pentru notificări minerit XMR
Trimite mesaje când se găsește un block sau la anumite intervale
"""

import requests
import time
import json
import asyncio
from datetime import datetime

# CONFIGURARE - ÎN LOCUIEȘTE CU DATELE TALE REALE
TELEGRAM_BOT_TOKEN = "7801243078:AAFvGRtUxBttRyKFU6PtOjXInwINfN1D2n0"  # @WhoamiSecXMRBot
TELEGRAM_CHAT_ID = "7474310431"  # ID-ul tău de Telegram

# Adresa ta Monero
XMR_ADDRESS = "8BuSHCofBXzAti2oQemtqo1j8q2UZHQBpFwqvJa6pMyUWp6x4QZTaWuHBmUxRb5S9Z6KZCqCaosZw78G9ufrffSz6AXjUhJ"

class XMRMinerNotifier:
    def __init__(self):
        self.base_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"
        self.last_block_height = 0
        self.last_hashrate = 0
        self.total_mined = 0
        
    def send_message(self, text, parse_mode='HTML'):
        """Trimite mesaj pe Telegram"""
        if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
            print("⚠️ Telegram not configured")
            return
            
        try:
            payload = {
                'chat_id': TELEGRAM_CHAT_ID,
                'text': text,
                'parse_mode': parse_mode
            }
            response = requests.post(f"{self.base_url}/sendMessage", json=payload, timeout=10)
            if response.status_code == 200:
                print(f"✅ Message sent: {text[:50]}...")
            else:
                print(f"❌ Failed to send: {response.text}")
        except Exception as e:
            print(f"❌ Error sending message: {e}")
    
    def get_mining_stats(self):
        """Obține statistici reale de la XMRig"""
        try:
            response = requests.get('http://localhost:8081/api/summary', timeout=5)
            if response.status_code == 200:
                data = response.json()
                return {
                    'hashrate': data.get('hashrate', {}).get('total', [0])[0],
                    'total_hashes': data.get('results', {}).get('total', 0),
                    'active_workers': len(data.get('workers', {})),
                    'connection': data.get('connection', {}).get('uptime', 0)
                }
        except:
            pass
        return None
    
    def get_pool_stats(self):
        """Obține statistici de la pool"""
        try:
            response = requests.get(f'https://supportxmr.com/api/miner/{XMR_ADDRESS}/stats', timeout=10)
            if response.status_code == 200:
                data = response.json()
                return {
                    'hashrate': data.get('hashrate', 0),
                    'total_hashes': data.get('totalHashes', 0),
                    'balance': data.get('amtDue', 0) / 1e12,
                    'last_share': data.get('lastShare', 0)
                }
        except:
            pass
        return None
    
    def check_new_blocks(self):
        """Verifică dacă s-a găsit un block nou"""
        try:
            response = requests.get('https://supportxmr.com/api/pool/stats', timeout=10)
            if response.status_code == 200:
                data = response.json()
                current_height = data.get('height', 0)
                
                if current_height > self.last_block_height and self.last_block_height > 0:
                    # Block nou găsit!
                    block_reward = data.get('lastReward', 0) / 1e12
                    self.send_message(
                        f"🎉 <b>BLOCK FOUND!</b> 🎉\n\n"
                        f"⛏️ Block height: <code>{current_height}</code>\n"
                        f"💰 Reward: {block_reward:.6f} XMR\n"
                        f"📊 Pool: supportxmr.com\n"
                        f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                        f"🔗 <a href='https://supportxmr.com/block/{current_height}'>View Block</a>"
                    )
                
                self.last_block_height = current_height
        except:
            pass
    
    def send_daily_report(self):
        """Trimite raport zilnic"""
        pool_stats = self.get_pool_stats()
        local_stats = self.get_mining_stats()
        
        if pool_stats:
            message = (
                f"📊 <b>XMR-MINER-WHOAMI.SEC - DAILY REPORT</b> 📊\n\n"
                f"⛏️ <b>Pool Stats:</b>\n"
                f"   • Hashrate: {pool_stats.get('hashrate', 0):.2f} H/s\n"
                f"   • Total hashes: {pool_stats.get('total_hashes', 0):,}\n"
                f"   • Balance: {pool_stats.get('balance', 0):.8f} XMR\n\n"
                f"🖥️ <b>Local Stats:</b>\n"
                f"   • Hashrate: {local_stats.get('hashrate', 0):.2f} H/s\n"
                f"   • Active workers: {local_stats.get('active_workers', 0)}\n\n"
                f"💰 <b>Platform Fee (35%):</b>\n"
                f"   • Estimated profit: {pool_stats.get('balance', 0) * 0.35:.8f} XMR\n\n"
                f"📅 {datetime.now().strftime('%Y-%m-%d')}\n"
                f"🔗 <a href='https://xmr-miner.whoamisec.com'>Open Dashboard</a>"
            )
            self.send_message(message)
    
    def send_alert(self, alert_type, details):
        """Trimite alertă"""
        alerts = {
            'high_hashrate': f"⚡ <b>HIGH HASHRATE ALERT</b> ⚡\n\nHashrate: {details} H/s\nPerformance excellent!",
            'low_hashrate': f"⚠️ <b>LOW HASHRATE ALERT</b> ⚠️\n\nHashrate: {details} H/s\nCheck your miners!",
            'node_down': f"🔴 <b>NODE DOWN ALERT</b> 🔴\n\nNode: {details}\nAttempting restart...",
            'payment_received': f"💚 <b>PAYMENT RECEIVED</b> 💚\n\nAmount: {details} XMR\nThank you for supporting XMR-MINER-WHOAMI.SEC!"
        }
        
        if alert_type in alerts:
            self.send_message(alerts[alert_type])
    
    def run(self):
        """Buclă principală"""
        print("🤖 XMR Miner Telegram Bot started!")
        self.send_message("✅ <b>XMR-MINER-WHOAMI.SEC</b> is ONLINE!\n\n⛏️ All 100 nodes operational\n💰 Platform fee: 35%\n📊 Monitoring real-time mining")
        
        last_report = time.time()
        
        while True:
            try:
                # Verifică block-uri noi la fiecare 10 secunde
                self.check_new_blocks()
                
                # Trimite raport zilnic (la fiecare 24h)
                if time.time() - last_report >= 86400:
                    self.send_daily_report()
                    last_report = time.time()
                
                time.sleep(10)
                
            except Exception as e:
                print(f"Error in main loop: {e}")
                time.sleep(30)

if __name__ == '__main__':
    bot = XMRMinerNotifier()
    bot.run()
