#!/usr/bin/env python3
"""
Phase 2: Reference-based SVG generation.
Uses Gemini Vision to generate SVGs based on textbook reference images.
"""
import argparse
import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime
from dataclasses import asdict, dataclass

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.data_loader import get_mcqs_needing_images, MCQData
from src.generators.reference_generator import ReferenceGenerator
from src.matchers.vector_matcher import VectorMatcher
from config.settings import (
    OUTPUT_DIR, GENERATED_DIR, FAILED_DIR,
    MAX_RETRIES, RETRY_DELAY_SECONDS, SIMILARITY_THRESHOLD_LOW
)


@dataclass
class Phase2Result:
    mcq_id: str
    phase: int
    question_text: str
    subject: str
    source_file: str
    svg: str
    error: str
    attempts: int
    generated_at: str
    source_type: str
    reference_image: str
    similarity_score: float


async def process_mcq(
    mcq: MCQData,
    generator: ReferenceGenerator,
    matcher: VectorMatcher
) -> Phase2Result:
    """Process a single MCQ with reference image lookup."""
    result = Phase2Result(
        mcq_id=mcq.mcq_id,
        phase=2,
        question_text=mcq.question_text,
        subject=mcq.subject or 'unknown',
        source_file=mcq.source_file or 'unknown',
        svg=None,
        error=None,
        attempts=0,
        generated_at=datetime.now().isoformat(),
        source_type='reference',
        reference_image=None,
        similarity_score=None
    )
    
    match = await matcher.find_reference(
        mcq.question_text,
        mcq.subject.lower() if mcq.subject else None
    )
    
    if not match or not match.get('image_path'):
        result.error = "No matching reference image found"
        return result
    
    result.reference_image = match['image_path']
    result.similarity_score = match['similarity']
    
    for attempt in range(MAX_RETRIES):
        result.attempts = attempt + 1
        
        svg, error = generator.generate_from_reference(
            mcq.question_text,
            mcq.subject or 'unknown',
            mcq.source_file or '',
            match['image_path']
        )
        
        if svg:
            result.svg = svg
            return result
        
        result.error = error
        if attempt < MAX_RETRIES - 1:
            await asyncio.sleep(RETRY_DELAY_SECONDS)
    
    return result


async def main():
    parser = argparse.ArgumentParser(description='Phase 2: Reference-based SVG generation')
    parser.add_argument('--batch-size', type=int, default=50, help='Number of MCQs per batch')
    parser.add_argument('--offset', type=int, default=0, help='Starting offset')
    parser.add_argument('--limit', type=int, default=None, help='Max MCQs to process')
    args = parser.parse_args()
    
    print("\n" + "=" * 60)
    print("PHASE 2: Reference-based SVG Generation")
    print("=" * 60)
    
    generator = ReferenceGenerator()
    matcher = VectorMatcher()
    
    (GENERATED_DIR / 'reference').mkdir(parents=True, exist_ok=True)
    FAILED_DIR.mkdir(parents=True, exist_ok=True)
    
    print("\nLoading MCQs needing images...")
    mcqs = get_mcqs_needing_images()
    print(f"Found {len(mcqs)} MCQs needing images (no SMILES)")
    
    if args.limit:
        mcqs = mcqs[args.offset:args.offset + args.limit]
    else:
        mcqs = mcqs[args.offset:]
    
    print(f"Processing {len(mcqs)} MCQs (offset={args.offset})")
    
    results = []
    successful = 0
    failed = 0
    no_reference = 0
    
    for i, mcq in enumerate(mcqs):
        if i > 0 and i % 20 == 0:
            print(f"  Progress: {i}/{len(mcqs)} ({successful} ok, {failed} fail, {no_reference} no ref)")
        
        result = await process_mcq(mcq, generator, matcher)
        results.append(result)
        
        if result.svg:
            successful += 1
            svg_file = GENERATED_DIR / 'reference' / f"{mcq.mcq_id}.svg"
            with open(svg_file, 'w') as f:
                f.write(result.svg)
        elif result.error and "No matching reference" in result.error:
            no_reference += 1
        else:
            failed += 1
    
    output_file = GENERATED_DIR / 'reference' / 'batch_results.jsonl'
    with open(output_file, 'w') as f:
        for r in results:
            f.write(json.dumps(asdict(r)) + '\n')
    
    if failed > 0 or no_reference > 0:
        failures_file = FAILED_DIR / 'phase2_failures.jsonl'
        with open(failures_file, 'w') as f:
            for r in results:
                if not r.svg:
                    f.write(json.dumps(asdict(r)) + '\n')
    
    print("\n" + "=" * 60)
    print("PHASE 2 COMPLETE")
    print("=" * 60)
    print(f"Total processed: {len(results)}")
    print(f"Successful:       {successful}")
    print(f"No reference:     {no_reference}")
    print(f"Failed:           {failed}")
    print(f"Success rate:     {successful/len(results)*100:.1f}%" if results else "N/A")
    print()
    print(f"Results saved to: {output_file}")
    
    if failed > 0 or no_reference > 0:
        print(f"Failures logged:  {FAILED_DIR / 'phase2_failures.jsonl'}")


if __name__ == "__main__":
    asyncio.run(main())
