from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import requests
import os
from dotenv import load_dotenv
from verifier import has_nft

load_dotenv()

app = Flask(__name__)
CORS(app, origins=[
    "https://testverify.netlify.app",  # Your frontend domain
    "https://dancing-lollipop-fc680a.netlify.app",  # New frontend domain
    "https://*.netlify.app",
    "https://*.vercel.app",
    "https://*.railway.app",
    "http://localhost:3000",  # Local development
    "http://localhost:3001",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3001"
])

# UPDATE THIS URL to your bot server webhook
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://bot-server-h45u.onrender.com/verify_callback")

@app.route('/api/config')
def get_config():
    """Return configuration data including API keys"""
    return jsonify({
        "helius_api_key": os.getenv("HELIUS_API_KEY", "")
    })

@app.route('/api/verify-nft', methods=['POST'])
def verify_nft():
    try:
        data = request.json
        wallet_address = data.get('wallet_address')
        tg_id = data.get('tg_id')
        
        if not wallet_address or not tg_id:
            return jsonify({"error": "Missing wallet_address or tg_id"}), 400
        
        # Check NFT ownership using your verifier
        has_required_nft = has_nft(wallet_address)
        
        # Send result to bot's webhook
        webhook_data = {
            "tg_id": tg_id,
            "has_nft": has_required_nft,
            "username": f"user_{tg_id}"
        }
        
        try:
            webhook_response = requests.post(WEBHOOK_URL, json=webhook_data, timeout=10)
            if webhook_response.status_code == 200:
                print(f"Webhook sent successfully for user {tg_id}")
            else:
                print(f"Webhook failed for user {tg_id}: {webhook_response.status_code}")
        except Exception as e:
            print(f"Error sending webhook: {e}")
        
        return jsonify({
            "has_nft": has_required_nft,
            "wallet_address": wallet_address,
            "message": "NFT verification completed"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "service": "api"})

if __name__ == '__main__':
    port = int(os.getenv("PORT", 5001))
    app.run(host='0.0.0.0', port=port, debug=False) 
