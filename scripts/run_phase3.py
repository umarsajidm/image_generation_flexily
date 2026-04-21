#!/usr/bin/env python3
"""
Phase 3: Pure AI SVG generation.
Uses Gemini to generate SVGs purely from question text.
"""
import argparse
import json
import sys
from pathlib import Path
from datetime import datetime
from dataclasses import asdict, dataclass
import time

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.data_loader import get_mcqs_needing_images, MCQData
from src.generators.pure_generator import PureGenerator
from config.settings import (
    OUTPUT_DIR, GENERATED_DIR, FAILED_DIR,
    MAX_RETRIES, RETRY_DELAY_SECONDS
)


@dataclass
class Phase3Result:
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
    diagram_type: str


def process_mcq(mcq: MCQData, generator: PureGenerator) -> Phase3Result:
    """Process a single MCQ with pure AI generation."""
    result = Phase3Result(
        mcq_id=mcq.mcq_id,
        phase=3,
        question_text=mcq.question_text,
        subject=mcq.subject or 'unknown',
        source_file=mcq.source_file or 'unknown',
        svg=None,
        error=None,
        attempts=0,
        generated_at=datetime.now().isoformat(),
        source_type='pure',
        diagram_type=generator.detect_diagram_type(mcq.question_text)
    )
    
    for attempt in range(MAX_RETRIES):
        result.attempts = attempt + 1
        
        svg, error = generator.generate(
            mcq.question_text,
            mcq.subject or 'unknown',
            mcq.source_file or ''
        )
        
        if svg:
            result.svg = svg
            return result
        
        result.error = error
        if attempt < MAX_RETRIES - 1:
            time.sleep(RETRY_DELAY_SECONDS)
    
    return result


def main():
    parser = argparse.ArgumentParser(description='Phase 3: Pure AI SVG generation')
    parser.add_argument('--batch-size', type=int, default=50, help='Number of MCQs per batch')
    parser.add_argument('--offset', type=int, default=0, help='Starting offset')
    parser.add_argument('--limit', type=int, default=None, help='Max MCQs to process')
    args = parser.parse_args()
    
    print("\n" + "=" * 60)
    print("PHASE 3: Pure AI SVG Generation")
    print("=" * 60)
    
    generator = PureGenerator()
    
    (GENERATED_DIR / 'pure').mkdir(parents=True, exist_ok=True)
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
    
    for i, mcq in enumerate(mcqs):
        if i > 0 and i % 20 == 0:
            print(f"  Progress: {i}/{len(mcqs)} ({successful} successful, {failed} failed)")
        
        result = process_mcq(mcq, generator)
        results.append(result)
        
        if result.svg:
            successful += 1
            svg_file = GENERATED_DIR / 'pure' / f"{mcq.mcq_id}.svg"
            with open(svg_file, 'w') as f:
                f.write(result.svg)
        else:
            failed += 1
            if "429" in str(result.error) or "rate" in str(result.error).lower():
                print(f"    Rate limited, waiting 60s...")
                time.sleep(60)
        
        time.sleep(2)
    
    output_file = GENERATED_DIR / 'pure' / 'batch_results.jsonl'
    with open(output_file, 'w') as f:
        for r in results:
            f.write(json.dumps(asdict(r)) + '\n')
    
    if failed > 0:
        failures_file = FAILED_DIR / 'phase3_failures.jsonl'
        with open(failures_file, 'w') as f:
            for r in results:
                if not r.svg:
                    f.write(json.dumps(asdict(r)) + '\n')
    
    print("\n" + "=" * 60)
    print("PHASE 3 COMPLETE")
    print("=" * 60)
    print(f"Total processed: {len(results)}")
    print(f"Successful:       {successful}")
    print(f"Failed:           {failed}")
    print(f"Success rate:     {successful/len(results)*100:.1f}%" if results else "N/A")
    print()
    print(f"Results saved to: {output_file}")
    
    if failed > 0:
        print(f"Failures logged:  {FAILED_DIR / 'phase3_failures.jsonl'}")


if __name__ == "__main__":
    main()
