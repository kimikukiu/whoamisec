#!/bin/bash

# Încarcă ENV
set -a
source .env
set +a

WALLET_NAME="$WALLET_NAME"
WALLET_PASS="$WALLET_PASS"
EXPECTED_AMOUNT="$XMR_PRICE"
LOG_FILE="payments.log"
WHITELIST_FILE="whitelist.txt"

# Verifică dacă monero-wallet-cli există
if [ ! -f "$WALLET_CLI_PATH" ]; then
    echo "[ERROR] Nu găsesc monero-wallet-cli la $WALLET_CLI_PATH"
    exit 1
fi

check_payments() {
    # Obține balanța
    BALANCE=$($WALLET_CLI_PATH --wallet-file $WALLET_NAME --password $WALLET_PASS --balance 2>/dev/null | grep "Total" | awk '{print $4}')
    
    if [ -z "$BALANCE" ]; then
        echo "[$(date)] ⚠️ Nu pot conecta la portofel"
        return
    fi
    
    # Obține tranzacțiile noi
    $WALLET_CLI_PATH --wallet-file $WALLET_NAME --password $WALLET_PASS --incoming-transfers 2>/dev/null > /tmp/xmr_txs.txt
    
    while IFS= read -r line; do
        if [[ $line == *"incoming"* ]]; then
            TX_ID=$(echo $line | awk '{print $2}')
            TX_AMOUNT=$(echo $line | awk '{print $4}')
            
            # Verifică dacă e deja whitelistat
            if ! grep -q "$TX_ID" "$WHITELIST_FILE" 2>/dev/null; then
                if (( $(echo "$TX_AMOUNT >= $EXPECTED_AMOUNT" | bc -l) )); then
                    echo "[$(date)] ✅ PLĂTIT! TXID: $TX_ID | Sumă: $TX_AMOUNT XMR" >> $LOG_FILE
                    echo "$TX_ID" >> $WHITELIST_FILE
                    echo "🎫 Access acordat pentru TX: $TX_ID"
                fi
            fi
        fi
    done < /tmp/xmr_txs.txt
}

echo "[$(date)] 🚀 Monero Watchdog a pornit..."
echo "💰 Aștept plăți de $EXPECTED_AMOUNT XMR la adresa: $XMR_ADDRESS"

while true; do
    check_payments
    sleep 60
done
