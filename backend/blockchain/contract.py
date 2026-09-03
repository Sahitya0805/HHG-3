"""Smart Contract ABI and metadata definitions."""

VERIFICATION_REGISTRY_BYTECODE = (
    "0x"
    "608060405234801561001057600080fd5b50610599806100206000396000f3fe608060405234801561001057600080fd"
    "5b506004361061004c5760003560e01c806301e6472514610051578063213681cd146100835780634d408bcf146100b5"
    "578063671c0e5a146100e5575b600080fd5b61006b600480360381019061006691906103c8565b610115565b60405161"
    "007a9392919061045e565b60405180910390f35b61009d600480360381019061009891906103c8565b61015f565b6040"
    "516100ac9392919061045e565b60405180910390f35b6100cf60048036038101906100ca91906103c8565b61020b565b"
    "6040516100dc91906104b0565b60405180910390f35b6100ff60048036038101906100fa91906103c8565b61024d565b"
    "60405161010c91906104b0565b60405180910390f35b6000602052806000526040600020600091509050806000015490"
    "8060010154908060020160009054906101000a900473ffffffffffffffffffffffffffffffffffffffff16905083565b"
    "600080600080600080868152602001908152602001600020604051806060016040529081600082015481526020016001"
    "82015481526020016002820160009054906101000a900473ffffffffffffffffffffffffffffffffffffffff1673ffff"
    "ffffffffffffffffffffffffffffffffffff1673ffffffffffffffffffffffffffffffffffffffff1681525050905080"
    "6000015181602001518260400151935093509350509193909250565b6000816000808481526020019081526020016000"
    "20600001541480156102465750600080600084815260200190815260200160002060010154115b9050919050565b6000"
    "8060001b8203610294576040517f08c379a0000000000000000000000000000000000000000000000000000000008152"
    "60040161028b90610528565b60405180910390fd5b60405180606001604052808381526020014281526020013373ffff"
    "ffffffffffffffffffffffffffffffffffff168152506000808481526020019081526020016000206000820151816000"
    "01556020820151816001015560408201518160020160006101000a81548173ffffffffffffffffffffffffffffffffff"
    "ffffff021916908373ffffffffffffffffffffffffffffffffffffffff1602179055509050503373ffffffffffffffff"
    "ffffffffffffffffffffffff16827f90c094f999f8cedb7e5396d1979f131863f1f9d11033544f0ade5b77d037797142"
    "60405161037c9190610548565b60405180910390a360019050919050565b600080fd5b6000819050919050565b6103a5"
    "81610392565b81146103b057600080fd5b50565b6000813590506103c28161039c565b92915050565b60006020828403"
    "12156103de576103dd61038d565b5b60006103ec848285016103b3565b91505092915050565b6103fe81610392565b82"
    "525050565b6000819050919050565b61041781610404565b82525050565b600073ffffffffffffffffffffffffffffff"
    "ffffffffff82169050919050565b60006104488261041d565b9050919050565b6104588161043d565b82525050565b60"
    "0060608201905061047360008301866103f5565b610480602083018561040e565b61048d604083018461044f565b9493"
    "50505050565b60008115159050919050565b6104aa81610495565b82525050565b60006020820190506104c560008301"
    "846104a1565b92915050565b600082825260208201905092915050565b7f496e76616c6964207a65726f206861736800"
    "0000000000000000000000000000600082015250565b60006105126011836104cb565b915061051d826104dc565b6020"
    "82019050919050565b6000602082019050818103600083015261054181610505565b9050919050565b60006020820190"
    "5061055d600083018461040e565b9291505056fea2646970667358221220cc6aa5e3e4dae5759712987c78ad6b57046c"
    "bca55cadcbc4a867b88bec1d4ebf64736f6c63430008130033"
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
