"""
Main batch processor for image generation.
Handles JSONL format with 1 question per query.
"""
import json
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict

from config.settings import (
    OUTPUT_DIR, GENERATED_DIR, FAILED_DIR, LOGS_DIR, REVIEW_DIR,
    MAX_RETRIES, RETRY_DELAY_SECONDS, PILOT_SAMPLE_SIZE
)
from src.generators.chemistry_generator import ChemistryGenerator
from src.generators.reference_generator import ReferenceGenerator
from src.generators.pure_generator import PureGenerator
from src.matchers.vector_matcher import VectorMatcher
from src.database.connection import get_mcqs_without_images, get_mcq_chapter_info


@dataclass
class GenerationResult:
    """Result of a single image generation."""
    mcq_id: str
    phase: int
    question_text: str
    subject: str
    chapter: str
    svg: Optional[str]
    error: Optional[str]
    attempts: int
    generated_at: str
    source_type: str  # 'chemistry', 'reference', 'pure'
    reference_image: Optional[str] = None
    smiles: Optional[str] = None
    similarity_score: Optional[float] = None


class BatchProcessor:
    """Process MCQs in batches for image generation."""
    
    def __init__(self):
        self.chemistry_gen = ChemistryGenerator()
        self.reference_gen = ReferenceGenerator()
        self.pure_gen = PureGenerator()
        self.vector_matcher = VectorMatcher()
        
        # Ensure output directories exist
        for d in [OUTPUT_DIR, GENERATED_DIR, FAILED_DIR, LOGS_DIR, REVIEW_DIR]:
            d.mkdir(parents=True, exist_ok=True)
        
        for subdir in ['chemistry', 'reference', 'pure']:
            (GENERATED_DIR / subdir).mkdir(parents=True, exist_ok=True)
    
    async def process_single_mcq(
        self,
        mcq: Dict[str, Any],
        phase: int,
        smiles: str = None
    ) -> GenerationResult:
        """
        Process a single MCQ and generate image.
        
        Args:
            mcq: MCQ data dictionary
            phase: Which phase (1, 2, or 3)
            smiles: SMILES string for chemistry (phase 1)
            
        Returns:
            GenerationResult with SVG or error
        """
        mcq_id = mcq['id']
        question_text = mcq['question_text']
        
        # Get chapter/subject info
        chapter_info = await get_mcq_chapter_info(mcq_id)
        subject = chapter_info.get('subject_name', 'Unknown') if chapter_info else 'Unknown'
        chapter = chapter_info.get('chapter_title', 'Unknown') if chapter_info else 'Unknown'
        
        result = GenerationResult(
            mcq_id=mcq_id,
            phase=phase,
            question_text=question_text,
            subject=subject,
            chapter=chapter,
            svg=None,
            error=None,
            attempts=0,
            generated_at=datetime.now().isoformat(),
            source_type='',
            smiles=smiles
        )
        
        # Phase 1: Chemistry (SMILES)
        if phase == 1 and smiles:
            result.source_type = 'chemistry'
            for attempt in range(MAX_RETRIES):
                result.attempts = attempt + 1
                svg, error = self.chemistry_gen.smiles_to_svg(smiles)
                if svg:
                    result.svg = svg
                    return result
                result.error = error
                if attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(RETRY_DELAY_SECONDS)
        
        # Phase 2: Reference-based
        elif phase == 2:
            result.source_type = 'reference'
            for attempt in range(MAX_RETRIES):
                result.attempts = attempt + 1
                
                # Find reference
                match = await self.vector_matcher.find_reference(
                    question_text,
                    subject.lower() if subject else None
                )
                
                if match and match.get('image_path'):
                    result.reference_image = match['image_path']
                    result.similarity_score = match['similarity']
                    
                    # Generate from reference
                    svg, error = self.reference_gen.generate_from_reference(
                        question_text, subject, chapter, match['image_path']
                    )
                    
                    if svg:
                        result.svg = svg
                        return result
                    result.error = error
                else:
                    result.error = "No matching reference found"
                    break  # No point retrying if no reference
                
                if attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(RETRY_DELAY_SECONDS)
        
        # Phase 3: Pure AI generation
        elif phase == 3:
            result.source_type = 'pure'
            for attempt in range(MAX_RETRIES):
                result.attempts = attempt + 1
                svg, error = self.pure_gen.generate(
                    question_text, subject, chapter
                )
                if svg:
                    result.svg = svg
                    return result
                result.error = error
                if attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(RETRY_DELAY_SECONDS)
        
        return result
    
    def save_result_to_jsonl(self, result: GenerationResult, output_file: Path):
        """Save result to JSONL file."""
        with open(output_file, 'a') as f:
            f.write(json.dumps(asdict(result)) + '\n')
    
    def save_svg(self, mcq_id: str, phase: int, source_type: str, svg: str):
        """Save SVG to file."""
        filename = f"mcq_{mcq_id}.svg"
        filepath = GENERATED_DIR / source_type / filename
        with open(filepath, 'w') as f:
            f.write(svg)
        return str(filepath)
    
    def save_failed(self, result: GenerationResult):
        """Save failed generation to log."""
        filename = f"phase{result.phase}_failures.jsonl"
        filepath = FAILED_DIR / filename
        with open(filepath, 'a') as f:
            f.write(json.dumps(asdict(result)) + '\n')


async def run_pilot():
    """
    Run pilot mode with sample MCQs for each phase.
    10 samples per phase = 30 total.
    """
    print("=" * 60)
    print("PILOT MODE - Testing with sample MCQs")
    print("=" * 60)
    
    processor = BatchProcessor()
    pilot_output = OUTPUT_DIR / "pilot"
    pilot_output.mkdir(parents=True, exist_ok=True)
    
    results = []
    
    # Sample SMILES for chemistry (Phase 1)
    sample_smiles = [
        ("CCO", "ethanol"),
        ("CC(C)C", "isobutane"),
        ("c1ccccc1", "benzene"),
        ("CC(=O)O", "acetic acid"),
        ("CCN(CC)CC", "triethylamine"),
    ]
    
    print("\n--- Phase 1: Chemistry (SMILES) ---")
    for smiles, name in sample_smiles[:PILOT_SAMPLE_SIZE]:
        print(f"  Testing: {name} ({smiles})")
        svg, error = processor.chemistry_gen.smiles_to_svg(smiles)
        result = GenerationResult(
            mcq_id=f"sample_{name}",
            phase=1,
            question_text=f"Sample molecule: {name}",
            subject="Chemistry",
            chapter="Test",
            svg=svg,
            error=error,
            attempts=1,
            generated_at=datetime.now().isoformat(),
            source_type='chemistry',
            smiles=smiles
        )
        results.append(result)
        if svg:
            processor.save_svg(f"sample_{name}", 1, 'chemistry', svg)
            print(f"    ✓ Generated")
        else:
            print(f"    ✗ Failed: {error}")
    
    print(f"\nPilot complete. {len([r for r in results if r.svg])} successful generations.")
    print(f"Results saved to: {pilot_output}")
    
    # Save all results
    with open(pilot_output / "pilot_results.jsonl", 'w') as f:
        for r in results:
            f.write(json.dumps(asdict(r)) + '\n')
    
    return results


if __name__ == "__main__":
    asyncio.run(run_pilot())
