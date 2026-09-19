import logging
from web3 import Web3

from app.config import settings

logger = logging.getLogger("blockchain")

w3 = Web3(Web3.HTTPProvider(settings.ethereum_rpc_url))


def get_latest_block_number() -> int:
    return w3.eth.block_number


def get_wallet_activity(address: str, from_block: int, to_block: int) -> dict:
    """
    Scans a block range for transactions sent FROM this wallet, and
    summarizes the activity: how many transactions, total ETH moved,
    and how many were contract interactions.

    Note: this is a simple polling scan, not an indexed lookup, so it's
    bounded by settings.lookback_blocks to stay fast on free-tier RPCs.
    """
    checksum_address = Web3.to_checksum_address(address)
    tx_count = 0
    total_value_eth = 0.0
    contract_interactions = 0

    for block_number in range(from_block, to_block + 1):
        try:
            block = w3.eth.get_block(block_number, full_transactions=True)
        except Exception as e:
            logger.warning(f"Could not fetch block {block_number}: {e}")
            continue

        for tx in block["transactions"]:
            if tx["from"].lower() != checksum_address.lower():
                continue

            tx_count += 1
            total_value_eth += float(w3.from_wei(tx["value"], "ether"))
            if tx["input"] not in ("0x", b""):
                contract_interactions += 1

    return {
        "tx_count": tx_count,
        "total_value_eth": total_value_eth,
        "contract_interactions": contract_interactions,
    }
