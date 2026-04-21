#!/usr/bin/env python3
"""
Phase 1: Chemistry SMILES to SVG batch processing.
Processes MCQs with SMILES strings using RDKit.
"""
import argparse
import json
import sys
from pathlib import Path
from datetime import datetime
from dataclasses import asdict, dataclass

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.data_loader import get_mcqs_with_smiles, MCQData
from src.generators.chemistry_generator import ChemistryGenerator
from config.settings import (
    OUTPUT_DIR, GENERATED_DIR, FAILED_DIR, LOGS_DIR,
    MAX_RETRIES, RETRY_DELAY_SECONDS
)


@dataclass
class Phase1Result:
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
    smiles: str


def process_mcq(mcq: MCQData, generator: ChemistryGenerator) -> Phase1Result:
    """Process a single MCQ with SMILES."""
    result = Phase1Result(
        mcq_id=mcq.mcq_id,
        phase=1,
        question_text=mcq.question_text,
        subject=mcq.subject or 'chemistry',
        source_file=mcq.source_file or 'unknown',
        svg=None,
        error=None,
        attempts=0,
        generated_at=datetime.now().isoformat(),
        source_type='chemistry',
        smiles=mcq.smiles_string
    )
    
    for attempt in range(MAX_RETRIES):
        result.attempts = attempt + 1
        svg, error = generator.smiles_to_svg(mcq.smiles_string)
        
        if svg:
            result.svg = svg
            return result
        
        result.error = error
    
    return result


def main():
    parser = argparse.ArgumentParser(description='Phase 1: Chemistry SMILES to SVG')
    parser.add_argument('--batch-size', type=int, default=100, help='Number of MCQs per batch')
    parser.add_argument('--offset', type=int, default=0, help='Starting offset')
    parser.add_argument('--limit', type=int, default=None, help='Max MCQs to process')
    args = parser.parse_args()
    
    print("\n" + "=" * 60)
    print("PHASE 1: Chemistry SMILES → SVG")
    print("=" * 60)
    
    generator = ChemistryGenerator()
    
    (GENERATED_DIR / 'chemistry').mkdir(parents=True, exist_ok=True)
    FAILED_DIR.mkdir(parents=True, exist_ok=True)
    
    print("\nLoading MCQs with SMILES...")
    mcqs = get_mcqs_with_smiles()
    print(f"Found {len(mcqs)} MCQs with SMILES strings")
    
    if args.limit:
        mcqs = mcqs[args.offset:args.offset + args.limit]
    else:
        mcqs = mcqs[args.offset:]
    
    print(f"Processing {len(mcqs)} MCQs (offset={args.offset})")
    
    results = []
    successful = 0
    failed = 0
    
    for i, mcq in enumerate(mcqs):
        if i > 0 and i % 50 == 0:
            print(f"  Progress: {i}/{len(mcqs)} ({successful} successful, {failed} failed)")
        
        result = process_mcq(mcq, generator)
        results.append(result)
        
        if result.svg:
            successful += 1
            svg_file = GENERATED_DIR / 'chemistry' / f"{mcq.mcq_id}.svg"
            with open(svg_file, 'w') as f:
                f.write(result.svg)
        else:
            failed += 1
    
    output_file = GENERATED_DIR / 'chemistry' / 'batch_results.jsonl'
    with open(output_file, 'w') as f:
        for r in results:
            f.write(json.dumps(asdict(r)) + '\n')
    
    if failed > 0:
        failures_file = FAILED_DIR / 'phase1_failures.jsonl'
        with open(failures_file, 'w') as f:
            for r in results:
                if not r.svg:
                    f.write(json.dumps(asdict(r)) + '\n')
    
    print("\n" + "=" * 60)
    print("PHASE 1 COMPLETE")
    print("=" * 60)
    print(f"Total processed: {len(results)}")
    print(f"Successful:       {successful}")
    print(f"Failed:           {failed}")
    print(f"Success rate:     {successful/len(results)*100:.1f}%" if results else "N/A")
    print()
    print(f"Results saved to: {output_file}")
    print(f"SVGs saved to:    {GENERATED_DIR / 'chemistry'}")
    
    if failed > 0:
        print(f"Failures logged:  {FAILED_DIR / 'phase1_failures.jsonl'}")


if __name__ == "__main__":
    main()
