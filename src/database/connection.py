"""
Database connection for read-only access to Flexily database.
"""
import asyncpg
from typing import Optional, List, Dict, Any
from config.settings import DATABASE_URL


class DatabaseConnection:
    """Read-only database connection to Flexily."""
    
    _pool: Optional[asyncpg.Pool] = None
    
    @classmethod
    async def get_pool(cls) -> asyncpg.Pool:
        if cls._pool is None:
            cls._pool = await asyncpg.create_pool(
                DATABASE_URL,
                min_size=2,
                max_size=10,
                server_settings={'default_transaction_read_only': 'on'}
            )
        return cls._pool
    
    @classmethod
    async def close(cls):
        if cls._pool:
            await cls._pool.close()
            cls._pool = None


async def get_mcqs_without_images(limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
    """Get MCQs that need images (flagged or likely needing)."""
    pool = await DatabaseConnection.get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT 
                id, chapter_id, question_text, options, correct_answer,
                source_type, source_reference, difficulty, verification_status
            FROM mcqs
            WHERE is_active = true
              AND (question_image_url IS NULL OR question_image_url = '')
            ORDER BY created_at DESC
            LIMIT $1 OFFSET $2
        """, limit, offset)
        return [dict(row) for row in rows]


async def get_mcq_by_id(mcq_id: str) -> Optional[Dict[str, Any]]:
    """Get a single MCQ by ID."""
    pool = await DatabaseConnection.get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT 
                id, chapter_id, question_text, options, correct_answer,
                source_type, source_reference, difficulty, verification_status
            FROM mcqs
            WHERE id = $1 AND is_active = true
        """, mcq_id)
        return dict(row) if row else None


async def get_mcqs_with_smiles(limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
    """Get MCQs that have SMILES strings in the predictions file."""
    # This will be populated from the predictions.jsonl file
    # Not from database directly
    pass


async def get_mcq_chapter_info(mcq_id: str) -> Optional[Dict[str, Any]]:
    """Get chapter and subject info for an MCQ."""
    pool = await DatabaseConnection.get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT 
                m.id as mcq_id,
                c.title as chapter_title,
                s.name as subject_name,
                s.slug as subject_slug
            FROM mcqs m
            LEFT JOIN chapters c ON m.chapter_id = c.id
            LEFT JOIN subjects s ON c.subject_id = s.id
            WHERE m.id = $1
        """, mcq_id)
        return dict(row) if row else None


async def get_textbook_chunks_with_images(
    query_embedding: List[float],
    subject: str = None,
    limit: int = 5,
    threshold: float = 0.75
) -> List[Dict[str, Any]]:
    """Search textbook chunks with images using vector similarity."""
    pool = await DatabaseConnection.get_pool()
    async with pool.acquire() as conn:
        embedding_str = f"[{','.join(map(str, query_embedding))}]"
        
        sql = """
            SELECT 
                id, subject, year_level, source_file,
                chunk_type, has_image, image_paths,
                clean_content, header_metadata,
                1 - (embedding <=> $1) as similarity
            FROM textbook_chunks
            WHERE has_image = true
              AND 1 - (embedding <=> $1) >= $2
        """
        params = [embedding_str, threshold]
        
        if subject:
            sql += " AND subject = $3"
            params.append(subject)
        
        sql += f" ORDER BY similarity DESC LIMIT ${len(params) + 1}"
        params.append(limit)
        
        rows = await conn.fetch(sql, *params)
        return [dict(row) for row in rows]


async def get_total_mcqs_needing_images() -> int:
    """Get count of MCQs without images."""
    pool = await DatabaseConnection.get_pool()
    async with pool.acquire() as conn:
        return await conn.fetchval("""
            SELECT COUNT(*) FROM mcqs
            WHERE is_active = true
              AND (question_image_url IS NULL OR question_image_url = '')
        """)
