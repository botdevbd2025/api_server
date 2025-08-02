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

def get_wallet_nfts_alternative(wallet_address: str) -> Optional[List[Dict]]:
    """
    Alternative method using Helius v0 API for NFT detection
    """
    try:
        url = f"https://api.helius.xyz/v0/addresses/{wallet_address}/nfts?api-key={HELIUS_API_KEY}"
        
        print(f"🎨 Fetching NFTs using alternative method for: {wallet_address}")
        
        response = requests.get(url)
        print(f"📊 Alternative API Response Status: {response.status_code}")
        
        if response.status_code == 200:
            nfts = response.json()
            print(f"✅ Alternative method found {len(nfts)} NFTs")
            return nfts
        else:
            print(f"❌ Alternative API failed: {response.status_code}")
            return []
            
    except Exception as e:
        print(f"❌ Error in alternative NFT fetch: {e}")
        return []

def get_wallet_nfts_by_collection(wallet_address: str, collection_id: str = None) -> Optional[List[Dict]]:
    """
    Fetch NFTs owned by a wallet for a specific collection using Helius DAS API.
    Args:
        wallet_address: The Solana wallet address.
        collection_id: The collection ID to filter by (optional).
    Returns:
        List of NFTs, or None if the request fails.
    """
    # Check cache first
    cache_key = f"{wallet_address}_{collection_id}" if collection_id else wallet_address
    if cache_key in wallet_cache and 'nfts' in wallet_cache[cache_key]:
        print(f"🎨 Using cached NFTs for {wallet_address}")
        return wallet_cache[cache_key]['nfts']
    
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
    if collection_id:
        print(f"🎯 Filtering by collection: {collection_id}")
    
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
                collection = item.get("grouping", [{}])[0].get("group_value", "Unknown") if item.get("grouping") else "Unknown"
                print(f"  Item {i+1}: token_standard = {token_standard}, interface = {interface}, collection = {collection}")
            
            # Filter for non-fungible tokens
            nfts = [item for item in all_items 
                   if item.get("content", {}).get("metadata", {}).get("token_standard") in ["NonFungible", "non-fungible", "NONFUNGIBLE"]]
            
            # If collection_id is specified, filter by collection
            if collection_id:
                nfts = [nft for nft in nfts 
                       if nft.get("grouping", [{}])[0].get("group_value") == collection_id]
                print(f"🎨 NFTs in collection {collection_id}: {len(nfts)}")
            else:
                print(f"🎨 Non-fungible tokens found: {len(nfts)}")
            
            # Cache the result
            if cache_key not in wallet_cache:
                wallet_cache[cache_key] = {}
            wallet_cache[cache_key]['nfts'] = nfts
            
            return nfts
        else:
            print(f"❌ No 'result' or 'items' in response")
            return []
    except requests.RequestException as e:
        print(f"❌ Error fetching NFTs: {e}")
        return None

def has_nft_python(wallet_address: str, collection_id: str = None) -> Tuple[bool, int]:
    """
    Check if wallet has NFTs using Python-based approach (replacing JavaScript)
    Args:
        wallet_address: The Solana wallet address.
        collection_id: The collection ID to filter by (optional) - IGNORED for now
    Returns: (has_nft, nft_count)
    """
    try:
        print(f"🔍 Checking NFT ownership for wallet: {wallet_address}")
        print(f"🔑 Using Python-based approach...")
        
        # Get NFTs from wallet (ignore collection_id for now)
        nfts = get_wallet_nfts_by_collection(wallet_address)  # No collection filter
        
        if nfts is None:
            print(f"❌ Failed to fetch NFT data")
            return False, 0
        
        nft_count = len(nfts)
        print(f"📊 Total NFTs found: {nft_count}")
        
        # Check if wallet has any NFTs (any NFT will pass)
        if nft_count > 0:
            print(f"✅ Wallet has {nft_count} NFTs - verification successful")
            return True, nft_count
        else:
            print(f"❌ Wallet has no NFTs - verification failed")
            return False, 0
            
    except Exception as e:
        print(f"❌ Error in Python NFT verification: {e}")
        return False, 0

def has_nft(wallet_address: str, collection_id: str = None) -> Tuple[bool, int]:
    """
    Main function - use Python approach instead of JavaScript
    Args:
        wallet_address: The Solana wallet address.
        collection_id: The collection ID to filter by (optional).
    Returns: (has_nft, nft_count)
    """
    return has_nft_python(wallet_address, collection_id) 
