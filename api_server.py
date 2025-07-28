from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import requests
import os
from dotenv import load_dotenv
from verifier_js import has_nft  # Changed to use JavaScript-based verifier

load_dotenv()

app = Flask(__name__)
CORS(app, origins="*", methods=["GET", "POST", "OPTIONS"], allow_headers=["Content-Type", "Authorization"])

# UPDATE THIS URL to your bot server webhook
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")

@app.route('/api/config')
def get_config():
    """Return configuration data including API keys"""
    response = jsonify({
        "helius_api_key": os.getenv("HELIUS_API_KEY", "")
    })
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
    return response

@app.route('/api/verify-nft', methods=['POST'])
def verify_nft():
    try:
        data = request.json
        wallet_address = data.get('wallet_address')
        tg_id = data.get('tg_id')
        
        print(f"🔍 Verification request received:")
        print(f"  👤 Telegram ID: {tg_id}")
        print(f"  💰 Wallet Address: {wallet_address}")
        
        if not wallet_address or not tg_id:
            print("❌ Missing wallet_address or tg_id")
            return jsonify({"error": "Missing wallet_address or tg_id"}), 400
        
        # Check NFT ownership using JavaScript-based verifier
        print("🔍 Starting NFT verification (JavaScript approach)...")
        has_required_nft, nft_count = has_nft(wallet_address)  # Updated to get nft_count
        print(f"✅ Verification result: {has_required_nft}")
        print(f"📊 NFT Count: {nft_count}")  # Added print for NFT count
        
        # Send result to bot's webhook
        webhook_data = {
            "tg_id": tg_id,
            "has_nft": has_required_nft,
            "username": f"user_{tg_id}",
            "nft_count": nft_count  # Added nft_count to webhook data
        }
        
        print(f"📤 Sending webhook to: {WEBHOOK_URL}")
        print(f"📦 Webhook data: {webhook_data}")
        
        try:
            webhook_response = requests.post(WEBHOOK_URL, json=webhook_data, timeout=10)
            if webhook_response.status_code == 200:
                print(f"✅ Webhook sent successfully for user {tg_id}")
            else:
                print(f"❌ Webhook failed for user {tg_id}: {webhook_response.status_code}")
                print(f"📄 Webhook response: {webhook_response.text}")
        except Exception as e:
            print(f"❌ Error sending webhook: {e}")
        
        response = jsonify({
            "has_nft": has_required_nft,
            "nft_count": nft_count,  # Added nft_count to API response
            "wallet_address": wallet_address,
            "message": "NFT verification completed (JavaScript approach)"
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
        return response
        
    except Exception as e:
        print(f"❌ Error in verify_nft: {e}")
        response = jsonify({"error": str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
        return response, 500

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

if __name__ == '__main__':
    print("🚀 Starting API Server with JavaScript-based NFT verification...")
    app.run(host='0.0.0.0', port=5001, debug=True) 
