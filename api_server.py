from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import requests
import os
from dotenv import load_dotenv
from verifier_python import has_nft  # Changed to use Python-based verifier

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
    helius_api_key = os.getenv("HELIUS_API_KEY", "")
    
    # Log the API key status for debugging
    if helius_api_key:
        print(f"✅ HELIUS_API_KEY loaded successfully (length: {len(helius_api_key)})")
        print(f"🔑 API Key preview: {helius_api_key[:8]}...{helius_api_key[-4:]}")
    else:
        print("❌ HELIUS_API_KEY not found in environment variables!")
        print("💡 Please set HELIUS_API_KEY in your environment")
    
    response = jsonify({
        "helius_api_key": helius_api_key,
        "api_key_status": "loaded" if helius_api_key else "missing"
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
    """Verify NFT ownership for a wallet address"""
    try:
        data = request.get_json()
        wallet_address = data.get('wallet_address')
        tg_id = data.get('tg_id')
        collection_id = data.get('collection_id')  # Add collection_id support
        
        if not wallet_address or not tg_id:
            return jsonify({"error": "Missing wallet_address or tg_id"}), 400
        
        print(f"🔍 Verifying NFT ownership for wallet: {wallet_address}")
        print(f"👤 Telegram ID: {tg_id}")
        if collection_id:
            print(f"🎯 Collection ID: {collection_id}")
        else:
            print(f"🔑 No collection filter (any NFT will pass)")
        
        # Verify NFT ownership with collection filter
        has_required_nft, nft_count = has_nft(wallet_address, collection_id)
        
        print(f"📊 Verification result: has_nft={has_required_nft}, count={nft_count}")
        
        # Send webhook to bot server
        webhook_data = {
            "tg_id": tg_id,
            "has_nft": has_required_nft,
            "username": f"user_{tg_id}",
            "nft_count": nft_count,
            "wallet_address": wallet_address
        }
        
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
        
        # Prepare response message
        if collection_id:
            message = f"NFT verification completed (collection: {collection_id})"
        else:
            message = "NFT verification completed (any NFT will pass)"
        
        response = jsonify({
            "has_nft": has_required_nft,
            "nft_count": nft_count,
            "wallet_address": wallet_address,
            "collection_id": collection_id,
            "message": message
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
        print(f"🔍 NFT assets request for wallet: {wallet_address}")
        print(f"🔑 API key received: {'✅ Present' if api_key else '❌ Missing'}")
        
        if not api_key:
            print("❌ API key missing from request")
            return jsonify({"error": "API key required", "details": "No api-key parameter provided"}), 400
        
        if len(api_key) < 10:
            print(f"❌ API key too short: {len(api_key)} characters")
            return jsonify({"error": "Invalid API key", "details": "API key appears to be invalid"}), 400
            
        print(f"✅ API key validation passed, length: {len(api_key)}")
        
        # Helius API call to get NFTs
        url = f"https://api.helius.xyz/v0/addresses/{wallet_address}/nfts?api-key={api_key}"
        print(f"🌐 Calling Helius API: {url[:50]}...")
        
        response = requests.get(url, timeout=30)
        print(f"📊 Helius API response status: {response.status_code}")
        
        if response.status_code == 200:
            nfts = response.json()
            print(f"✅ Successfully fetched {len(nfts)} NFTs from Helius")
            result = jsonify(nfts)
            
            # Add CORS headers
            result.headers.add('Access-Control-Allow-Origin', '*')
            result.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,X-Requested-With')
            result.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
            result.headers.add('Access-Control-Allow-Credentials', 'true')
            result.headers.add('Access-Control-Max-Age', '3600')
            
            return result
        else:
            error_msg = f"Helius API returned status {response.status_code}"
            try:
                error_data = response.json()
                if 'error' in error_data:
                    error_msg += f": {error_data['error']}"
            except:
                error_msg += f": {response.text[:100]}"
            
            print(f"❌ Helius API error: {error_msg}")
            return jsonify({"error": "Failed to fetch NFTs", "details": error_msg}), response.status_code
            
    except requests.exceptions.Timeout:
        print("❌ Helius API request timed out")
        return jsonify({"error": "Request timeout", "details": "Helius API request timed out"}), 408
    except requests.exceptions.RequestException as e:
        print(f"❌ Helius API request failed: {e}")
        return jsonify({"error": "Request failed", "details": str(e)}), 500
    except Exception as e:
        print(f"❌ Unexpected error in get_nft_assets: {e}")
        response = jsonify({"error": str(e), "details": "Unexpected server error"})
        
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
    print("🚀 Starting API Server with Python-based NFT verification...")
    app.run(host='0.0.0.0', port=5001, debug=True) 
