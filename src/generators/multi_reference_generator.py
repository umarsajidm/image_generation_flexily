"""
Multi-Reference SVG Generator v2
- Uses gemini-2.5-pro for better spatial reasoning
- Extracts keywords for better vector search
- Improved prompts with strict spatial rules
- Falls back to Python code generation (schemdraw/matplotlib) for poor SVG
"""
import os
import json
import base64
import time
import asyncio
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from google import genai
from google.genai import types

from config.settings import GCP_PROJECT_ID, GCP_LOCATION
from src.utils.local_vector_search import LocalVectorSearch
from src.utils.svg_validator import (
    extract_svg_from_response,
    validate_and_fix_svg,
    clean_svg,
    inject_textbook_style,
)
from src.utils.diagram_classifier import (
    classify_diagram,
    extract_visual_keywords,
    DiagramType,
    ClassificationResult
)
from src.utils.svg_quality_checker import calculate_quality_score, QualityScore
from src.utils.biology_classifier import (
    classify_biology_diagram,
    BiologyDiagramType,
    BiologyClassificationResult
)
from src.generators.python_svg_generator import PythonSVGGenerator, PythonGenResult
from src.generators.mermaid_generator import MermaidGenerator, MermaidGenResult
from src.generators.imagen_generator import ImagenGenerator, ImagenGenResult
from src.generators.chemistry_molecule_generator import ChemistryMoleculeGenerator, MoleculeGenResult
from src.utils.mechanics_router import classify_mechanics_subtype, get_subtype_confidence


@dataclass
class ReferenceImage:
    path: str
    chunk_id: str
    subject: str
    content: str
    similarity: float


@dataclass
class GenerationResult:
    mcq_id: str
    svg: Optional[str]
    error: Optional[str]
    attempts: int
    references_used: List[str]
    fixes_applied: List[str]
    diagram_type: str
    generation_method: str
    quality_score: float


SYSTEM_PROMPT = """You are an expert technical illustrator creating textbook-quality SVG diagrams for Punjab Board Chemistry/Physics.

STRICT SPATIAL RULES:
1. Canvas: Always use <svg viewBox="0 0 500 400" xmlns="http://www.w3.org/2000/svg"> for a standard coordinate system.
2. Layout: Mentally map a grid. Keep objects aligned to coordinates ending in 0 or 5 (e.g., x="100", y="150").
3. Shapes: Use basic primitives (<rect>, <circle>, <line>, <polygon>). 
   - DO NOT use complex cubic bezier curves (<path d="C...">) unless absolutely necessary for smooth curves.
   - For simple curves, use quadratic beziers (<path d="Q...">) or simple arcs.
4. Styling: Use clean, educational black-and-white styles.
   - Fill: "white", "black", or "none"
   - Stroke: "black" with stroke-width="2"
   - Example: <rect x="50" y="50" width="100" height="60" fill="white" stroke="black" stroke-width="2"/>
5. Labels: Use <text font-family="Arial, sans-serif" font-size="14" fill="black">. 
   - Position labels carefully so they don't overlap with lines or shapes.
   - Use text-anchor="middle" for centered labels.
6. Axes: For graphs, draw axes as simple lines with arrows at ends.
7. Units: Include units in labels where appropriate (V, A, Ω, m/s, etc.)

OUTPUT: Generate ONLY valid, self-contained SVG code. No markdown, no explanations, no comments about what you're doing."""

USER_PROMPT_TEMPLATE = """Generate an educational SVG diagram for this multiple-choice question.

QUESTION:
{question}

{options_section}

SUBJECT: {subject}

DIAGRAM TYPE: {diagram_type}

REFERENCE IMAGES: I have provided {num_references} textbook reference images above. Study their style and recreate similar educational diagrams.

Generate ONLY the SVG code. No markdown formatting. No explanations."""


