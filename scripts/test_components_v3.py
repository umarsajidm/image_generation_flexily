"""
Simplified test script for Phase 2 v3.
Tests each generator separately with one MCQ each.
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.data_loader import get_mcqs_needing_images
from src.utils.diagram_classifier import classify_diagram, DiagramType
from src.utils.biology_classifier import classify_biology_diagram
from src.generators.python_svg_generator import PythonSVGGenerator
from src.generators.mermaid_generator import MermaidGenerator
from src.generators.imagen_generator import ImagenGenerator


async def test_python_generator():
    print("\n" + "="*60)
    print("Testing Python SVG Generator (Physics Graph)")
    print("="*60)
    
    mcqs = get_mcqs_needing_images()
    physics_mcqs = [m for m in mcqs if m.subject == 'physics']
    
    graph_mcqs = []
    for m in physics_mcqs[:50]:
        cls = classify_diagram(m.question_text, m.subject, m.options)
        if cls.diagram_type == DiagramType.GRAPH:
            graph_mcqs.append(m)
    
    if not graph_mcqs:
        print("No graph MCQs found")
        return
    
    mcq = graph_mcqs[0]
    print(f"\nMCQ: {mcq.question_text[:100]}...")
    
    gen = PythonSVGGenerator()
    result = await gen.generate(mcq.question_text, DiagramType.GRAPH)
    
    print(f"\nResult: {'SUCCESS' if result.success else 'FAILED'}")
    print(f"SVG length: {len(result.svg) if result.svg else 0}")
    if result.error:
        print(f"Error: {result.error[:200]}")
    
    if result.svg:
        output_dir = Path("/root/image_generation_flexily/output/generated/test_v3")
        output_dir.mkdir(parents=True, exist_ok=True)
        with open(output_dir / "python_graph_test.svg", 'w') as f:
            f.write(result.svg)
        print(f"Saved to: {output_dir / 'python_graph_test.svg'}")


async def test_mermaid_generator():
    print("\n" + "="*60)
    print("Testing Mermaid Generator (Biology Flowchart)")
    print("="*60)
    
    mcqs = get_mcqs_needing_images()
    bio_mcqs = [m for m in mcqs if m.subject == 'biology']
    
    pedigree_mcqs = []
    for m in bio_mcqs:
        if 'pedigree' in m.question_text.lower():
            pedigree_mcqs.append(m)
    
    if not pedigree_mcqs:
        print("No pedigree MCQs found, using generic cycle question")
        test_question = "The Krebs cycle involves multiple transformations. Show the main steps."
    else:
        test_question = pedigree_mcqs[0].question_text
    
    print(f"\nQuestion: {test_question[:100]}...")
    
    gen = MermaidGenerator()
    result = await gen.generate(test_question)
    
    print(f"\nResult: {'SUCCESS' if result.success else 'FAILED'}")
    print(f"SVG length: {len(result.svg) if result.svg else 0}")
    if result.error:
        print(f"Error: {result.error[:200]}")
    
    if result.svg:
        output_dir = Path("/root/image_generation_flexily/output/generated/test_v3")
        output_dir.mkdir(parents=True, exist_ok=True)
        with open(output_dir / "mermaid_test.svg", 'w') as f:
            f.write(result.svg)
        print(f"Saved to: {output_dir / 'mermaid_test.svg'}")
    
    await gen.close()


async def test_imagen_generator():
    print("\n" + "="*60)
    print("Testing Imagen Generator (Biology Anatomy)")
    print("="*60)
    
    mcqs = get_mcqs_needing_images()
    bio_mcqs = [m for m in mcqs if m.subject == 'biology']
    
    anatomy_mcqs = []
    for m in bio_mcqs:
        bio_class = classify_biology_diagram(m.question_text, m.options)
        if bio_class.suggested_method == 'imagen':
            anatomy_mcqs.append(m)
    
    if not anatomy_mcqs:
        print("No anatomy MCQs found, using generic cell question")
        test_question = "The diagram shows a plant cell with labeled organelles."
    else:
        test_question = anatomy_mcqs[0].question_text
    
    print(f"\nQuestion: {test_question[:100]}...")
    
    gen = ImagenGenerator()
    result = await gen.generate(test_question)
    
    print(f"\nResult: {'SUCCESS' if result.success else 'FAILED'}")
    print(f"Image: {result.image_path}")
    print(f"SVG overlay length: {len(result.svg_overlay) if result.svg_overlay else 0}")
    if result.error:
        print(f"Error: {result.error[:200]}")
    
    if result.combined_html:
        output_dir = Path("/root/image_generation_flexily/output/generated/test_v3")
        output_dir.mkdir(parents=True, exist_ok=True)
        with open(output_dir / "imagen_test.html", 'w') as f:
            f.write(result.combined_html)
        print(f"Saved to: {output_dir / 'imagen_test.html'}")


async def main():
    print("="*60)
    print("Phase 2 v3 Component Tests")
    print("="*60)
    
    await test_python_generator()
    await test_mermaid_generator()
    await test_imagen_generator()
    
    print("\n" + "="*60)
    print("All component tests completed!")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
