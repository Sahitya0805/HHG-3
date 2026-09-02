// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title VerificationRegistry
 * @dev Simple tamper-evident registry storing cryptographic SHA-256 fingerprints
 * of public search discoveries for FaceTrace pipeline verification.
 */
contract VerificationRegistry {

    struct Record {
        bytes32 dataHash;
        uint256 timestamp;
        address submitter;
    }

    // Mapping from dataHash (SHA-256) to on-chain Record
    mapping(bytes32 => Record) public records;

    event RecordStored(bytes32 indexed dataHash, address indexed submitter, uint256 timestamp);

    /**
     * @dev Store a cryptographic hash on-chain
     * @param _hash The 32-byte SHA-256 hash of the canonical metadata
     */
    function storeRecord(bytes32 _hash) public returns (bool) {
        require(_hash != bytes32(0), "Invalid zero hash");
        records[_hash] = Record(
            _hash,
            block.timestamp,
            msg.sender
        );
        emit RecordStored(_hash, msg.sender, block.timestamp);
        return true;
    }

    /**
     * @dev Verify if a hash is registered on-chain
     * @param _hash The hash to check
     * @return True if recorded, False otherwise
     */
    function verifyRecord(bytes32 _hash) public view returns (bool) {
        return records[_hash].dataHash == _hash && records[_hash].timestamp > 0;
    }

    /**
     * @dev Retrieve record details
     * @param _hash The hash to query
     * @return dataHash The registered hash
     * @return timestamp Block timestamp when stored
     * @return submitter Wallet address of submitter
     */
    function getRecord(bytes32 _hash) public view returns (bytes32 dataHash, uint256 timestamp, address submitter) {
        Record memory r = records[_hash];
        return (r.dataHash, r.timestamp, r.submitter);
    }
}
