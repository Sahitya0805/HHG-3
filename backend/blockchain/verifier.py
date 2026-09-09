"""Blockchain verification and storage interface using a real local EVM."""

import os
from typing import Any, Dict, Optional

from web3 import Web3

from backend.blockchain.contract import (
    VERIFICATION_REGISTRY_ABI,
    VERIFICATION_REGISTRY_BYTECODE,
)


class BlockchainConfigurationError(RuntimeError):
    """Raised when no usable EVM configuration is available."""


class BlockchainVerifier:
    """Stores and verifies metadata hashes in a deployed EVM registry contract."""

    DEFAULT_LOCAL_RPC_URL = "http://127.0.0.1:8545"

    def __init__(
        self,
        rpc_url: Optional[str] = None,
        private_key: Optional[str] = None,
        contract_address: Optional[str] = None,
        auto_deploy: Optional[bool] = None,
    ):
        self.rpc_url = rpc_url or os.getenv("LOCAL_RPC_URL") or os.getenv("RPC_URL") or self.DEFAULT_LOCAL_RPC_URL
        self.private_key = private_key or os.getenv("PRIVATE_KEY", "")
        self.contract_address = contract_address or os.getenv("CONTRACT_ADDRESS", "")
        self.auto_deploy = (
            auto_deploy
            if auto_deploy is not None
            else os.getenv("AUTO_DEPLOY_CONTRACT", "").lower() in {"1", "true", "yes"}
        )

        self.w3: Optional[Web3] = None
        self.contract = None
        self.account = None
        self.connection_error: Optional[str] = None

        self._connect()

    def _connect(self) -> None:
        try:
            self.w3 = Web3(Web3.HTTPProvider(self.rpc_url, request_kwargs={"timeout": 10}))
            if not self.w3.is_connected():
                self.connection_error = f"Could not connect to EVM RPC at {self.rpc_url}."
                return

            if not self.private_key:
                self.connection_error = "PRIVATE_KEY is required for blockchain transactions."
                return

            self.account = self.w3.eth.account.from_key(self.private_key)
            if not self.contract_address and self.auto_deploy:
                self.contract_address = self.deploy_contract()["contract_address"]

            if self.contract_address:
                code = self.w3.eth.get_code(Web3.to_checksum_address(self.contract_address))
                if not code:
                    self.connection_error = (
                        f"No contract bytecode found at {self.contract_address}. "
                        "Redeploy with `python scripts/deploy_contract.py`."
                    )
                    return
                self.contract = self.w3.eth.contract(
                    address=Web3.to_checksum_address(self.contract_address),
                    abi=VERIFICATION_REGISTRY_ABI,
                )
                self.connection_error = None
            else:
                self.connection_error = "CONTRACT_ADDRESS is required. Run scripts/deploy_contract.py first."
        except Exception as exc:
            self.connection_error = str(exc)

    @property
    def network_info(self) -> Dict[str, Any]:
        """Returns active network information."""
        connected = bool(self.w3 and self.w3.is_connected() and self.account)
        return {
            "mode": "local_anvil_evm",
            "chain_id": self.w3.eth.chain_id if connected and self.w3 else None,
            "rpc_url": self.rpc_url,
            "contract_address": self.contract_address or None,
            "wallet_address": self.account.address if self.account else None,
            "connected": connected and self.contract is not None,
            "error": self.connection_error,
        }

    def _require_ready(self) -> None:
        if not (self.w3 and self.w3.is_connected()):
            raise BlockchainConfigurationError(
                f"Anvil RPC is unavailable at {self.rpc_url}. Start it with `anvil --host 127.0.0.1 --port 8545`."
            )
        if not self.account:
            raise BlockchainConfigurationError("PRIVATE_KEY is required in .env.")
        if not self.contract:
            raise BlockchainConfigurationError("CONTRACT_ADDRESS is required. Run `python scripts/deploy_contract.py`.")

    def _normalize_hash(self, hash_str: str) -> bytes:
        """Ensure hash is 32 bytes binary."""
        clean = hash_str.lower().strip()
        if clean.startswith("0x"):
            clean = clean[2:]
        if len(clean) != 64:
            raise ValueError(f"Hash must be 64 hexadecimal characters, got {len(clean)}")
        return bytes.fromhex(clean)

    def _to_0x_hex(self, value: Any) -> str:
        hex_value = value.hex() if hasattr(value, "hex") else str(value)
        return hex_value if hex_value.startswith("0x") else "0x" + hex_value

    def _transaction_fee_fields(self) -> Dict[str, int]:
        assert self.w3 is not None
        latest = self.w3.eth.get_block("latest")
        if "baseFeePerGas" in latest:
            return {
                "maxFeePerGas": self.w3.to_wei("2", "gwei"),
                "maxPriorityFeePerGas": self.w3.to_wei("1", "gwei"),
            }
        return {"gasPrice": self.w3.to_wei("1", "gwei")}

    def _sign_and_send(self, tx: Dict[str, Any]):
        assert self.w3 is not None
        signed_tx = self.w3.eth.account.sign_transaction(tx, self.private_key)
        raw_tx = getattr(signed_tx, "raw_transaction", None) or signed_tx.rawTransaction
        tx_hash = self.w3.eth.send_raw_transaction(raw_tx)
        return self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)

    def deploy_contract(self) -> Dict[str, Any]:
        """Deploy VerificationRegistry to the configured local EVM."""
        if not (self.w3 and self.w3.is_connected()):
            raise BlockchainConfigurationError(
                f"Anvil RPC is unavailable at {self.rpc_url}. Start it before deploying."
            )
        if not self.private_key:
            raise BlockchainConfigurationError("PRIVATE_KEY is required to deploy the contract.")

        self.account = self.account or self.w3.eth.account.from_key(self.private_key)
        contract_factory = self.w3.eth.contract(
            abi=VERIFICATION_REGISTRY_ABI,
            bytecode=VERIFICATION_REGISTRY_BYTECODE,
        )
        nonce = self.w3.eth.get_transaction_count(self.account.address)
        tx_params = {
            "from": self.account.address,
            "nonce": nonce,
            **self._transaction_fee_fields(),
        }
        estimated_gas = contract_factory.constructor().estimate_gas({"from": self.account.address})
        tx_params["gas"] = int(estimated_gas * 1.4)
        tx = contract_factory.constructor().build_transaction(tx_params)
        receipt = self._sign_and_send(tx)
        if receipt.status != 1 or not receipt.contractAddress:
            raise BlockchainConfigurationError("VerificationRegistry deployment transaction failed.")

        code = self.w3.eth.get_code(receipt.contractAddress)
        if not code:
            raise BlockchainConfigurationError("Deployment finished, but no contract bytecode exists at the address.")

        self.contract_address = receipt.contractAddress
        self.contract = self.w3.eth.contract(
            address=Web3.to_checksum_address(self.contract_address),
            abi=VERIFICATION_REGISTRY_ABI,
        )
        self.connection_error = None

        return {
            "success": receipt.status == 1,
            "transaction_hash": self._to_0x_hex(receipt.transactionHash),
            "block_number": receipt.blockNumber,
            "gas_used": receipt.gasUsed,
            "contract_address": self.contract_address,
            "deployer": self.account.address,
            "mode": "local_anvil_evm",
        }

    def store_hash(self, hash_str: str) -> Dict[str, Any]:
        """Store SHA-256 fingerprint hash on-chain."""
        self._require_ready()
        assert self.w3 is not None and self.contract is not None and self.account is not None

        hash_bytes = self._normalize_hash(hash_str)
        hash_hex_standard = "0x" + hash_bytes.hex()
        nonce = self.w3.eth.get_transaction_count(self.account.address)
        tx = self.contract.functions.storeRecord(hash_bytes).build_transaction(
            {
                "from": self.account.address,
                "nonce": nonce,
                "gas": 180_000,
                **self._transaction_fee_fields(),
            }
        )
        receipt = self._sign_and_send(tx)
        record = self.contract.functions.getRecord(hash_bytes).call()

        return {
            "success": receipt.status == 1,
            "transaction_hash": self._to_0x_hex(receipt.transactionHash),
            "block_number": receipt.blockNumber,
            "gas_used": receipt.gasUsed,
            "submitter": record[2],
            "stored_hash": hash_hex_standard,
            "timestamp": record[1],
            "mode": "local_anvil_evm",
            "contract_address": self.contract_address,
        }

    def verify_hash(self, hash_str: str) -> Dict[str, Any]:
        """Verify if hash exists on-chain and retrieve details."""
        self._require_ready()
        assert self.contract is not None

        hash_bytes = self._normalize_hash(hash_str)
        hash_hex_standard = "0x" + hash_bytes.hex()
        is_valid = self.contract.functions.verifyRecord(hash_bytes).call()
        if is_valid:
            record = self.contract.functions.getRecord(hash_bytes).call()
            return {
                "verified": True,
                "on_chain_hash": "0x" + record[0].hex(),
                "timestamp": record[1],
                "submitter": record[2],
                "mode": "local_anvil_evm",
                "contract_address": self.contract_address,
            }

        return {
            "verified": False,
            "on_chain_hash": None,
            "timestamp": None,
            "submitter": None,
            "mode": "local_anvil_evm",
            "contract_address": self.contract_address,
        }
