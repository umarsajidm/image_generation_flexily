"""
Phase 3D-2 Processor - ATOM Diagrams
Processes ATOM type MCQs using template-based generation.
"""
import json
import sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.data_loader import get_mcqs_needing_images
from src.utils.diagram_classifier import classify_diagram, DiagramType
from src.generators.atom_generator import AtomGenerator
from src.utils.svg_quality_checker import calculate_quality_score
from src.utils.svg_validator import inject_textbook_style


class Phase3D2Processor:
    def __init__(self):
        self.output_dir = Path("/root/image_generation_flexily/output/generated/phase3d2")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.results_file = self.output_dir / "phase3d2_results.jsonl"
        self.checkpoint_file = self.output_dir / "checkpoint.jsonl"
        self.generator = AtomGenerator()
    
    def get_already_processed(self):
        """Get MCQ IDs from all previous phases."""
        processed = set()
        for phase in ['phase3a', 'phase3b', 'phase3c', 'phase3d1']:
            ckpt = Path(f"/root/image_generation_flexily/output/generated/{phase}/checkpoint.jsonl")
            if ckpt.exists():
                with open(ckpt, 'r') as f:
                    for line in f:
                        if line.strip():
                            data = json.loads(line)
                            processed.add(data['mcq_id'])
        return processed
    
    def get_atom_mcqs(self):
        """Get ATOM type MCQs that haven't been processed."""
        mcqs = get_mcqs_needing_images()
        processed = self.get_already_processed()
        
        atom_mcqs = []
        for m in mcqs:
            if m.mcq_id in processed:
                continue
            cls = classify_diagram(m.question_text, m.subject, m.options)
            if cls.diagram_type == DiagramType.ATOM:
                atom_mcqs.append(m)
        
        return atom_mcqs
    
    def load_checkpoint(self):
        """Load previously processed MCQ IDs from this phase."""
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
    
    def process_mcq(self, mcq) -> dict:
        """Process a single MCQ."""
        result = self.generator.generate(mcq.question_text, mcq.subject)
        
        output = {
            'mcq_id': mcq.mcq_id,
            'question_text': mcq.question_text[:200],
            'subject': mcq.subject,
            'diagram_type': 'atom',
            'diagram_subtype': result.diagram_subtype,
            'quality_score': 0,
            'success': result.success,
            'svg_path': None,
            'error': result.error,
            'generated_at': datetime.now().isoformat(),
        }
        
        if result.success and result.svg:
            safe_id = mcq.mcq_id.replace('/', '_').replace('\\', '_')[:50]
            svg_path = self.output_dir / f"{safe_id}.svg"
            svg = inject_textbook_style(result.svg)
            with open(svg_path, 'w') as f:
                f.write(svg)
            
            quality = calculate_quality_score(svg)
            output['svg_path'] = str(svg_path)
            output['quality_score'] = quality.overall_score
        
        return output
    
    def run(self):
        """Run the processor."""
        print("=" * 70)
        print("Phase 3D-2 Processor - ATOM Diagrams")
        print("=" * 70)
        
        mcqs = self.get_atom_mcqs()
        checkpoint_processed = self.load_checkpoint()
        
        remaining = [m for m in mcqs if m.mcq_id not in checkpoint_processed]
        
        print(f"\nTotal ATOM MCQs: {len(mcqs)}")
        print(f"Already processed (from checkpoint): {len(checkpoint_processed)}")
        print(f"Remaining: {len(remaining)}")
        
        if not remaining:
            print("\nAll ATOM MCQs already processed!")
            return
        
        print("\n" + "-" * 70)
        print("Processing...")
        print("-" * 70)
        
        stats = defaultdict(lambda: {'success': 0, 'failed': 0, 'quality': []})
        count = 0
        
        for mcq in remaining:
            count += 1
            print(f"\n[{count}/{len(remaining)}] [{mcq.subject}] {mcq.mcq_id[:40]}...")
            
            try:
                output = self.process_mcq(mcq)
                self.save_checkpoint(output)
                
                if output['success']:
                    stats[output['diagram_subtype']]['success'] += 1
                    stats[output['diagram_subtype']]['quality'].append(output['quality_score'])
                    status = '✓' if output['quality_score'] >= 70 else '~'
                    print(f"  {status} Type: {output['diagram_subtype']}")
                    print(f"     Quality: {output['quality_score']:.1f}")
                else:
                    stats['failed']['failed'] += 1
                    print(f"  ✗ Error: {output['error'][:60] if output['error'] else 'unknown'}")
            
            except Exception as e:
                stats['exception']['failed'] += 1
                print(f"  ✗ Exception: {str(e)[:60]}")
                self.save_checkpoint({
                    'mcq_id': mcq.mcq_id,
                    'success': False,
                    'error': str(e),
                })
        
        self.print_summary(stats, count)
        self.generate_html_viewer()
    
    def print_summary(self, stats, total):
        """Print processing summary."""
        print("\n" + "=" * 70)
        print("PROCESSING COMPLETE")
        print("=" * 70)
        
        total_success = sum(s['success'] for s in stats.values())
        total_failed = sum(s['failed'] for s in stats.values())
        
        if total > 0:
            print(f"\nTotal processed: {total}")
            print(f"Success: {total_success} ({100*total_success/total:.1f}%)")
            print(f"Failed: {total_failed}")
        
        print("\nBy subtype:")
        for subtype, s in stats.items():
            if s['success'] > 0:
                avg_q = sum(s['quality']) / len(s['quality']) if s['quality'] else 0
                print(f"  {subtype}: {s['success']} - Avg quality: {avg_q:.1f}")
        
        all_quality = [q for s in stats.values() for q in s['quality']]
        if all_quality:
            print(f"\nAverage quality: {sum(all_quality)/len(all_quality):.1f}")
    
    def generate_html_viewer(self):
        """Generate HTML viewer for results."""
        if not self.checkpoint_file.exists():
            return
        
        results = []
        with open(self.checkpoint_file, 'r') as f:
            for line in f:
                if line.strip():
                    results.append(json.loads(line))
        
        html = """<!DOCTYPE html>
<html>
<head>
    <title>Phase 3D-2 Results - ATOM Diagrams</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .result { border: 1px solid #ccc; margin: 10px 0; padding: 10px; background: white; }
        .success { border-color: #4CAF50; }
        .failed { border-color: #f44336; }
        svg { max-width: 400px; max-height: 300px; }
    </style>
</head>
<body>
    <h1>Phase 3D-2 Results - ATOM Diagrams</h1>
    <p>Generated: """ + datetime.now().strftime("%Y-%m-%d %H:%M") + """</p>
"""
        
        for r in results:
            status_class = 'success' if r.get('success') else 'failed'
            html += f"""
    <div class="result {status_class}">
        <h3>{r['mcq_id'][:50]}</h3>
        <p>Subtype: <b>{r.get('diagram_subtype', 'N/A')}</b> |
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


if __name__ == "__main__":
    processor = Phase3D2Processor()
    processor.run()
