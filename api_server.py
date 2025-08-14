from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import requests
import os
from dotenv import load_dotenv
from verifier_python import has_nft  # Changed to use Python-based verifier
import time
import logging

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configure CORS to allow specific origins
allowed_origins = [
    "https://admin-q2j7.onrender.com",
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

# Performance settings
WEBHOOK_TIMEOUT = 10  # 10 seconds timeout for webhook calls
MAX_VERIFICATION_TIME = 25  # Maximum time for verification process

@app.route('/api/config')
def get_config():
    """Return configuration data including API keys"""
    response = jsonify({
        "helius_api_key": os.getenv("HELIUS_API_KEY", ""),
        "status": "operational",
        "version": "2.0.0"
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
    start_time = time.time()
    
    try:
        data = request.get_json()
        wallet_address = data.get('wallet_address')
        tg_id = data.get('tg_id')
        collection_id = data.get('collection_id')  # Add collection_id support
        
        if not wallet_address or not tg_id:
            return jsonify({"error": "Missing wallet_address or tg_id"}), 400
        
        logger.info(f"🔍 Verifying NFT ownership for wallet: {wallet_address}")
        logger.info(f"👤 Telegram ID: {tg_id}")
        if collection_id:
            logger.info(f"🎯 Collection ID: {collection_id}")
        else:
            logger.info(f"🔑 No collection filter (any NFT will pass)")
        
        # Check if verification is taking too long
        if time.time() - start_time > MAX_VERIFICATION_TIME:
            logger.warning(f"⚠️ Verification taking too long, aborting")
            return jsonify({"error": "Verification timeout", "has_nft": False}), 408
        
        # Verify NFT ownership with collection filter
        has_required_nft, nft_count = has_nft(wallet_address, collection_id)
        
        verification_time = time.time() - start_time
        logger.info(f"📊 Verification result: has_nft={has_required_nft}, count={nft_count}, time={verification_time:.2f}s")
        
        # Send webhook to bot server (non-blocking)
        webhook_data = {
            "tg_id": tg_id,
            "has_nft": has_required_nft,
            "username": f"user_{tg_id}",
            "nft_count": nft_count,
            "wallet_address": wallet_address,
            "verification_time": round(verification_time, 2)
        }
        
        logger.info(f"📦 Webhook data: {webhook_data}")
        
        # Send webhook asynchronously to prevent blocking
        try:
            webhook_response = requests.post(WEBHOOK_URL, json=webhook_data, timeout=WEBHOOK_TIMEOUT)
            if webhook_response.status_code == 200:
                logger.info(f"✅ Webhook sent successfully for user {tg_id}")
            else:
                logger.warning(f"❌ Webhook failed for user {tg_id}: {webhook_response.status_code}")
                logger.warning(f"📄 Webhook response: {webhook_response.text}")
        except Exception as e:
            logger.error(f"❌ Error sending webhook: {e}")
            # Don't fail the verification if webhook fails
        
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
            "message": message,
            "verification_time": round(verification_time, 2),
            "status": "success"
        })
        
        # Add CORS headers for all origins
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,X-Requested-With')
        response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        response.headers.add('Access-Control-Max-Age', '3600')
        
        return response
        
    except Exception as e:
        error_time = time.time() - start_time
        logger.error(f"❌ Error in verify_nft: {e}")
        logger.error(f"⏱️ Error occurred after {error_time:.2f}s")
        
        response = jsonify({
            "error": str(e),
            "has_nft": False,
            "status": "error",
            "verification_time": round(error_time, 2)
        })
        
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
            
        # Helius API call to get NFTs with timeout
        url = f"https://api.helius.xyz/v0/addresses/{wallet_address}/nfts?api-key={api_key}"
        response = requests.get(url, timeout=15)
        
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
        logger.error(f"❌ Error getting NFT assets: {e}")
        response = jsonify({"error": str(e)})
        
        # Add CORS headers
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,X-Requested-With')
        response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        response.headers.add('Access-Control-Max-Age', '3600')
        
        return response, 500

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": time.time(),
        "version": "2.0.0"
    })

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

# Add OPTIONS handler for preflight requests
@app.route('/api/config', methods=['OPTIONS'])
@app.route('/api/verify-nft', methods=['OPTIONS'])
@app.route('/api/addresses/<path:wallet_address>/nft-assets', methods=['OPTIONS'])
@app.route('/api/health', methods=['OPTIONS'])
def handle_options(wallet_address=None):
    response = jsonify({})
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,X-Requested-With')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    response.headers.add('Access-Control-Max-Age', '3600')
    return response

if __name__ == '__main__':
    logger.info("🚀 Starting API Server with Python-based NFT verification...")
    logger.info("📊 Performance optimizations enabled: caching, timeouts, error handling")
    app.run(host='0.0.0.0', port=5001, debug=True) 
