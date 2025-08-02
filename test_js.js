const { Connection, PublicKey } = require("@solana/web3.js");
const { Metaplex } = require("@metaplex-foundation/js");

const RPC_ENDPOINT = "https://mainnet.helius-rpc.com";
const HELIUS_API_KEY = "6873bd5e-0b5d-49c4-a9ab-4e7febfd9cd3";
const FULL_RPC = `${RPC_ENDPOINT}/?api-key=${HELIUS_API_KEY}`;

const connection = new Connection(FULL_RPC);
const metaplex = new Metaplex(connection);

async function getSolBalance(walletAddress) {
  const pubkey = new PublicKey(walletAddress);
  const lamports = await connection.getBalance(pubkey);
  return lamports / 1e9; // convert lamports to SOL
}

async function listNFTs(walletAddress) {
  const owner = new PublicKey(walletAddress);
  const nfts = await metaplex.nfts().findAllByOwner({ owner });

  console.log(`\n🔎 NFTs (${nfts.length}) owned by ${walletAddress}:`);
  nfts.forEach((nft, i) => {
    console.log(`NFT #${i + 1}`);
    console.log("  Mint Address:", nft.mintAddress.toString());
    console.log("  Name:", nft.name);
    console.log("  URI:", nft.uri);
    console.log("----------------------------");
  });
  
  return nfts.length;
}

async function listSPLTokens(walletAddress) {
  const owner = new PublicKey(walletAddress);
  const tokenAccounts = await connection.getParsedTokenAccountsByOwner(owner, {
    programId: new PublicKey("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"),
  });

  // Filter out tokens with zero balance
  const nonZeroTokens = tokenAccounts.value.filter(({ account }) => {
    const amountInfo = account.data.parsed.info.tokenAmount;
    return amountInfo.uiAmount > 0;
  });

  console.log(`\n🔎 SPL Tokens (${nonZeroTokens.length}) owned by ${walletAddress}:`);
  nonZeroTokens.forEach(({ account }, i) => {
    const info = account.data.parsed.info;
    const mint = info.mint;
    const amount = info.tokenAmount.uiAmountString;
    console.log(`Token #${i + 1}:`);
    console.log("  Mint Address:", mint);
    console.log("  Amount:", amount);
    console.log("----------------------------");
  });
  
  return nonZeroTokens.length;
}

async function checkNFTVerification(walletAddress) {
  try {
    console.log(`\n🧾 Fetching data for wallet: ${walletAddress}`);

    const solBalance = await getSolBalance(walletAddress);
    console.log(`\n💰 SOL Balance: ${solBalance} SOL`);

    const nftCount = await listNFTs(walletAddress);
    console.log(`\n🎨 Total NFTs found: ${nftCount}`);

    const tokenCount = await listSPLTokens(walletAddress);
    console.log(`\n🪙 Total SPL Tokens found: ${tokenCount}`);

    if (nftCount > 0) {
      console.log(`\n✅ Wallet has ${nftCount} NFTs - verification successful`);
      return { has_nft: true, nft_count: nftCount };
    } else {
      console.log(`\n❌ Wallet has no NFTs - verification failed`);
      return { has_nft: false, nft_count: 0 };
    }

  } catch (error) {
    console.error(`\n❌ Error checking NFT verification: ${error}`);
    return { has_nft: false, nft_count: 0, error: error.message };
  }
}

// Get wallet address from command line arguments
const walletAddress = process.argv[2];

if (!walletAddress) {
  console.error("❌ Please provide a wallet address as argument");
  console.log("Usage: node test_js.js <wallet_address>");
  process.exit(1);
}

// Run the verification
checkNFTVerification(walletAddress)
  .then(result => {
    console.log("\n📊 Verification Result:", result);
    console.log("\n✅ Done.");
  })
  .catch(error => {
    console.error("\n❌ Error:", error);
    process.exit(1);
  }); 