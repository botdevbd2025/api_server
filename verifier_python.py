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

# Cache disabled - allow multiple verifications
# wallet_cache = {}

def get_wallet_balance(wallet_address: str) -> Optional[float]:
    """
    Fetch the SOL balance of a wallet using Helius API.
    Args:
        wallet_address: The Solana wallet address.
    Returns:
        SOL balance as a float, or None if the request fails.
    """
    # No cache - always fetch fresh data
    url = f"{HELIUS_API_URL}/addresses/{wallet_address}/balances?api-key={HELIUS_API_KEY}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        balance = data.get("nativeBalance", 0) / LAMPORTS_PER_SOL
        
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
    # No cache - always fetch fresh data
    
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
    
    print(f"🎨 Fetching fresh NFTs for wallet: {wallet_address}")
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
                grouping = item.get("grouping", [])
                collection = grouping[0].get("group_value", "Unknown") if grouping and len(grouping) > 0 else "Unknown"
                print(f"  Item {i+1}: token_standard = {token_standard}, interface = {interface}, collection = {collection}")
            
            # Improved NFT filtering - check multiple criteria
            nfts = []
            for item in all_items:
                # Check if it's an NFT based on multiple criteria
                is_nft = False
                
                # Criterion 1: Token standard
                token_standard = item.get("content", {}).get("metadata", {}).get("token_standard", "")
                if token_standard in ["NonFungible", "non-fungible", "NONFUNGIBLE"]:
                    is_nft = True
                
                # Criterion 2: Interface type
                interface = item.get("interface", "")
                if interface in ["V1_NFT", "MplCoreAsset"]:
                    is_nft = True
                
                # Criterion 3: Has files or name/symbol
                content = item.get("content", {})
                files = content.get("files", [])
                metadata = content.get("metadata", {})
                name = metadata.get("name", "")
                symbol = metadata.get("symbol", "")
                
                if files or name or symbol:
                    is_nft = True
                
                # Criterion 4: Check for NFT keywords in description
                description = metadata.get("description", "")
                if any(keyword in description.lower() for keyword in ["nft", "non-fungible", "token"]):
                    is_nft = True
                
                if is_nft:
                    nfts.append(item)
            
            # If collection_id is specified, filter by collection
            if collection_id:
                filtered_nfts = []
                for nft in nfts:
                    grouping = nft.get("grouping", [])
                    if grouping and len(grouping) > 0:
                        nft_collection = grouping[0].get("group_value")
                        if nft_collection == collection_id:
                            filtered_nfts.append(nft)
                nfts = filtered_nfts
                print(f"🎨 NFTs in collection {collection_id}: {len(nfts)}")
            else:
                print(f"🎨 Non-fungible tokens found: {len(nfts)}")
            
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
        collection_id: The collection ID to filter by (optional).
    Returns: (has_nft, nft_count)
    """
    try:
        print(f"🔍 Checking NFT ownership for wallet: {wallet_address}")
        if collection_id:
            print(f"🎯 Checking for collection: {collection_id}")
        else:
            print(f"🔑 Checking for any NFT (no collection filter)")
        
        # Get NFTs from wallet (with collection filter if specified)
        nfts = get_wallet_nfts_by_collection(wallet_address, collection_id)
        
        if nfts is None:
            print(f"❌ Failed to fetch NFT data")
            return False, 0
        
        nft_count = len(nfts)
        print(f"📊 Total NFTs found: {nft_count}")
        
        # Check if wallet has any NFTs
        if nft_count > 0:
            if collection_id:
                print(f"✅ Wallet has {nft_count} NFTs in collection {collection_id} - verification successful")
            else:
                print(f"✅ Wallet has {nft_count} NFTs - verification successful")
            return True, nft_count
        else:
            if collection_id:
                print(f"❌ Wallet has no NFTs in collection {collection_id} - verification failed")
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
