import requests
import os
from typing import Tuple, Optional, List, Dict
from dotenv import load_dotenv

load_dotenv()

# Configuration
HELIUS_API_KEY = os.getenv("HELIUS_API_KEY", "6873bd5e-0b5d-49c4-a9ab-4e7febfd9cd3")
HELIUS_API_URL = "https://api.helius.xyz/v0"  # Keep v0 for balance
DAS_API_URL = "https://mainnet.helius-rpc.com"  # DAS API endpoint
LAMPORTS_PER_SOL = 1_000_000_000  # Conversion factor for SOL (1 SOL = 1e9 lamports)

# Cache for API responses to avoid repeated calls
wallet_cache = {}

def get_wallet_balance(wallet_address: str) -> Optional[float]:
    """
    Fetch the SOL balance of a wallet using Helius API.
    Args:
        wallet_address: The Solana wallet address.
    Returns:
        SOL balance as a float, or None if the request fails.
    """
    # Check cache first
    if wallet_address in wallet_cache and 'balance' in wallet_cache[wallet_address]:
        print(f"💰 Using cached SOL balance for {wallet_address}")
        return wallet_cache[wallet_address]['balance']
    
    url = f"{HELIUS_API_URL}/addresses/{wallet_address}/balances?api-key={HELIUS_API_KEY}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        balance = data.get("nativeBalance", 0) / LAMPORTS_PER_SOL
        
        # Cache the result
        if wallet_address not in wallet_cache:
            wallet_cache[wallet_address] = {}
        wallet_cache[wallet_address]['balance'] = balance
        
        return balance
    except requests.RequestException as e:
        print(f"Error fetching wallet balance: {e}")
        return None

def get_wallet_nfts(wallet_address: str) -> Optional[List[Dict]]:
    """
    Fetch NFTs owned by a wallet using Helius DAS API.
    Args:
        wallet_address: The Solana wallet address.
    Returns:
        List of NFTs, or None if the request fails.
    """
    # Check cache first
    if wallet_address in wallet_cache and 'nfts' in wallet_cache[wallet_address]:
        print(f"🎨 Using cached NFTs for {wallet_address}")
        return wallet_cache[wallet_address]['nfts']
    
    # Using Helius DAS API for NFTs - simpler approach
    url = f"{DAS_API_URL}/?api-key={HELIUS_API_KEY}"
    payload = {
        "jsonrpc": "2.0",
        "id": "my-id",
        "method": "searchAssets",
        "params": {
            "ownerAddress": wallet_address
        }
    }
    
    print(f"🎨 Fetching NFTs for wallet: {wallet_address}")
    
    try:
        response = requests.post(url, json=payload)
        print(f"📊 Response Status: {response.status_code}")
        
        response.raise_for_status()
        data = response.json()
        
        # Check for error in response
        if "error" in data:
            print(f"❌ API Error: {data['error']}")
            return None
        
        if "result" in data and "items" in data["result"]:
            all_items = data["result"]["items"]
            print(f"📦 Total items received: {len(all_items)}")
            
            # Log first few items for debugging
            for i, item in enumerate(all_items[:3]):
                token_standard = item.get("content", {}).get("metadata", {}).get("token_standard", "Unknown")
                interface = item.get("interface", "Unknown")
                print(f"  Item {i+1}: token_standard = {token_standard}, interface = {interface}")
            
            # Filter for non-fungible tokens - try different possible values
            nfts = [item for item in all_items 
                   if item.get("content", {}).get("metadata", {}).get("token_standard") in ["NonFungible", "non-fungible", "NONFUNGIBLE"]]
            
            print(f"🎨 Non-fungible tokens found: {len(nfts)}")
            
            # Cache the result
            if wallet_address not in wallet_cache:
                wallet_cache[wallet_address] = {}
            wallet_cache[wallet_address]['nfts'] = nfts
            
            return nfts
        else:
            print(f"❌ No 'result' or 'items' in response")
            return []
    except requests.RequestException as e:
        print(f"❌ Error fetching NFTs: {e}")
        return None

def has_nft_python(wallet_address: str) -> Tuple[bool, int]:
    """
    Check if wallet has NFTs using Python-based approach (replacing JavaScript)
    Returns: (has_nft, nft_count)
    """
    try:
        print(f"🔍 Checking NFT ownership for wallet: {wallet_address}")
        print(f"🔑 Using Python-based approach...")
        
        # Get NFTs from wallet
        nfts = get_wallet_nfts(wallet_address)
        
        if nfts is None:
            print(f"❌ Failed to fetch NFT data")
            return False, 0
        
        nft_count = len(nfts)
        print(f"📊 Total NFTs found: {nft_count}")
        
        # Check if wallet has any NFTs (removed specific collection check)
        if nft_count > 0:
            print(f"✅ Wallet has {nft_count} NFTs - verification successful")
            return True, nft_count
        else:
            print(f"❌ Wallet has no NFTs - verification failed")
            return False, 0
            
    except Exception as e:
        print(f"❌ Error in Python NFT verification: {e}")
        return False, 0

def has_nft(wallet_address: str) -> Tuple[bool, int]:
    """
    Main function - use Python approach instead of JavaScript
    Returns: (has_nft, nft_count)
    """
    return has_nft_python(wallet_address) 