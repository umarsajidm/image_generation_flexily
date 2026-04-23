"""
Phase 3B Batch Processor
Processes Mechanics and Optics MCQs using hybrid few-shot approach.
"""
import asyncio
import json
import sys
import argparse
from pathlib import Path
from datetime import datetime
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.data_loader import get_mcqs_needing_images
from src.utils.diagram_classifier import classify_diagram, DiagramType
from src.generators.multi_reference_generator import MultiReferenceGenerator, GenerationResult
from src.utils.svg_quality_checker import calculate_quality_score
from src.utils.mechanics_router import classify_mechanics_subtype, get_subtype_confidence, MechanicsSubtype


class Phase3BProcessor:
    def __init__(self, batch_size: int = 10, rate_limit: float = 2.0, test_limit: int = None):
        self.batch_size = batch_size
        self.rate_limit = rate_limit
        self.test_limit = test_limit
        self.output_dir = Path("/root/image_generation_flexily/output/generated/phase3b")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.results_file = self.output_dir / "phase3b_results.jsonl"
        self.checkpoint_file = self.output_dir / "checkpoint.jsonl"
        
    def get_mcqs_by_type(self):
        """Get MCQs organized by diagram type (mechanics/optics only)."""
        mcqs = get_mcqs_needing_images()
        physics_mcqs = [m for m in mcqs if m.subject == 'physics']
        
        by_type = {
            'mechanics': [],
            'optics': [],
        }
        
        for m in physics_mcqs:
            cls = classify_diagram(m.question_text, m.subject, m.options)
            dtype = cls.diagram_type.value
            
            if dtype in by_type:
                by_type[dtype].append(m)
        
        if self.test_limit:
            for dtype in by_type:
                by_type[dtype] = by_type[dtype][:self.test_limit]
        
        return by_type
    
    def load_checkpoint(self):
        """Load previously processed MCQ IDs."""
        processed = set()
        if self.checkpoint_file.exists():
            with open(self.checkpoint_file, 'r') as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        processed.add(data['mcq_id'])
        return processed
    
    def save_checkpoint(self, result: dict):
        """Save result to checkpoint."""
        with open(self.checkpoint_file, 'a') as f:
            f.write(json.dumps(result) + '\n')
    
    def save_final_result(self, result: dict):
        """Save to final results file."""
        with open(self.results_file, 'a') as f:
            f.write(json.dumps(result) + '\n')
    
    async def process_mcq(self, generator, mcq, diagram_type: str) -> dict:
        """Process a single MCQ."""
        result = await generator.generate(mcq)
        
        mechanics_subtype = None
        if diagram_type == 'mechanics':
            subtype, confidence = get_subtype_confidence(mcq.question_text)
            mechanics_subtype = subtype.value
        
        output = {
            'mcq_id': mcq.mcq_id,
            'question_text': mcq.question_text[:200],
            'subject': mcq.subject,
            'diagram_type': result.diagram_type,
            'mechanics_subtype': mechanics_subtype,
            'generation_method': result.generation_method,
            'quality_score': result.quality_score,
            'success': result.svg is not None,
            'svg_path': None,
            'error': result.error,
            'generated_at': datetime.now().isoformat(),
        }
        
        if result.svg:
            svg_path = self.output_dir / f"{mcq.mcq_id[:50]}.svg"
            with open(svg_path, 'w') as f:
                f.write(result.svg)
            output['svg_path'] = str(svg_path)
        
        return output
    
    async def run(self):
        """Run the batch processor."""
        print("=" * 70)
        print("Phase 3B Batch Processor - Mechanics & Optics")
        print("Using Hybrid Few-Shot Code Generation")
        print("=" * 70)
        
        by_type = self.get_mcqs_by_type()
        processed = self.load_checkpoint()
        
        total = sum(len(mcqs) for mcqs in by_type.values())
        remaining = total - len([m for t in by_type.values() for m in t if m.mcq_id in processed])
        
        print(f"\nTotal MCQs: {total}")
        print(f"Already processed: {len(processed)}")
        print(f"Remaining: {remaining}")
        
        print("\nBy type:")
        for dtype, mcqs in by_type.items():
            done = sum(1 for m in mcqs if m.mcq_id in processed)
            print(f"  {dtype}: {len(mcqs)} total, {done} done, {len(mcqs) - done} remaining")
        
        if remaining == 0:
            print("\nAll MCQs already processed!")
            return
        
        if by_type.get('mechanics'):
            print("\nMechanics subtype breakdown:")
            subtype_counts = defaultdict(int)
            for m in by_type['mechanics']:
                if m.mcq_id not in processed:
                    subtype = classify_mechanics_subtype(m.question_text)
                    subtype_counts[subtype.value] += 1
            for st, cnt in sorted(subtype_counts.items(), key=lambda x: -x[1]):
                print(f"  {st}: {cnt}")
        
        generator = MultiReferenceGenerator(
            model_name="gemini-2.5-pro",
            max_attempts=2,
            use_fallback=True,
            rate_limit_delay=self.rate_limit,
        )
        
        print("\n" + "-" * 70)
        print("Processing...")
        print("-" * 70)
        
        stats = defaultdict(lambda: {'success': 0, 'failed': 0, 'quality': []})
        subtype_stats = defaultdict(lambda: {'success': 0, 'failed': 0, 'quality': []})
        count = 0
        
        for dtype, mcqs in by_type.items():
            for mcq in mcqs:
                if mcq.mcq_id in processed:
                    continue
                
                count += 1
                print(f"\n[{count}/{remaining}] [{dtype}] {mcq.mcq_id[:40]}...")
                
                try:
                    output = await self.process_mcq(generator, mcq, dtype)
                    self.save_checkpoint(output)
                    
                    if output['success']:
                        stats[dtype]['success'] += 1
                        stats[dtype]['quality'].append(output['quality_score'])
                        
                        if output.get('mechanics_subtype'):
                            st = output['mechanics_subtype']
                            subtype_stats[st]['success'] += 1
                            subtype_stats[st]['quality'].append(output['quality_score'])
                        
                        status = '✓' if output['quality_score'] >= 70 else '~'
                        print(f"  {status} Quality: {output['quality_score']:.1f} | Method: {output['generation_method']}")
                    else:
                        stats[dtype]['failed'] += 1
                        
                        if output.get('mechanics_subtype'):
                            st = output['mechanics_subtype']
                            subtype_stats[st]['failed'] += 1
                        
                        print(f"  ✗ Error: {output['error'][:80] if output['error'] else 'unknown'}")
                    
                except Exception as e:
                    stats[dtype]['failed'] += 1
                    print(f"  ✗ Exception: {str(e)[:80]}")
                    self.save_checkpoint({
                        'mcq_id': mcq.mcq_id,
                        'success': False,
                        'error': str(e),
                    })
                
                if count % self.batch_size == 0:
                    print(f"\n  Batch complete. Sleeping {self.rate_limit}s...")
                    await asyncio.sleep(self.rate_limit)
        
        await generator.mermaid_generator.close()
        
        if self.checkpoint_file.exists():
            with open(self.checkpoint_file, 'r') as src:
                with open(self.results_file, 'w') as dst:
                    dst.write(src.read())
        
        self.print_summary(stats, subtype_stats, count)
        self.generate_html_viewer()
    
    def print_summary(self, stats, subtype_stats, total):
        """Print processing summary."""
        print("\n" + "=" * 70)
        print("PROCESSING COMPLETE")
        print("=" * 70)
        
        total_success = sum(s['success'] for s in stats.values())
        total_failed = sum(s['failed'] for s in stats.values())
        
        print(f"\nTotal processed: {total}")
        print(f"Success: {total_success} ({100*total_success/total:.1f}%)")
        print(f"Failed: {total_failed}")
        
        print("\nBy diagram type:")
        for dtype, s in stats.items():
            t = s['success'] + s['failed']
            rate = 100 * s['success'] / t if t > 0 else 0
            avg_q = sum(s['quality']) / len(s['quality']) if s['quality'] else 0
            print(f"  {dtype:10}: {s['success']}/{t} ({rate:.0f}%) - Avg quality: {avg_q:.1f}")
        
        if subtype_stats:
            print("\nBy mechanics subtype:")
            for st, s in sorted(subtype_stats.items(), key=lambda x: -x[1]['success']):
                t = s['success'] + s['failed']
                rate = 100 * s['success'] / t if t > 0 else 0
                avg_q = sum(s['quality']) / len(s['quality']) if s['quality'] else 0
                print(f"  {st:15}: {s['success']}/{t} ({rate:.0f}%) - Avg quality: {avg_q:.1f}")
        
        all_quality = [q for s in stats.values() for q in s['quality']]
        if all_quality:
            print("\nQuality distribution:")
            print(f"  Auto-accept (70+): {sum(1 for q in all_quality if q >= 70)}")
            print(f"  Manual review (50-70): {sum(1 for q in all_quality if 50 <= q < 70)}")
            print(f"  Auto-reject (<50): {sum(1 for q in all_quality if q < 50)}")
    
    def generate_html_viewer(self):
        """Generate HTML viewer for results."""
        if not self.results_file.exists():
            return
        
        results = []
        with open(self.results_file, 'r') as f:
            for line in f:
                if line.strip():
                    results.append(json.loads(line))
        
        html = """<!DOCTYPE html>
<html>
<head>
    <title>Phase 3B Results - Mechanics & Optics</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .result { border: 1px solid #ccc; margin: 10px 0; padding: 10px; background: white; }
        .success { border-color: #4CAF50; }
        .failed { border-color: #f44336; }
        svg { max-width: 400px; max-height: 300px; }
        .stats { background: #e3f2fd; padding: 15px; margin: 20px 0; border-radius: 5px; }
    </style>
</head>
<body>
    <h1>Phase 3B Results - Mechanics & Optics</h1>
    <p>Generated: """ + datetime.now().strftime("%Y-%m-%d %H:%M") + """</p>
    <p>Using Hybrid Few-Shot Code Generation</p>
"""
        
        success_count = sum(1 for r in results if r.get('success'))
        html += f"""
    <div class="stats">
        <h3>Summary</h3>
        <p>Total: {len(results)} | Success: {success_count} | Failed: {len(results) - success_count}</p>
    </div>
"""
        
        for r in results:
            status_class = 'success' if r.get('success') else 'failed'
            html += f"""
    <div class="result {status_class}">
        <h3>{r['mcq_id'][:50]}</h3>
        <p>Type: <b>{r.get('diagram_type', 'N/A')}</b> | 
           Subtype: <b>{r.get('mechanics_subtype', 'N/A')}</b> |
           Method: <b>{r.get('generation_method', 'N/A')}</b> | 
           Quality: <b>{r.get('quality_score', 0):.1f}</b></p>
        <p>{r.get('question_text', '')[:150]}...</p>
"""
            
            if r.get('svg_path') and Path(r['svg_path']).exists():
                with open(r['svg_path'], 'r') as f:
                    svg = f.read()
                html += f"""<div style="background:white;padding:10px;">{svg}</div>"""
            elif r.get('error'):
                html += f"""<p style="color:red;">Error: {r['error'][:100]}</p>"""
            
            html += """    </div>"""
        
        html += """</body></html>"""
        
        html_path = self.output_dir / "view_results.html"
        with open(html_path, 'w') as f:
            f.write(html)
        
        print(f"\nHTML viewer: {html_path}")


async def main():
    parser = argparse.ArgumentParser(description='Phase 3B Batch Processor')
    parser.add_argument('--batch-size', type=int, default=10, help='Batch size for rate limiting')
    parser.add_argument('--rate-limit', type=float, default=2.0, help='Rate limit delay in seconds')
    parser.add_argument('--test-limit', type=int, default=None, help='Limit number of MCQs per type for testing')
    args = parser.parse_args()
    
    processor = Phase3BProcessor(
        batch_size=args.batch_size,
        rate_limit=args.rate_limit,
        test_limit=args.test_limit
    )
    await processor.run()


if __name__ == "__main__":
    asyncio.run(main())
