#!/usr/bin/env python3
"""Deploy VerificationRegistry to a running local Anvil EVM."""

import os
import sys

from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.blockchain.verifier import BlockchainVerifier


ANVIL_DEFAULT_PRIVATE_KEY = (
    "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"
)


def main() -> int:
    os.environ.setdefault("LOCAL_RPC_URL", "http://127.0.0.1:8545")
    os.environ.setdefault("PRIVATE_KEY", ANVIL_DEFAULT_PRIVATE_KEY)

    verifier = BlockchainVerifier(contract_address="", auto_deploy=False)
    result = verifier.deploy_contract()

    print("VerificationRegistry deployed")
    print(f"  RPC:              {verifier.rpc_url}")
    print(f"  Contract address: {result['contract_address']}")
    print(f"  Tx hash:          {result['transaction_hash']}")
    print(f"  Block number:     {result['block_number']}")
    print()
    print("Add this to .env:")
    print(f"LOCAL_RPC_URL={verifier.rpc_url}")
    print(f"PRIVATE_KEY={os.environ['PRIVATE_KEY']}")
    print(f"CONTRACT_ADDRESS={result['contract_address']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
