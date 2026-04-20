"""
Vector matcher for finding similar textbook content with images.
"""
from typing import List, Dict, Any, Optional
import google.generativeai as genai
from config.settings import GEMINI_MODEL, SIMILARITY_THRESHOLD_HIGH, SIMILARITY_THRESHOLD_LOW
from src.database.connection import get_textbook_chunks_with_images


class VectorMatcher:
    """Match MCQs to textbook content with images using vector similarity."""
    
    def __init__(self):
        self.model = genai.GenerativeModel(GEMINI_MODEL)
    
    async def find_reference(
        self,
        question_text: str,
        subject: str = None
    ) -> Optional[Dict[str, Any]]:
        """
        Find best matching textbook chunk with image.
        
        Args:
            question_text: MCQ question to match
            subject: Optional subject filter
            
        Returns:
            Match result with image path and similarity score, or None
        """
        try:
            # Generate embedding for question
            embedding = await self._generate_embedding(question_text)
            
            # Search textbook chunks with images
            results = await get_textbook_chunks_with_images(
                query_embedding=embedding,
                subject=subject,
                limit=5,
                threshold=SIMILARITY_THRESHOLD_LOW
            )
            
            if not results:
                return None
            
            # Get best match
            best_match = results[0]
            
            # Get image path
            if best_match.get('image_paths'):
                image_path = best_match['image_paths'][0]
            else:
                return None
            
            return {
                'chunk_id': best_match['id'],
                'image_path': image_path,
                'similarity': best_match['similarity'],
                'content': best_match['clean_content'],
                'source_file': best_match['source_file'],
                'confidence': self._get_confidence(best_match['similarity'])
            }
            
        except Exception as e:
            print(f"Error finding reference: {e}")
            return None
    
    async def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding using Gemini."""
        # Use embedding model
        try:
            from google import genai as genai_client
            from google.genai import types
            
            client = genai_client.Client()
            
            result = await client.aio.models.embed_content(
                model="text-embedding-004",
                contents=[text],
                config=types.EmbedContentConfig(
                    task_type="RETRIEVAL_QUERY",
                    output_dimensionality=768
                )
            )
            
            return result.embeddings[0].values
            
        except Exception as e:
            print(f"Embedding error: {e}")
            # Return empty embedding as fallback
            return [0.0] * 768
    
    def _get_confidence(self, similarity: float) -> str:
        """Get confidence level based on similarity score."""
        if similarity >= SIMILARITY_THRESHOLD_HIGH:
            return 'high'
        elif similarity >= SIMILARITY_THRESHOLD_LOW:
            return 'medium'
        return 'low'
