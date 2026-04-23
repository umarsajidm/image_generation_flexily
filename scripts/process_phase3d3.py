"""
Phase 3D-3 Processor - GEOMETRY Diagrams
Processes GEOMETRY type MCQs using few-shot approach with Gemini.
"""
import asyncio
import json
import sys
import os
import re
import tempfile
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from typing import Optional, Tuple

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.data_loader import get_mcqs_needing_images
from src.utils.diagram_classifier import classify_diagram, DiagramType
from src.generators.geometry_generator import GeometryGenerator, classify_geometry_question
from src.utils.svg_quality_checker import calculate_quality_score
from src.utils.svg_validator import inject_textbook_style, validate_and_fix_svg
from google import genai
from google.genai import types
from config.settings import GCP_PROJECT_ID, GCP_LOCATION


class Phase3D3Processor:
    def __init__(self, batch_size: int = 10, rate_limit: float = 2.0):
        self.batch_size = batch_size
        self.rate_limit = rate_limit
        self.output_dir = Path("/root/image_generation_flexily/output/generated/phase3d3")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.results_file = self.output_dir / "phase3d3_results.jsonl"
        self.checkpoint_file = self.output_dir / "checkpoint.jsonl"
        self.generator = GeometryGenerator()
        self.client = None
    
    def get_already_processed(self):
        """Get MCQ IDs from all previous phases."""
        processed = set()
        for phase in ['phase3a', 'phase3b', 'phase3c', 'phase3d1', 'phase3d2']:
            ckpt = Path(f"/root/image_generation_flexily/output/generated/{phase}/checkpoint.jsonl")
            if ckpt.exists():
                with open(ckpt, 'r') as f:
                    for line in f:
                        if line.strip():
                            data = json.loads(line)
                            processed.add(data['mcq_id'])
        return processed
    
    def get_geometry_mcqs(self):
        """Get GEOMETRY type MCQs that haven't been processed."""
        mcqs = get_mcqs_needing_images()
        processed = self.get_already_processed()
        
        geometry_mcqs = []
        for m in mcqs:
            if m.mcq_id in processed:
                continue
            cls = classify_diagram(m.question_text, m.subject, m.options)
            if cls.diagram_type == DiagramType.GEOMETRY:
                geometry_mcqs.append(m)
        
        return geometry_mcqs
    
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
    
    async def get_gemini_client(self):
        """Get Gemini client."""
        if self.client is None:
            self.client = genai.Client(
                vertexai=True,
                project=GCP_PROJECT_ID,
                location=GCP_LOCATION,
            )
        return self.client
    
    async def generate_with_gemini(self, question: str) -> tuple:
        """Generate geometry diagram using Gemini with few-shot prompt."""
        prompt, subtype = self.generator.get_prompt(question)
        
        client = await self.get_gemini_client()
        
        response = await client.aio.models.generate_content(
            model="gemini-2.5-pro",
            contents=prompt,
        )
        
        code = response.text
        
        # Strip markdown code blocks
        code = re.sub(r'^```python\s*', '', code)
        code = re.sub(r'^```\s*', '', code)
        code = re.sub(r'\s*```$', '', code)
        code = code.strip()
        
        return code, subtype
    
    async def execute_python_code(self, code: str) -> Optional[str]:
        """Execute Python code and return SVG content."""
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                output_path = os.path.join(tmpdir, 'output.svg')
                
                # Modify code to save to output_path
                code = code.replace("plt.savefig('output.svg'", f"plt.savefig('{output_path}'")
                code = code.replace('plt.savefig("output.svg"', f'plt.savefig("{output_path}"')
                
                exec_globals = {}
                exec(code, exec_globals)
                
                if os.path.exists(output_path):
                    with open(output_path, 'r') as f:
                        svg = f.read()
                    
                    svg = re.sub(r'<\?xml[^>]*\?>', '', svg)
                    svg = re.sub(r'<!DOCTYPE[^>]*>', '', svg)
                    return svg.strip()
        
        except Exception as e:
            return None
        
        return None
    
    async def process_mcq(self, mcq) -> dict:
        """Process a single MCQ."""
        
        # Try direct generation first for simple cases
        subtype = classify_geometry_question(mcq.question_text)
        
        if subtype in ['charge_triangle', 'charge_square']:
            result = self.generator.generate_direct(mcq.question_text)
            if result.success:
                svg = result.svg
            else:
                # Fallback to Gemini
                code, _ = await self.generate_with_gemini(mcq.question_text)
                svg = await self.execute_python_code(code)
        else:
            # Use Gemini for complex cases
            code, subtype = await self.generate_with_gemini(mcq.question_text)
            svg = await self.execute_python_code(code)
        
        output = {
            'mcq_id': mcq.mcq_id,
            'question_text': mcq.question_text[:200],
            'subject': mcq.subject,
            'diagram_type': 'geometry',
            'diagram_subtype': subtype,
            'quality_score': 0,
            'success': svg is not None,
            'svg_path': None,
            'error': None,
            'generated_at': datetime.now().isoformat(),
        }
        
        if svg:
            # Validate and fix SVG
            validation = validate_and_fix_svg(svg)
            if validation.is_valid:
                svg = validation.svg
                svg = inject_textbook_style(svg)
                
                safe_id = mcq.mcq_id.replace('/', '_').replace('\\', '_')[:50]
                svg_path = self.output_dir / f"{safe_id}.svg"
                with open(svg_path, 'w') as f:
                    f.write(svg)
                
                quality = calculate_quality_score(svg)
                output['svg_path'] = str(svg_path)
                output['quality_score'] = quality.overall_score
            else:
                output['success'] = False
                output['error'] = validation.error
        else:
            output['error'] = 'Failed to generate SVG'
        
        return output
    
    async def run(self):
        """Run the processor."""
        print("=" * 70)
        print("Phase 3D-3 Processor - GEOMETRY Diagrams")
        print("=" * 70)
        
        mcqs = self.get_geometry_mcqs()
        checkpoint_processed = self.load_checkpoint()
        
        remaining = [m for m in mcqs if m.mcq_id not in checkpoint_processed]
        
        print(f"\nTotal GEOMETRY MCQs: {len(mcqs)}")
        print(f"Already processed (from checkpoint): {len(checkpoint_processed)}")
        print(f"Remaining: {len(remaining)}")
        
        if not remaining:
            print("\nAll GEOMETRY MCQs already processed!")
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
                output = await self.process_mcq(mcq)
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
            
            if count % self.batch_size == 0:
                print(f"\n  Batch complete. Sleeping {self.rate_limit}s...")
                await asyncio.sleep(self.rate_limit)
        
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
    <title>Phase 3D-3 Results - GEOMETRY Diagrams</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .result { border: 1px solid #ccc; margin: 10px 0; padding: 10px; background: white; }
        .success { border-color: #4CAF50; }
        .failed { border-color: #f44336; }
        svg { max-width: 400px; max-height: 300px; }
    </style>
</head>
<body>
    <h1>Phase 3D-3 Results - GEOMETRY Diagrams</h1>
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


async def main():
    processor = Phase3D3Processor(batch_size=10, rate_limit=2.0)
    await processor.run()


if __name__ == "__main__":
    asyncio.run(main())
