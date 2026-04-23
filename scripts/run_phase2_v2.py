#!/usr/bin/env python3
"""
Phase 2: Multi-Reference Image Generation

Generates SVG diagrams for MCQs using textbook reference images.
"""

import os
import sys
import json
import argparse
import time
import asyncio
from pathlib import Path
from datetime import datetime
from typing import List, Dict
import tqdm

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.data_loader import get_mcqs_needing_images
from src.generators.multi_reference_generator import MultiReferenceGenerator, GenerationResult


def load_checkpoint(checkpoint_path: Path) -> set:
    if not checkpoint_path.exists():
        return set()
    
    completed = set()
    with open(checkpoint_path, 'r') as f:
        for line in f:
            try:
                data = json.loads(line)
                if data.get('svg') and not data.get('error'):
                    completed.add(data['mcq_id'])
            except:
                pass
    
    return completed


def save_result(result: GenerationResult, output_file: Path, checkpoint_file: Path):
    record = {
        'mcq_id': result.mcq_id,
        'svg': result.svg,
        'error': result.error,
        'attempts': result.attempts,
        'references_used': result.references_used,
        'fixes_applied': result.fixes_applied,
        'diagram_type': result.diagram_type,
        'generation_method': result.generation_method,
        'quality_score': result.quality_score,
        'generated_at': datetime.now().isoformat()
    }
    
    with open(output_file, 'a') as f:
        f.write(json.dumps(record) + '\n')
    
    with open(checkpoint_file, 'a') as f:
        f.write(json.dumps({'mcq_id': result.mcq_id, 'svg': result.svg, 'error': result.error}) + '\n')


async def run_batch(
    mcqs: List,
    generator: MultiReferenceGenerator,
    output_file: Path,
    checkpoint_file: Path,
    completed_ids: set,
    batch_size: int = 10,
    rate_limit_delay: float = 2.0
):
    pending = []
    for m in mcqs:
        mcq_id = m.mcq_id
        if mcq_id not in completed_ids:
            pending.append(m)
    
    print(f"Total MCQs: {len(mcqs)}")
    print(f"Already completed: {len(completed_ids)}")
    print(f"Pending: {len(pending)}")
    
    if not pending:
        print("All MCQs already processed!")
        return
    
    success_count = 0
    error_count = 0
    fallback_count = 0
    quality_scores = []
    
    for i, mcq in enumerate(tqdm.tqdm(pending, desc="Generating")):
        try:
            result = await generator.generate(mcq)
            
            save_result(result, output_file, checkpoint_file)
            
            if result.svg:
                success_count += 1
                quality_scores.append(result.quality_score)
                if result.generation_method == 'python_code':
                    fallback_count += 1
            else:
                error_count += 1
                print(f"\nError for {result.mcq_id}: {result.error[:100] if result.error else 'Unknown'}")
            
            if (i + 1) % batch_size == 0:
                avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
                print(f"\nProgress: {i+1}/{len(pending)} | Success: {success_count} | Errors: {error_count} | Fallback: {fallback_count} | Avg Quality: {avg_quality:.1f}")
                time.sleep(rate_limit_delay)
            
            time.sleep(0.5)
            
        except KeyboardInterrupt:
            print("\n\nInterrupted by user. Progress saved.")
            break
        except Exception as e:
            error_count += 1
            print(f"\nUnexpected error for MCQ: {e}")
    
    avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
    print(f"\n\nFinal Results:")
    print(f"  Success: {success_count}")
    print(f"  Errors: {error_count}")
    print(f"  Python fallback used: {fallback_count}")
    print(f"  Average quality score: {avg_quality:.1f}")
    print(f"  Total processed: {success_count + error_count}")


def main():
    parser = argparse.ArgumentParser(description="Phase 2: Multi-Reference Image Generation")
    parser.add_argument('--batch-size', type=int, default=10, help="Batch size for progress updates")
    parser.add_argument('--max-references', type=int, default=3, help="Max reference images per MCQ")
    parser.add_argument('--max-attempts', type=int, default=2, help="Max generation attempts per MCQ")
    parser.add_argument('--rate-limit', type=float, default=2.0, help="Delay between batches (seconds)")
    parser.add_argument('--limit', type=int, default=None, help="Limit number of MCQs to process")
    parser.add_argument('--test', action='store_true', help="Run with 5 MCQs for testing")
    parser.add_argument('--threshold', type=float, default=0.6, help="Similarity threshold for vector search")
    parser.add_argument('--no-fallback', action='store_true', help="Disable Python code fallback")
    parser.add_argument('--model', type=str, default='gemini-2.5-pro', help="Gemini model to use")
    parser.add_argument('--subject', type=str, default=None, help="Filter by subject (e.g., biology, physics, chemistry)")
    args = parser.parse_args()
    
    base_dir = Path(__file__).parent.parent
    output_dir = base_dir / "output" / "generated" / "reference"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_dir / "phase2_results.jsonl"
    checkpoint_file = output_dir / "checkpoint.jsonl"
    
    api_key = os.environ.get('GOOGLE_API_KEY') or os.environ.get('GEMINI_API_KEY')
    
    creds_path = os.path.expanduser("~/mcq-worker-key.json")
    if not os.path.exists(creds_path) and not api_key:
        print("Error: Set GOOGLE_API_KEY/GEMINI_API_KEY or ensure ~/mcq-worker-key.json exists")
        sys.exit(1)
    
    if os.path.exists(creds_path):
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
    
    print("Loading MCQs...")
    all_mcqs = get_mcqs_needing_images()
    
    # Filter by subject if specified
    if args.subject:
        subject_lower = args.subject.lower()
        all_mcqs = [m for m in all_mcqs if m.subject and subject_lower in m.subject.lower()]
        print(f"Filtered by subject '{args.subject}': {len(all_mcqs)} MCQs")
    
    if args.test:
        all_mcqs = all_mcqs[:5]
        print(f"TEST MODE: Processing only {len(all_mcqs)} MCQs")
    elif args.limit:
        all_mcqs = all_mcqs[:args.limit]
        print(f"LIMIT MODE: Processing {len(all_mcqs)} MCQs")
    
    print("Loading checkpoint...")
    completed_ids = load_checkpoint(checkpoint_file)
    
    print("Initializing generator...")
    print(f"  Model: {args.model}")
    print(f"  Similarity threshold: {args.threshold}")
    print(f"  Python fallback: {'disabled' if args.no_fallback else 'enabled'}")
    
    generator = MultiReferenceGenerator(
        model_name=args.model,
        max_references=args.max_references,
        max_attempts=args.max_attempts,
        similarity_threshold=args.threshold,
        use_fallback=not args.no_fallback
    )
    
    print(f"\nStarting generation...")
    print(f"Output: {output_file}")
    print(f"Checkpoint: {checkpoint_file}")
    print()
    
    asyncio.run(run_batch(
        mcqs=all_mcqs,
        generator=generator,
        output_file=output_file,
        checkpoint_file=checkpoint_file,
        completed_ids=completed_ids,
        batch_size=args.batch_size,
        rate_limit_delay=args.rate_limit
    ))
    
    print(f"\nResults saved to: {output_file}")


if __name__ == "__main__":
    main()
