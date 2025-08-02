from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import requests
import os
from dotenv import load_dotenv
from verifier_js import has_nft  # Changed to use JavaScript-based verifier

load_dotenv()

app = Flask(__name__)

# Configure CORS to allow specific origins
allowed_origins = [
    "https://admin-q2j7.onrender.com",
    "https://meta-betties-frontend.onrender.com",
    "https://meta-betties-frontend-*.onrender.com",
    "http://localhost:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3001"
]

CORS(app, 
     origins=allowed_origins,
     methods=["GET", "POST", "OPTIONS"],
     allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
     supports_credentials=True,
     max_age=3600)

# UPDATE THIS URL to your bot server webhook
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://bot-server-kem4.onrender.com/verify_callback")

@app.route('/api/config')
def get_config():
    """Return configuration data including API keys"""
    response = jsonify({
        "helius_api_key": os.getenv("HELIUS_API_KEY", "")
    })
    
    # Add CORS headers for all origins
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,X-Requested-With')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    response.headers.add('Access-Control-Max-Age', '3600')
    
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
        
        # Add CORS headers for all origins
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,X-Requested-With')
        response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        response.headers.add('Access-Control-Max-Age', '3600')
        
        return response
        
    except Exception as e:
        print(f"❌ Error in verify_nft: {e}")
        response = jsonify({"error": str(e)})
        
        # Add CORS headers for all origins
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,X-Requested-With')
        response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        response.headers.add('Access-Control-Max-Age', '3600')
        
        return response, 500

@app.route('/api/addresses/<wallet_address>/nft-assets')
def get_nft_assets(wallet_address):
    """Get NFT assets for a wallet address"""
    try:
        api_key = request.args.get('api-key')
        if not api_key:
            return jsonify({"error": "API key required"}), 400
            
        # Helius API call to get NFTs
        url = f"https://api.helius.xyz/v0/addresses/{wallet_address}/nfts?api-key={api_key}"
        response = requests.get(url)
        
        if response.status_code == 200:
            nfts = response.json()
            result = jsonify(nfts)
            
            # Add CORS headers
            result.headers.add('Access-Control-Allow-Origin', '*')
            result.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,X-Requested-With')
            result.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
            result.headers.add('Access-Control-Allow-Credentials', 'true')
            result.headers.add('Access-Control-Max-Age', '3600')
            
            return result
        else:
            return jsonify({"error": "Failed to fetch NFTs"}), response.status_code
            
    except Exception as e:
        print(f"❌ Error getting NFT assets: {e}")
        response = jsonify({"error": str(e)})
        
        # Add CORS headers
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,X-Requested-With')
        response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        response.headers.add('Access-Control-Max-Age', '3600')
        
        return response, 500

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

# Add OPTIONS handler for preflight requests
@app.route('/api/config', methods=['OPTIONS'])
@app.route('/api/verify-nft', methods=['OPTIONS'])
@app.route('/api/addresses/<path:wallet_address>/nft-assets', methods=['OPTIONS'])
def handle_options(wallet_address=None):
    response = jsonify({})
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,X-Requested-With')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    response.headers.add('Access-Control-Max-Age', '3600')
    return response

if __name__ == '__main__':
    print("🚀 Starting API Server with JavaScript-based NFT verification...")
    app.run(host='0.0.0.0', port=5001, debug=True) 
