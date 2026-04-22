"""
Phase 3A Test: High-Confidence Physics (Graph, Circuit, Waves)
Tests 25 MCQs to validate the pipeline before full batch processing.
"""
import asyncio
import sys
import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.data_loader import get_mcqs_needing_images
from src.utils.diagram_classifier import classify_diagram, DiagramType
from src.generators.python_svg_generator import PythonSVGGenerator
from src.utils.svg_validator import inject_textbook_style
from src.utils.svg_quality_checker import calculate_quality_score


class Phase3ATester:
    def __init__(self):
        self.output_dir = Path("/root/image_generation_flexily/output/generated/phase3a_test")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.python_gen = PythonSVGGenerator()
        self.results = []
    
    def get_test_mcqs(self):
        """Get test MCQs for each type."""
        mcqs = get_mcqs_needing_images()
        physics_mcqs = [m for m in mcqs if m.subject == 'physics']
        
        test_mcqs = {
            'graph': [],
            'circuit': [],
            'waves': [],
        }
        
        for m in physics_mcqs:
            cls = classify_diagram(m.question_text, m.subject, m.options)
            dtype = cls.diagram_type.value
            
            if dtype in test_mcqs and len(test_mcqs[dtype]) < 10:
                test_mcqs[dtype].append((m, cls))
        
        return test_mcqs
    
    async def test_mcq(self, mcq, classification, dtype):
        """Test a single MCQ."""
        mcq_id = mcq.mcq_id
        question = mcq.question_text
        
        print(f"\n  [{dtype}] {mcq_id[:40]}...")
        print(f"    Q: {question[:60]}...")
        
        diagram_type = classification.diagram_type
        
        result = await self.python_gen.generate(
            question=question,
            diagram_type=diagram_type,
            classification=classification
        )
        
        if result.success and result.svg:
            quality = calculate_quality_score(result.svg)
            
            svg_path = self.output_dir / f"{mcq_id[:50]}_{dtype}.svg"
            with open(svg_path, 'w') as f:
                f.write(result.svg)
            
            print(f"    ✓ SUCCESS - Quality: {quality.overall_score:.1f}")
            
            return {
                'mcq_id': mcq_id,
                'type': dtype,
                'success': True,
                'quality_score': quality.overall_score,
                'svg_path': str(svg_path),
                'error': None,
            }
        else:
            print(f"    ✗ FAILED - {result.error[:100] if result.error else 'Unknown error'}")
            
            return {
                'mcq_id': mcq_id,
                'type': dtype,
                'success': False,
                'quality_score': 0,
                'svg_path': None,
                'error': result.error,
            }
    
    async def run_tests(self):
        """Run all tests."""
        print("=" * 70)
        print("Phase 3A Test: High-Confidence Physics")
        print("=" * 70)
        
        test_mcqs = self.get_test_mcqs()
        
        total = sum(len(v) for v in test_mcqs.values())
        print(f"\nTest set: {total} MCQs")
        for dtype, mcqs in test_mcqs.items():
            print(f"  {dtype}: {len(mcqs)}")
        
        print("\n" + "-" * 70)
        print("Running tests...")
        print("-" * 70)
        
        for dtype, mcqs in test_mcqs.items():
            print(f"\n[{dtype.upper()}] Testing {len(mcqs)} MCQs...")
            
            for mcq, classification in mcqs:
                result = await self.test_mcq(mcq, classification, dtype)
                self.results.append(result)
        
        self.print_summary()
        self.save_results()
    
    def print_summary(self):
        """Print test summary."""
        print("\n" + "=" * 70)
        print("TEST SUMMARY")
        print("=" * 70)
        
        by_type = defaultdict(lambda: {'success': 0, 'failed': 0, 'quality': []})
        
        for r in self.results:
            t = r['type']
            if r['success']:
                by_type[t]['success'] += 1
                by_type[t]['quality'].append(r['quality_score'])
            else:
                by_type[t]['failed'] += 1
        
        total_success = sum(v['success'] for v in by_type.values())
        total_failed = sum(v['failed'] for v in by_type.values())
        
        print(f"\nOverall: {total_success}/{len(self.results)} success ({100*total_success/len(self.results):.1f}%)")
        
        print("\nBy type:")
        for dtype, stats in by_type.items():
            total = stats['success'] + stats['failed']
            rate = 100 * stats['success'] / total if total > 0 else 0
            avg_quality = sum(stats['quality']) / len(stats['quality']) if stats['quality'] else 0
            
            print(f"  {dtype:10} : {stats['success']}/{total} success ({rate:.0f}%) - Avg quality: {avg_quality:.1f}")
        
        print("\nQuality distribution:")
        quality_scores = [r['quality_score'] for r in self.results if r['success']]
        if quality_scores:
            auto_accept = sum(1 for q in quality_scores if q >= 70)
            manual_review = sum(1 for q in quality_scores if 50 <= q < 70)
            auto_reject = sum(1 for q in quality_scores if q < 50)
            
            print(f"  Auto-accept (70+): {auto_accept}")
            print(f"  Manual review (50-70): {manual_review}")
            print(f"  Auto-reject (<50): {auto_reject}")
    
    def save_results(self):
        """Save results to JSON."""
        results_file = self.output_dir / "test_results.json"
        with open(results_file, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'total': len(self.results),
                'results': self.results,
            }, f, indent=2)
        
        print(f"\nResults saved to: {results_file}")
        
        html_file = self.output_dir / "view_results.html"
        html = self._generate_html()
        with open(html_file, 'w') as f:
            f.write(html)
        
        print(f"HTML viewer: {html_file}")
    
    def _generate_html(self):
        """Generate HTML viewer for results."""
        html = """<!DOCTYPE html>
<html>
<head>
    <title>Phase 3A Test Results</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .result { border: 1px solid #ccc; margin: 10px 0; padding: 10px; }
        .success { border-color: #4CAF50; }
        .failed { border-color: #f44336; }
        .quality { font-weight: bold; }
        .quality-high { color: #4CAF50; }
        .quality-medium { color: #FF9800; }
        .quality-low { color: #f44336; }
        svg { max-width: 400px; max-height: 300px; }
    </style>
</head>
<body>
    <h1>Phase 3A Test Results</h1>
"""
        
        for r in self.results:
            status_class = 'success' if r['success'] else 'failed'
            quality_class = 'quality-high' if r['quality_score'] >= 70 else ('quality-medium' if r['quality_score'] >= 50 else 'quality-low')
            
            html += f"""
    <div class="result {status_class}">
        <h3>{r['mcq_id'][:50]}</h3>
        <p>Type: <b>{r['type']}</b> | 
           Status: <b>{'SUCCESS' if r['success'] else 'FAILED'}</b> | 
           Quality: <span class="quality {quality_class}">{r['quality_score']:.1f}</span></p>
"""
            
            if r['svg_path'] and Path(r['svg_path']).exists():
                with open(r['svg_path'], 'r') as f:
                    svg_content = f.read()
                html += f"""
        <div style="background: white; padding: 10px; border: 1px solid #ddd;">
            {svg_content}
        </div>
"""
            else:
                html += f"""
        <p style="color: red;">Error: {r['error'][:200] if r['error'] else 'Unknown'}</p>
"""
            
            html += "    </div>\n"
        
        html += """
</body>
</html>"""
        
        return html


async def main():
    tester = Phase3ATester()
    await tester.run_tests()


if __name__ == "__main__":
    asyncio.run(main())
