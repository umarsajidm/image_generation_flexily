"""
Test script for Phase 2 v3 with improved textbook-style generation.
Tests 10 MCQs covering different diagram types.
"""
import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.data_loader import get_mcqs_needing_images, MCQData
from src.utils.diagram_classifier import classify_diagram, DiagramType
from src.utils.biology_classifier import classify_biology_diagram
from src.generators.multi_reference_generator import MultiReferenceGenerator


TEST_MCQ_IDS = [
    "mcq_PHYSICS_PORTION_NUMS_PMC_MDCAT_GUIDE_BOOK_DOGAR_S__642",
    "mcq_KIPS_PHYSICS_PRACTICE_BOOK_part2_pdf_211",
    "mcq_KIPS_PHYSICS_PRACTICE_BOOK_part2_pdf_244",
    "mcq_KIPS_PHYSICS_PRACTICE_BOOK_part2_pdf_246",
    "mcq_STEP_Chemistry_practice_book_MDCAT__schoolzi_com___1258",
    "mcq_CHEMISTRY_PORTION_NUMS_PMC_MDCAT_GUIDE_BOOK_DOGAR__9254",
    "mcq_2553_KIPS_KDP_MDCAT_Biology_Practice_Book_PDF__tal_2417",
    "mcq_ERA_Biology_Practice_Book_By_SAEED_MDCAT_TEAM_part_4324",
    "mcq_ERA_Biology_Practice_Book_By_SAEED_MDCAT_TEAM_part_6668",
    "mcq_BIOLOGY_KIPS_PRACTICE_BOOK_pdf_6985",
]


async def run_test():
    print("=" * 60)
    print("Phase 2 v3 Test: 10 MCQs with Improved Textbook Style")
    print("=" * 60)
    
    all_mcqs = get_mcqs_needing_images()
    mcq_map = {m.mcq_id: m for m in all_mcqs}
    
    test_mcqs = []
    for mcq_id in TEST_MCQ_IDS:
        if mcq_id in mcq_map:
            test_mcqs.append(mcq_map[mcq_id])
        else:
            print(f"Warning: MCQ not found: {mcq_id}")
    
    print(f"\nFound {len(test_mcqs)} test MCQs")
    
    generator = MultiReferenceGenerator(
        model_name="gemini-2.5-pro",
        max_references=3,
        max_attempts=2,
        similarity_threshold=0.6,
        use_fallback=True
    )
    
    output_dir = Path("/root/image_generation_flexily/output/generated/test_v3")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    results = []
    
    for i, mcq in enumerate(test_mcqs, 1):
        print(f"\n{'='*60}")
        print(f"[{i}/{len(test_mcqs)}] Processing: {mcq.mcq_id[:50]}...")
        print(f"Subject: {mcq.subject}")
        print(f"Question: {mcq.question_text[:100]}...")
        
        classification = classify_diagram(mcq.question_text, mcq.subject, mcq.options)
        print(f"Diagram type: {classification.diagram_type.value}")
        
        if classification.diagram_type == DiagramType.BIOLOGY:
            bio_class = classify_biology_diagram(mcq.question_text, mcq.options)
            print(f"Biology subtype: {bio_class.diagram_type.value} -> {bio_class.suggested_method}")
        
        result = await generator.generate(mcq)
        
        print(f"\nResult: {'SUCCESS' if result.svg else 'FAILED'}")
        print(f"Method: {result.generation_method}")
        print(f"Quality: {result.quality_score:.1f}")
        if result.error:
            print(f"Error: {result.error[:100]}")
        
        if result.svg:
            svg_path = output_dir / f"{mcq.mcq_id[:50]}.svg"
            with open(svg_path, 'w') as f:
                f.write(result.svg)
            print(f"Saved: {svg_path}")
        
        results.append({
            'mcq_id': mcq.mcq_id,
            'subject': mcq.subject,
            'question': mcq.question_text[:100],
            'diagram_type': result.diagram_type,
            'generation_method': result.generation_method,
            'quality_score': result.quality_score,
            'success': result.svg is not None,
            'error': result.error
        })
    
    await generator.mermaid_generator.close()
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    successful = sum(1 for r in results if r['success'])
    failed = len(results) - successful
    
    print(f"\nTotal: {len(results)}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    
    if successful > 0:
        avg_quality = sum(r['quality_score'] for r in results if r['success']) / successful
        print(f"Average quality score: {avg_quality:.1f}")
    
    by_method = {}
    for r in results:
        method = r['generation_method']
        if method not in by_method:
            by_method[method] = {'success': 0, 'failed': 0}
        if r['success']:
            by_method[method]['success'] += 1
        else:
            by_method[method]['failed'] += 1
    
    print("\nBy generation method:")
    for method, stats in by_method.items():
        print(f"  {method}: {stats['success']} success, {stats['failed']} failed")
    
    results_path = output_dir / "test_results.json"
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to: {results_path}")
    
    html_path = output_dir / "view_svgs.html"
    html_content = "<html><head><title>Test Results</title></head><body>\n"
    html_content += "<h1>Phase 2 v3 Test Results</h1>\n"
    
    for r in results:
        html_content += f"<h2>{r['mcq_id'][:50]}</h2>\n"
        html_content += f"<p><b>Subject:</b> {r['subject']} | "
        html_content += f"<b>Type:</b> {r['diagram_type']} | "
        html_content += f"<b>Method:</b> {r['generation_method']} | "
        html_content += f"<b>Quality:</b> {r['quality_score']:.1f}</p>\n"
        html_content += f"<p>{r['question']}...</p>\n"
        
        svg_file = f"{r['mcq_id'][:50]}.svg"
        svg_path = output_dir / svg_file
        if svg_path.exists():
            html_content += f"<div style='border:1px solid #ccc; padding:10px; margin:10px;'>\n"
            html_content += f"<object data='{svg_file}' type='image/svg+xml' width='400' height='300'></object>\n"
            html_content += "</div>\n"
        else:
            html_content += f"<p style='color:red;'>FAILED: {r['error']}</p>\n"
    
    html_content += "</body></html>"
    
    with open(html_path, 'w') as f:
        f.write(html_content)
    print(f"HTML viewer: {html_path}")


if __name__ == "__main__":
    asyncio.run(run_test())