class MultiReferenceGenerator:
    def __init__(
        self,
        model_name: str = "gemini-2.5-pro",
        max_references: int = 3,
        max_attempts: int = 2,
        rate_limit_delay: float = 2.0,
        similarity_threshold: float = 0.6,
        use_fallback: bool = True
    ):
        self.model_name = model_name
        self.max_references = max_references
        self.max_attempts = max_attempts
        self.rate_limit_delay = rate_limit_delay
        self.similarity_threshold = similarity_threshold
        self.use_fallback = use_fallback
        
        self.client = genai.Client(
            vertexai=True,
            project=GCP_PROJECT_ID,
            location=GCP_LOCATION
        )
        
        self.vector_search = LocalVectorSearch()
        self.python_generator = PythonSVGGenerator()
        self.mermaid_generator = MermaidGenerator()
        self.imagen_generator = ImagenGenerator()
        self.chemistry_generator = ChemistryMoleculeGenerator()
        self._metadata_cache = None
    
    def _mcq_to_dict(self, mcq) -> Dict:
        if hasattr(mcq, '__dataclass_fields__'):
            return {
                'mcq_id': mcq.mcq_id,
                'question_text': mcq.question_text,
                'options': mcq.options,
                'subject': mcq.subject,
                'source_file': mcq.source_file,
                'source_page': mcq.source_page,
                'correct_answer_key': mcq.correct_answer_key,
                'explanation': mcq.explanation,
            }
        return mcq
    
    async def find_references(self, query_text: str, limit: int = 5) -> List[ReferenceImage]:
        keywords, _ = extract_visual_keywords(query_text)
        
        search_query = keywords if keywords else query_text
        
        results = await self.vector_search.search(
            search_query, 
            limit=limit * 2, 
            threshold=self.similarity_threshold
        )
        
        references = []
        
        for result in results:
            if not result.get('has_image'):
                continue
            
            image_paths = result.get('image_paths', [])
            if not image_paths:
                continue
            
            for img_path in image_paths:
                if os.path.exists(img_path):
                    references.append(ReferenceImage(
                        path=img_path,
                        chunk_id=result['id'],
                        subject=result.get('subject', ''),
                        content=result.get('content', '')[:500],
                        similarity=result['similarity']
                    ))
                    break
            
            if len(references) >= limit:
                break
        
        return references
    
    def _build_prompt(
        self, 
        mcq: Dict, 
        references: List[ReferenceImage],
        classification: ClassificationResult
    ) -> Tuple[str, List[Tuple[bytes, str]]]:
        question = mcq.get('question_text', '')
        options = mcq.get('options', {})
        subject = mcq.get('subject', 'general')
        
        options_text = ""
        if isinstance(options, dict):
            for key in ['A', 'B', 'C', 'D']:
                if key in options and options[key]:
                    options_text += f"{key}. {options[key]}\n"
        elif isinstance(options, list):
            for i, opt in enumerate(options):
                if opt:
                    options_text += f"{chr(65+i)}. {opt}\n"
        
        options_section = f"OPTIONS:\n{options_text}" if options_text else ""
        
        prompt = USER_PROMPT_TEMPLATE.format(
            question=question,
            options_section=options_section,
            subject=subject,
            diagram_type=classification.description,
            num_references=len(references)
        )
        
        image_parts = []
        for ref in references[:self.max_references]:
            if os.path.exists(ref.path):
                try:
                    with open(ref.path, 'rb') as f:
                        image_data = f.read()
                    image_parts.append((image_data, 'image/png'))
                except Exception as e:
                    print(f"Error reading {ref.path}: {e}")
        
        return prompt, image_parts
    
    async def _generate_raw_svg(
        self,
        prompt: str,
        image_parts: List[Tuple[bytes, str]]
    ) -> Tuple[Optional[str], Optional[str], List[str]]:
        contents = []
        
        for img_data, mime_type in image_parts:
            contents.append(types.Part.from_bytes(
                data=img_data,
                mime_type=mime_type
            ))
        
        contents.append(prompt)
        
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT
                )
            )
            
            raw_response = response.text
            
            svg, extract_error = extract_svg_from_response(raw_response)
            if extract_error:
                return None, extract_error, []
            
            validation = validate_and_fix_svg(svg)
            if not validation.is_valid:
                return None, validation.error, validation.fixes_applied
            
            clean_result = clean_svg(validation.svg)
            return clean_result, None, validation.fixes_applied
            
        except Exception as e:
            return None, str(e), []
    
    async def _try_python_fallback(
        self,
        question: str,
        classification: ClassificationResult
    ) -> Tuple[Optional[str], Optional[str]]:
        if not self.use_fallback:
            return None, "Python fallback disabled"
        
        diagram_type = classification.diagram_type
        
        if diagram_type == DiagramType.MOLECULE:
            result: MoleculeGenResult = self.chemistry_generator.generate(
                question=question,
                subject='chemistry'
            )
            
            if result.success and result.svg:
                svg = inject_textbook_style(result.svg)
                return svg, None
            else:
                return None, f"Chemistry molecule generator failed: {result.error}"
        
        if diagram_type == DiagramType.MECHANICS:
            subtype, confidence = get_subtype_confidence(question)
            print(f"  Mechanics subtype: {subtype.value} (confidence: {confidence:.2f})")
        
        if diagram_type == DiagramType.OPTICS:
            print(f"  Using optics few-shot prompt")
        
        supported_types = [
            DiagramType.CIRCUIT, DiagramType.GRAPH, 
            DiagramType.MECHANICS, DiagramType.WAVES,
            DiagramType.OPTICS, DiagramType.GEOMETRY,
            DiagramType.APPARATUS
        ]
        
        if diagram_type in supported_types:
            result: PythonGenResult = await self.python_generator.generate(
                question=question,
                diagram_type=diagram_type,
                classification=classification
            )
            
            if result.success and result.svg:
                return result.svg, None
            else:
                return None, result.error
        
        return None, f"No Python generator for diagram type: {diagram_type.value}"
    
    async def _try_biology_generator(
        self,
        question: str,
        options: dict
    ) -> Tuple[Optional[str], Optional[str], str]:
        """Try appropriate biology generator based on diagram subtype."""
        bio_class = classify_biology_diagram(question, options)
        
        method = bio_class.suggested_method
        
        if method == 'mermaid':
            result: MermaidGenResult = await self.mermaid_generator.generate(question)
            if result.success and result.svg:
                return result.svg, None, 'mermaid'
            else:
                return None, f"Mermaid failed: {result.error}", 'mermaid_failed'
        
        elif method == 'imagen':
            result: ImagenGenResult = await self.imagen_generator.generate(question)
            if result.success:
                if result.svg_overlay:
                    return result.svg_overlay, None, 'imagen_svg'
                else:
                    return None, "Imagen generated image but SVG overlay failed", 'imagen_partial'
            else:
                return None, f"Imagen failed: {result.error}", 'imagen_failed'
        
        else:
            result: PythonGenResult = await self.python_generator.generate(
                question=question,
                diagram_type=DiagramType.BIOLOGY,
                classification=None
            )
            
            if result.success and result.svg:
                return result.svg, None, 'python_biology'
            else:
                return None, result.error, 'python_failed'
    
    async def generate(self, mcq) -> GenerationResult:
        mcq_dict = self._mcq_to_dict(mcq)
        mcq_id = mcq_dict.get('mcq_id', 'unknown')
        question_text = mcq_dict.get('question_text', '')
        subject = mcq_dict.get('subject', 'general')
        options = mcq_dict.get('options', {})
        
        classification = classify_diagram(question_text, subject, options)
        
        keywords, _ = extract_visual_keywords(question_text)
        search_query = keywords if keywords else question_text
        references = await self.find_references(search_query, limit=5)
        reference_paths = [r.path for r in references]
        
        deterministic_types = [
            DiagramType.GRAPH, DiagramType.CIRCUIT, DiagramType.WAVES,
            DiagramType.MECHANICS, DiagramType.OPTICS
        ]
        
        if classification.diagram_type in deterministic_types:
            print(f"[{mcq_id[:40]}] Using Python code generation (primary)...")
            svg, error = await self._try_python_fallback(question_text, classification)
            
            if svg:
                quality = calculate_quality_score(svg)
                print(f"[{mcq_id[:40]}] Python SUCCESS - Quality: {quality.overall_score:.1f}")
                return GenerationResult(
                    mcq_id=mcq_id,
                    svg=svg,
                    error=None,
                    attempts=1,
                    references_used=reference_paths,
                    fixes_applied=['Python code generation (primary method)'],
                    diagram_type=classification.diagram_type.value,
                    generation_method='python_code',
                    quality_score=quality.overall_score
                )
            else:
                print(f"[{mcq_id[:40]}] Python failed, falling back to raw SVG: {error[:50] if error else 'unknown'}")
        
        prompt, image_parts = self._build_prompt(mcq_dict, references, classification)
        
        last_error = None
        all_fixes = []
        best_svg = None
        best_quality = 0.0
        
        for attempt in range(1, self.max_attempts + 1):
            svg, error, fixes = await self._generate_raw_svg(prompt, image_parts)
            
            if svg:
                quality = calculate_quality_score(svg)
                
                if quality.overall_score > best_quality:
                    best_svg = svg
                    best_quality = quality.overall_score
                    all_fixes = fixes
                
                if not quality.should_fallback:
                    return GenerationResult(
                        mcq_id=mcq_id,
                        svg=svg,
                        error=None,
                        attempts=attempt,
                        references_used=reference_paths,
                        fixes_applied=fixes,
                        diagram_type=classification.diagram_type.value,
                        generation_method='gemini_svg',
                        quality_score=quality.overall_score
                    )
            else:
                last_error = error
            
            time.sleep(self.rate_limit_delay)
        
        if self.use_fallback:
            if classification.diagram_type == DiagramType.BIOLOGY:
                print(f"Routing biology diagram to specialized generator for {mcq_id}")
                svg, error, method = await self._try_biology_generator(question_text, options)
                
                if svg:
                    quality = calculate_quality_score(svg)
                    return GenerationResult(
                        mcq_id=mcq_id,
                        svg=svg,
                        error=None,
                        attempts=self.max_attempts + 1,
                        references_used=reference_paths,
                        fixes_applied=[f'Used biology {method} generator'],
                        diagram_type=classification.diagram_type.value,
                        generation_method=f'biology_{method}',
                        quality_score=quality.overall_score
                    )
                else:
                    last_error = f"Biology generator failed: {error}"
            
            elif best_quality < 50 and classification.diagram_type not in deterministic_types:
                print(f"Quality low ({best_quality:.1f}), trying Python fallback for {mcq_id}")
                svg, error = await self._try_python_fallback(question_text, classification)
                
                if svg:
                    quality = calculate_quality_score(svg)
                    return GenerationResult(
                        mcq_id=mcq_id,
                        svg=svg,
                        error=None,
                        attempts=self.max_attempts + 1,
                        references_used=reference_paths,
                        fixes_applied=['Used Python fallback'],
                        diagram_type=classification.diagram_type.value,
                        generation_method='python_code',
                        quality_score=quality.overall_score
                    )
                else:
                    last_error = f"Python fallback failed: {error}"
        
        if best_svg:
            return GenerationResult(
                mcq_id=mcq_id,
                svg=best_svg,
                error=None,
                attempts=self.max_attempts,
                references_used=reference_paths,
                fixes_applied=all_fixes,
                diagram_type=classification.diagram_type.value,
                generation_method='gemini_svg_low_quality',
                quality_score=best_quality
            )
        
        return GenerationResult(
            mcq_id=mcq_id,
            svg=None,
            error=last_error,
            attempts=self.max_attempts,
            references_used=reference_paths,
            fixes_applied=all_fixes,
            diagram_type=classification.diagram_type.value,
            generation_method='failed',
            quality_score=0.0
        )
