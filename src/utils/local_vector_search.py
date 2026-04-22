"""
Local vector search using pre-computed embeddings.
Loads textbook chunks from CSV files and provides similarity search.
"""
import csv
import json
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from google import genai
from google.genai import types

from config.settings import GCP_PROJECT_ID, GCP_LOCATION

DATA_DIR = Path(__file__).parent.parent.parent / "data"
METADATA_FILE = DATA_DIR / "textbook_chunks_metadata.csv"
EMBEDDINGS_FILE = DATA_DIR / "textbook_chunks_embeddings_768.csv"


@dataclass
class TextbookChunk:
    id: str
    subject: str
    year_level: str
    source_file: str
    chunk_type: str
    has_image: bool
    image_paths: List[str]
    clean_content: str
    header_metadata: Dict[str, Any]
    content_hash: str
    embedding: Optional[np.ndarray] = None


class LocalVectorSearch:
    """Local vector search using numpy and pre-computed embeddings."""
    
    def __init__(self):
        self.client = genai.Client(
            vertexai=True,
            project=GCP_PROJECT_ID,
            location=GCP_LOCATION
        )
        self.chunks: List[TextbookChunk] = []
        self.embedding_matrix: Optional[np.ndarray] = None
        self._load_data()
    
    def _load_data(self):
        """Load metadata and embeddings from CSV files."""
        if not METADATA_FILE.exists():
            raise FileNotFoundError(f"Metadata file not found: {METADATA_FILE}")
        if not EMBEDDINGS_FILE.exists():
            raise FileNotFoundError(f"Embeddings file not found: {EMBEDDINGS_FILE}")
        
        embeddings_map = {}
        with open(EMBEDDINGS_FILE, 'r') as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) >= 769:
                    chunk_id = row[0]
                    try:
                        embedding_values = [float(x) for x in row[1:769]]
                        embedding = np.array(embedding_values, dtype=np.float32)
                        embeddings_map[chunk_id] = embedding
                    except:
                        pass
        
        with open(METADATA_FILE, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                chunk_id = row['id']
                
                image_paths = []
                if row.get('image_paths'):
                    paths_str = row['image_paths'].strip('{}')
                    image_paths = [p.strip() for p in paths_str.split(',') if p.strip()]
                
                header_metadata = {}
                if row.get('header_metadata'):
                    try:
                        header_metadata = json.loads(row['header_metadata'])
                    except:
                        pass
                
                chunk = TextbookChunk(
                    id=chunk_id,
                    subject=row['subject'],
                    year_level=row['year_level'],
                    source_file=row['source_file'],
                    chunk_type=row['chunk_type'],
                    has_image=row['has_image'].lower() == 't',
                    image_paths=image_paths,
                    clean_content=row['clean_content'],
                    header_metadata=header_metadata,
                    content_hash=row.get('content_hash', ''),
                    embedding=embeddings_map.get(chunk_id)
                )
                self.chunks.append(chunk)
        
        valid_chunks = [c for c in self.chunks if c.embedding is not None]
        if valid_chunks:
            self.embedding_matrix = np.vstack([c.embedding for c in valid_chunks])
            self.embedding_matrix = self.embedding_matrix / np.linalg.norm(
                self.embedding_matrix, axis=1, keepdims=True
            )
            self.valid_chunks = valid_chunks
        else:
            raise ValueError("No valid embeddings found")
        
        print(f"Loaded {len(self.valid_chunks)} chunks with embeddings")
    
    async def generate_embedding(self, text: str) -> np.ndarray:
        """Generate embedding using Gemini with 768 dimensions."""
        print(f"[DEBUG-VEC] Generating embedding for text ({len(text)} chars)...")
        try:
            result = await self.client.aio.models.embed_content(
                model="text-embedding-004",
                contents=[text],
                config=types.EmbedContentConfig(
                    task_type="RETRIEVAL_QUERY",
                    output_dimensionality=768
                )
            )
            print(f"[DEBUG-VEC] Embedding generated successfully")
            embedding = np.array(result.embeddings[0].values, dtype=np.float32)
            return embedding / np.linalg.norm(embedding)
        except Exception as e:
            print(f"[DEBUG-VEC] Error generating embedding: {e}")
            raise
    
    async def search(
        self,
        query: str,
        subject: Optional[str] = None,
        limit: int = 5,
        threshold: float = 0.70
    ) -> List[Dict[str, Any]]:
        """
        Search for similar chunks using vector similarity.
        
        Args:
            query: Search query text
            subject: Optional filter by subject
            limit: Maximum results to return
            threshold: Minimum similarity score
        
        Returns:
            List of matching chunks with similarity scores
        """
        print(f"[DEBUG-VEC] Starting search for query: {query[:50]}...")
        query_embedding = await self.generate_embedding(query)
        
        print(f"[DEBUG-VEC] Computing similarities...")
        similarities = np.dot(self.embedding_matrix, query_embedding)
        
        results = []
        for idx, similarity in enumerate(similarities):
            chunk = self.valid_chunks[idx]
            
            if subject and chunk.subject.lower() != subject.lower():
                continue
            
            if similarity < threshold:
                continue
            
            results.append({
                'id': chunk.id,
                'subject': chunk.subject,
                'year_level': chunk.year_level,
                'source_file': chunk.source_file,
                'chunk_type': chunk.chunk_type,
                'has_image': chunk.has_image,
                'image_paths': chunk.image_paths,
                'content': chunk.clean_content[:500],
                'similarity': float(similarity),
                'header_metadata': chunk.header_metadata
            })
        
        print(f"[DEBUG-VEC] Found {len(results)} matches above threshold {threshold}")
        results.sort(key=lambda x: x['similarity'], reverse=True)
        return results[:limit]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about loaded data."""
        stats = {
            'total_chunks': len(self.chunks),
            'valid_embeddings': len(self.valid_chunks),
            'by_subject': {},
            'by_year': {}
        }
        
        for chunk in self.valid_chunks:
            stats['by_subject'][chunk.subject] = stats['by_subject'].get(chunk.subject, 0) + 1
            stats['by_year'][chunk.year_level] = stats['by_year'].get(chunk.year_level, 0) + 1
        
        return stats


if __name__ == "__main__":
    import asyncio
    
    async def test():
        search = LocalVectorSearch()
        print("\nStats:", search.get_stats())
        
        print("\nSearching for 'benzene aromatic compound'...")
        results = await search.search("benzene aromatic compound", subject="chemistry")
        for r in results:
            print(f"  - {r['subject']}/{r['year_level']}: sim={r['similarity']:.3f}")
            print(f"    Images: {r['image_paths'][:2]}")
    
    asyncio.run(test())
