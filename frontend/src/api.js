const API_ENDPOINTS = [
  '/api',
  'http://localhost:8000/api',
  'http://127.0.0.1:8000/api',
];

async function fetchWithFallback(path, options = {}) {
  let lastError = null;

  for (const base of API_ENDPOINTS) {
    try {
      const url = `${base}${path}`;
      const res = await fetch(url, options);
      const contentType = res.headers.get('content-type') || '';
      
      let data = null;
      if (contentType.includes('application/json')) {
        data = await res.json();
      } else {
        const text = await res.text();
        try {
          data = JSON.parse(text);
        } catch {
          data = { error: text || 'Server returned invalid response' };
        }
      }

      if (!res.ok) {
        throw new Error(data?.detail || data?.error || `Request failed with status ${res.status}`);
      }
      return data;
    } catch (err) {
      lastError = err;
    }
  }

  throw lastError || new Error('Failed to connect to FaceTrace backend server.');
}

export async function checkHealth() {
  return fetchWithFallback('/health');
}

export async function uploadAndDetectFace(imageFile) {
  const formData = new FormData();
  formData.append('image', imageFile);

  return fetchWithFallback('/face', {
    method: 'POST',
    body: formData,
  });
}

export async function searchReverseImage(
  embedding,
  imageB64 = null,
  searchQuery = null,
  faceCropB64 = null,
  embeddingModel = null,
) {
  return fetchWithFallback('/search', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      embedding,
      embedding_model: embeddingModel,
      image_b64: imageB64,
      face_crop_b64: faceCropB64,
      search_query: searchQuery,
      search_hint: searchQuery,
      include_videos: true,
      max_sources: 8,
      max_candidates_per_source: 8,
      strict_face_match: true,
    }),
  });
}

export async function generateFingerprint(metadata) {
  return fetchWithFallback('/hash', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ metadata }),
  });
}

export async function storeOnBlockchain(hash) {
  return fetchWithFallback('/blockchain/store', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ hash }),
  });
}

export async function verifyOnBlockchain(hash) {
  return fetchWithFallback(`/blockchain/verify?hash=${encodeURIComponent(hash)}`);
}

export async function testTampering(originalMetadata, tamperedMetadata, onChainHash) {
  return fetchWithFallback('/tamper-test', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      original_metadata: originalMetadata,
      tampered_metadata: tamperedMetadata,
      on_chain_hash: onChainHash,
    }),
  });
}

export async function runFullPipeline(imageFile) {
  const formData = new FormData();
  formData.append('image', imageFile);

  return fetchWithFallback('/pipeline', {
    method: 'POST',
    body: formData,
  });
}
