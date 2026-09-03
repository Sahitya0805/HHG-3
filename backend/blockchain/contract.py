"""Smart Contract ABI and metadata definitions."""

VERIFICATION_REGISTRY_BYTECODE = (
    "0x608060405234801561000f575f80fd5b506105668061001d5f395ff3fe608060405234801561000f"
    "575f80fd5b506004361061004a575f3560e01c806301e647251461004e578063213681cd1461008057"
    "80634d408bcf146100b2578063671c0e5a146100e2575b5f80fd5b61006860048036038101906100"
    "6391906103a6565b610112565b60405161007793929190610437565b60405180910390f35b61009a"
    "600480360381019061009591906103a6565b610156565b6040516100a993929190610437565b604051"
    "80910390f35b6100cc60048036038101906100c791906103a6565b6101fb565b6040516100d99190"
    "610486565b60405180910390f35b6100fc60048036038101906100f791906103a6565b610236565b"
    "6040516101099190610486565b60405180910390f35b5f602052805f5260405f205f91509050805f"
    "015490806001015490806002015f9054906101000a900473ffffffffffffffffffffffffffffffffffff"
    "ffff16905083565b5f805f805f808681526020019081526020015f20604051806060016040529081"
    "5f820154815260200160018201548152602001600282015f9054906101000a900473ffffffffffffff"
    "ffffffffffffffffffffffffff1673ffffffffffffffffffffffffffffffffffffffff1673ffffffffffff"
    "ffffffffffffffffffffffffffff16815250509050805f01518160200151826040015193509350935050"
    "9193909250565b5f815f808481526020019081526020015f205f015414801561022f57505f805f84"
    "81526020019081526020015f2060010154115b9050919050565b5f805f1b820361027b576040517f"
    "08c379a0000000000000000000000000000000000000000000000000000000008152600401610272"
    "906104f9565b60405180910390fd5b60405180606001604052808381526020014281526020013373ff"
    "ffffffffffffffffffffffffffffffffffffff168152505f808481526020019081526020015f205f82"
    "0151815f0155602082015181600101556040820151816002015f6101000a81548173ffffffffffffff"
    "ffffffffffffffffffffffffff021916908373ffffffffffffffffffffffffffffffffffffffff16021790"
    "55509050503373ffffffffffffffffffffffffffffffffffffffff16827f90c094f999f8cedb7e5396"
    "d1979f131863f1f9d11033544f0ade5b77d03779714260405161035e9190610517565b60405180"
    "910390a360019050919050565b5f80fd5b5f819050919050565b61038581610373565b811461038f"
    "575f80fd5b50565b5f813590506103a08161037c565b92915050565b5f602082840312156103bb"
    "576103ba61036f565b5b5f6103c884828501610392565b91505092915050565b6103da81610373"
    "565b82525050565b5f819050919050565b6103f2816103e0565b82525050565b5f73ffffffffff"
    "ffffffffffffffffffffffffffffff82169050919050565b5f610421826103f8565b9050919050565b"
    "61043181610417565b82525050565b5f60608201905061044a5f8301866103d1565b6104576020"
    "8301856103e9565b6104646040830184610428565b949350505050565b5f8115159050919050565b"
    "6104808161046c565b82525050565b5f6020820190506104995f830184610477565b92915050565b"
    "5f82825260208201905092915050565b7f496e76616c6964207a65726f2068617368000000000000"
    "00000000000000000005f82015250565b5f6104e360118361049f565b91506104ee826104af565b"
    "602082019050919050565b5f6020820190508181035f830152610510816104d7565b905091905056"
    "5b5f60208201905061052a5f8301846103e9565b9291505056fea2646970667358221220a5c1c4"
    "2516fc5bf9ea5da40f5584cbd9699010266db887a8302e0be2e752300564736f6c63430008140033"
)

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
