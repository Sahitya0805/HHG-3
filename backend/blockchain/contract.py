"""Smart Contract ABI and metadata definitions."""

VERIFICATION_REGISTRY_ABI = [
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": True,
                "internalType": "bytes32",
                "name": "dataHash",
                "type": "bytes32",
            },
            {
                "indexed": True,
                "internalType": "address",
                "name": "submitter",
                "type": "address",
            },
            {
                "indexed": False,
                "internalType": "uint256",
                "name": "timestamp",
                "type": "uint256",
            },
        ],
        "name": "RecordStored",
        "type": "event",
    },
    {
        "inputs": [
            {
                "internalType": "bytes32",
                "name": "_hash",
                "type": "bytes32",
            }
        ],
        "name": "getRecord",
        "outputs": [
            {
                "internalType": "bytes32",
                "name": "dataHash",
                "type": "bytes32",
            },
            {
                "internalType": "uint256",
                "name": "timestamp",
                "type": "uint256",
            },
            {
                "internalType": "address",
                "name": "submitter",
                "type": "address",
            },
        ],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [
            {
                "internalType": "bytes32",
                "name": "",
                "type": "bytes32",
            }
        ],
        "name": "records",
        "outputs": [
            {
                "internalType": "bytes32",
                "name": "dataHash",
                "type": "bytes32",
            },
            {
                "internalType": "uint256",
                "name": "timestamp",
                "type": "uint256",
            },
            {
                "internalType": "address",
                "name": "submitter",
                "type": "address",
            },
        ],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [
            {
                "internalType": "bytes32",
                "name": "_hash",
                "type": "bytes32",
            }
        ],
        "name": "storeRecord",
        "outputs": [
            {
                "internalType": "bool",
                "name": "",
                "type": "bool",
            }
        ],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [
            {
                "internalType": "bytes32",
                "name": "_hash",
                "type": "bytes32",
            }
        ],
        "name": "verifyRecord",
        "outputs": [
            {
                "internalType": "bool",
                "name": "",
                "type": "bool",
            }
        ],
        "stateMutability": "view",
        "type": "function",
    },
]
