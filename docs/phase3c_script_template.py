"""
Phase 3C Batch Processor - Chemistry Molecules
Uses RDKit for deterministic molecular diagrams.
"""
import json
import sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.data_loader import get_mcqs_needing_images
from src.utils.diagram_classifier import classify_diagram, DiagramType
from src.generators.chemistry_molecule_generator import ChemistryMoleculeGenerator
from src.utils.svg_quality_checker import calculate_quality_score
from src.utils.svg_validator import inject_textbook_style


class Phase3CProcessor:
    def __init__(self, test_limit: int = None):
        self.test_limit = test_limit
        self.output_dir = Path("/root/image_generation_flexily/output/generated/phase3c")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.results_file = self.output_dir / "phase3c_results.jsonl"
        self.checkpoint_file = self.output_dir / "checkpoint.jsonl"
        self.failed_compounds_file = self.output_dir / "failed_compounds.txt"
        self.failed_compounds = set()
    
    def get_molecule_mcqs(self):
        mcqs = get_mcqs_needing_images()
        chemistry_mcqs = [m for m in mcqs if m.subject == 'chemistry']
        
        molecule_mcqs = []
        for m in chemistry_mcqs:
            cls = classify_diagram(m.question_text, m.subject, m.options)
            if cls.diagram_type == DiagramType.MOLECULE:
                molecule_mcqs.append(m)
        
        if self.test_limit:
            molecule_mcqs = molecule_mcqs[:self.test_limit]
        
        return molecule_mcqs
    
    def load_checkpoint(self):
        processed = set()
        if self.checkpoint_file.exists():
            with open(self.checkpoint_file, 'r') as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        processed.add(data['mcq_id'])
        return processed
    
    def save_checkpoint(self, result: dict):
        with open(self.checkpoint_file, 'a') as f:
            f.write(json.dumps(result) + '\n')
    
    def save_failed_compound(self, compound_name: str, mcq_id: str):
        self.failed_compounds.add(compound_name)
        with open(self.failed_compounds_file, 'a') as f:
            f.write(f"{compound_name}\t{mcq_id}\n")
    
    def process_mcq(self, generator: ChemistryMoleculeGenerator, mcq) -> dict:
        result = generator.generate(mcq.question_text, mcq.subject)
        
        output = {
            'mcq_id': mcq.mcq_id,
            'question_text': mcq.question_text[:200],
            'subject': mcq.subject,
            'diagram_type': 'molecule',
            'compound_names': result.compound_name,
            'smiles': result.smiles,
            'generation_method': result.method,
            'quality_score': 0,
            'success': result.success,
            'svg_path': None,
            'error': result.error,
            'generated_at': datetime.now().isoformat(),
        }
        
        if result.success and result.svg:
            svg_path = self.output_dir / f"{mcq.mcq_id[:50]}.svg"
            svg = inject_textbook_style(result.svg)
            with open(svg_path, 'w') as f:
                f.write(svg)
            
            quality = calculate_quality_score(svg)
            output['svg_path'] = str(svg_path)
            output['quality_score'] = quality.overall_score
        else:
            if result.compound_name:
                self.save_failed_compound(result.compound_name, mcq.mcq_id)
        
        return output
    
    def run(self):
        print("=" * 70)
        print("Phase 3C Batch Processor - Chemistry Molecules")
        print("Using RDKit for Deterministic Rendering")
        print("=" * 70)
        
        mcqs = self.get_molecule_mcqs()
        processed = self.load_checkpoint()
        
        remaining = [m for m in mcqs if m.mcq_id not in processed]
        
        print(f"\nTotal MCQs: {len(mcqs)}")
        print(f"Already processed: {len(processed)}")
        print(f"Remaining: {len(remaining)}")
        
        if not remaining:
            print("\nAll MCQs already processed!")
            return
        
        generator = ChemistryMoleculeGenerator()
        
        print("\n" + "-" * 70)
        print("Processing...")
        print("-" * 70)
        
        stats = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'rdkit': 0,
            'quality_scores': [],
        }
        
        for i, mcq in enumerate(remaining, 1):
            print(f"\n[{i}/{len(remaining)}] {mcq.mcq_id[:40]}...")
            
            try:
                output = self.process_mcq(generator, mcq)
                self.save_checkpoint(output)
                stats['total'] += 1
                
                if output['success']:
                    stats['success'] += 1
                    stats['quality_scores'].append(output['quality_score'])
                    
                    if output['generation_method'] == 'rdkit':
                        stats['rdkit'] += 1
                    
                    status = '✓' if output['quality_score'] >= 70 else '~'
                    print(f"  {status} Compound: {output['compound_names']}")
                    print(f"     SMILES: {output['smiles']}")
                    print(f"     Quality: {output['quality_score']:.1f}")
                else:
                    stats['failed'] += 1
                    print(f"  ✗ Error: {output['error'][:60] if output['error'] else 'unknown'}")
            
            except Exception as e:
                stats['failed'] += 1
                print(f"  ✗ Exception: {str(e)[:80]}")
                self.save_checkpoint({
                    'mcq_id': mcq.mcq_id,
                    'success': False,
                    'error': str(e),
                })
        
        self.print_summary(stats)
        self.generate_html_viewer()
    
    def print_summary(self, stats):
        print("\n" + "=" * 70)
        print("PROCESSING COMPLETE")
        print("=" * 70)
        
        if stats['total'] > 0:
            rate = 100 * stats['success'] / stats['total']
            print(f"\nTotal processed: {stats['total']}")
            print(f"Success: {stats['success']} ({rate:.1f}%)")
            print(f"Failed: {stats['failed']}")
            print(f"\nRDKit renders: {stats['rdkit']}")
            
            if stats['quality_scores']:
                avg_q = sum(stats['quality_scores']) / len(stats['quality_scores'])
                print(f"\nAverage quality: {avg_q:.1f}")
        
        if self.failed_compounds:
            print(f"\nFailed compounds (add to dictionary):")
            for compound in sorted(self.failed_compounds):
                print(f"  - {compound}")
            print(f"\nSee: {self.failed_compounds_file}")
    
    def generate_html_viewer(self):
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
    <title>Phase 3C Results - Chemistry Molecules</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .result { border: 1px solid #ccc; margin: 10px 0; padding: 10px; background: white; }
        .success { border-color: #4CAF50; }
        .failed { border-color: #f44336; }
        svg { max-width: 400px; max-height: 300px; }
    </style>
</head>
<body>
    <h1>Phase 3C Results - Chemistry Molecules</h1>
    <p>Generated: """ + datetime.now().strftime("%Y-%m-%d %H:%M") + """</p>
"""
        
        for r in results:
            status_class = 'success' if r.get('success') else 'failed'
            html += f"""
    <div class="result {status_class}">
        <h3>{r['mcq_id'][:50]}</h3>
        <p>Compound: <b>{r.get('compound_names', 'N/A')}</b> |
           SMILES: <b>{r.get('smiles', 'N/A')}</b> |
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
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--test-limit', type=int, default=None)
    args = parser.parse_args()
    
    processor = Phase3CProcessor(test_limit=args.test_limit)
    processor.run()
