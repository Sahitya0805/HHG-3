"""Pydantic schemas for FaceTrace API endpoints."""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class FaceDetectionResponse(BaseModel):
    success: bool
    face_detected: bool
    faces_found: int
    boxes: List[List[int]] = []
    primary_box: Optional[List[int]] = None
    confidence: Optional[float] = None
    confidence_percent: Optional[float] = None
    detection_method: Optional[str] = None
    embedding_generated: bool = False
    embedding_dimensions: int = 0
    embedding_model: Optional[str] = None
    embedding: List[float] = []
    sample_vector: List[float] = []
    primary_crop_b64: Optional[str] = None
    annotated_image_b64: Optional[str] = None
    warning: Optional[str] = None
    error: Optional[str] = None


class SearchRequest(BaseModel):
    embedding: List[float]
    image_b64: Optional[str] = None
    face_crop_b64: Optional[str] = None
    search_query: Optional[str] = None


class CandidateItem(BaseModel):
    rank: int
    url: str
    title: str
    source: str
    snippet: str
    image_url: Optional[str] = None
    candidate_face_preview: Optional[str] = None
    similarity: float
    similarity_percent: float
    match_category: str
    match_label: str
    is_match: bool
    color: str
    candidate_faces_found: int = 0
    candidate_detection_method: Optional[str] = None
    match_evidence: Optional[str] = None
    discovered_at: str


class SearchResponse(BaseModel):
    success: bool
    provider_name: str
    total_candidates: int
    candidates: List[CandidateItem] = []
    best_match: Optional[CandidateItem] = None
    metadata: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class HashRequest(BaseModel):
    url: Optional[str] = None
    metadata: Dict[str, Any]


class HashResponse(BaseModel):
    algorithm: str = "SHA-256"
    canonical_payload: str
    hash: str
    bytes32_hash: str
    byte_length: int = 32


class BlockchainStoreRequest(BaseModel):
    hash: str


class BlockchainStoreResponse(BaseModel):
    success: bool
    transaction_hash: str
    block_number: int
    gas_used: int
    submitter: str
    stored_hash: str
    timestamp: int
    mode: str
    contract_address: str


class BlockchainVerifyResponse(BaseModel):
    verified: bool
    on_chain_hash: Optional[str] = None
    timestamp: Optional[int] = None
    submitter: Optional[str] = None
    transaction_hash: Optional[str] = None
    block_number: Optional[int] = None
    mode: str
    contract_address: str


class TamperTestRequest(BaseModel):
    original_metadata: Dict[str, Any]
    tampered_metadata: Dict[str, Any]
    on_chain_hash: str


class TamperTestResponse(BaseModel):
    original_hash: str
    tampered_hash: str
    on_chain_hash: str
    is_tampered: bool
    tamper_detected: bool
    status: str
    message: str
    altered_fields: List[Dict[str, Any]] = []


class PipelineRunResponse(BaseModel):
    success: bool
    face: Dict[str, Any]
    search: Dict[str, Any]
    metadata: Dict[str, Any]
    fingerprint: Dict[str, Any]
    blockchain: Dict[str, Any]
    verification: Dict[str, Any]
    error: Optional[str] = None
