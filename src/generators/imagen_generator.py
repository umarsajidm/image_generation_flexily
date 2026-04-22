"""
Imagen 3 SVG Generator for Biology Anatomy Diagrams
Generates biology anatomy diagrams using Vertex AI Imagen 3,
then creates SVG label overlays using Gemini Vision.
"""
import os
import re
import base64
import tempfile
import asyncio
import hashlib
from pathlib import Path
from typing import Optional, List, Tuple
from dataclasses import dataclass

from google import genai
from google.genai import types
from google.cloud import aiplatform
from vertexai.preview.vision_models import ImageGenerationModel

from config.settings import GCP_PROJECT_ID, GCP_LOCATION
from src.utils.svg_validator import inject_textbook_style


IMAGEN_PROMPT_TEMPLATE = """A black and white line-art illustration of {subject}, drawn in the style of a vintage educational biology textbook. 

CRITICAL REQUIREMENTS:
- High contrast, clean vector-style lines
- White background
- NO TEXT, NO LABELS, NO LETTERS, NO NUMBERS anywhere in the image
- NO ARROWS or indicator lines with text
- The image must be completely devoid of any writing
- Simple, clear educational diagram style
- Precise anatomical accuracy

Subject to draw: {description}
"""

LABEL_OVERLAY_PROMPT = """You are given an unlabeled biology diagram and need to create an SVG overlay with labels.

Study the image and generate an SVG that contains ONLY:
1. <text> elements for labels
2. <line> elements for arrows pointing to structures

SVG REQUIREMENTS:
- Use viewBox="0 0 512 512" to match the image dimensions
- Use font-family="Times New Roman, serif" for all text
- Use font-size="14" for labels
- Make arrows point FROM label TO the structure
- Keep labels outside the main diagram when possible
- Use stroke="black" and stroke-width="1" for arrows

STRUCTURES TO LABEL:
{structures}

Generate ONLY the SVG code, no explanations. The SVG should be transparent (no background) so it can be overlaid on the image.
"""


@dataclass
class ImagenGenResult:
    success: bool
    image_path: Optional[str]
    svg_overlay: Optional[str]
    combined_html: Optional[str]
    error: Optional[str]


class ImagenGenerator:
    def __init__(self, imagen_region: str = "us-central1"):
        self.imagen_region = imagen_region
        self.gemini_client = genai.Client(
            vertexai=True,
            project=GCP_PROJECT_ID,
            location=GCP_LOCATION
        )
        self._imagen_model = None
        self.output_dir = Path("/root/image_generation_flexily/output/generated/imagen")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_imagen_model(self):
        if self._imagen_model is None:
            aiplatform.init(project=GCP_PROJECT_ID, location=self.imagen_region)
            self._imagen_model = ImageGenerationModel.from_pretrained("imagen-3.0-generate-001")
        return self._imagen_model
    
    def _extract_structures_from_question(self, question: str) -> List[str]:
        structures = []
        
        structure_patterns = [
            r'labeled\s+(\w+)',
            r'structure[s]?\s+(\w+)',
            r'identify\s+(?:the\s+)?(\w+)',
            r'part[s]?\s+(\w+)',
            r'region[s]?\s+(\w+)',
        ]
        
        for pattern in structure_patterns:
            matches = re.findall(pattern, question.lower())
            structures.extend(matches)
        
        anatomy_terms = [
            'nucleus', 'membrane', 'mitochondria', 'ribosome', 'golgi',
            'endoplasmic', 'lysosome', 'vacuole', 'chloroplast', 'cytoplasm',
            'cell wall', 'cell membrane', 'nuclear envelope', 'nucleolus',
            'chromosome', 'dna', 'rna', 'centriole', 'cytoskeleton',
            'heart', 'atrium', 'ventricle', 'aorta', 'valve',
            'kidney', 'nephron', 'glomerulus', 'tubule',
            'lung', 'alveoli', 'bronchi', 'trachea',
            'neuron', 'axon', 'dendrite', 'synapse',
        ]
        
        for term in anatomy_terms:
            if term in question.lower() and term not in structures:
                structures.append(term)
        
        return structures[:5]
    
    def _generate_imagen_prompt(self, question: str) -> str:
        question_lower = question.lower()
        
        if 'cell' in question_lower:
            if 'plant' in question_lower:
                description = "a plant cell showing cell wall, chloroplasts, large central vacuole, nucleus, and other organelles"
            elif 'animal' in question_lower:
                description = "an animal cell showing nucleus, mitochondria, endoplasmic reticulum, Golgi apparatus, and other organelles"
            else:
                description = "a typical eukaryotic cell showing nucleus, mitochondria, endoplasmic reticulum, Golgi apparatus, ribosomes, and cell membrane"
        elif 'synapse' in question_lower or 'synaptic' in question_lower:
            description = "a synaptic junction showing presynaptic terminal, synaptic cleft, postsynaptic membrane, and neurotransmitter vesicles"
        elif 'heart' in question_lower:
            description = "a cross-section of the human heart showing four chambers: right atrium, left atrium, right ventricle, left ventricle, and major blood vessels"
        elif 'kidney' in question_lower:
            description = "a cross-section of the kidney showing cortex, medulla, nephrons, and renal pelvis"
        elif 'neuron' in question_lower:
            description = "a neuron showing cell body (soma), dendrites, axon, myelin sheath, and axon terminals"
        elif 'membrane' in question_lower:
            description = "a cell membrane showing phospholipid bilayer, integral proteins, peripheral proteins, and cholesterol molecules"
        elif 'mitochondria' in question_lower:
            description = "a mitochondrion showing outer membrane, inner membrane, cristae, matrix, and DNA"
        elif 'chloroplast' in question_lower:
            description = "a chloroplast showing outer membrane, inner membrane, thylakoids, grana, and stroma"
        elif 'lung' in question_lower or 'respiratory' in question_lower:
            description = "the human respiratory system showing trachea, bronchi, bronchioles, and alveoli"
        elif 'flatworm' in question_lower or 'excretory' in question_lower:
            description = "the excretory system of a flatworm showing flame cells and excretory tubules"
        else:
            description = f"a biological diagram related to: {question[:100]}"
        
        return IMAGEN_PROMPT_TEMPLATE.format(
            subject="biological structure",
            description=description
        )
    
    async def generate_image(self, question: str) -> Tuple[Optional[str], Optional[str]]:
        try:
            model = self._get_imagen_model()
            prompt = self._generate_imagen_prompt(question)
            
            print(f"[Imagen] Generating image with prompt: {prompt[:100]}...")
            
            response = model.generate_images(
                prompt=prompt,
                number_of_images=1,
                aspect_ratio="1:1",
                safety_filter_level="block_few",
                person_generation="allow_adult",
            )
            
            if not response or len(response.images) == 0:
                return None, "No image generated"
            
            image = response.images[0]
            
            image_hash = hashlib.md5(question.encode()).hexdigest()[:8]
            image_path = self.output_dir / f"anatomy_{image_hash}.png"
            
            image.save(str(image_path))
            
            print(f"[Imagen] Image saved to: {image_path}")
            
            return str(image_path), None
            
        except Exception as e:
            return None, f"Imagen generation error: {str(e)}"
    
    async def generate_svg_overlay(
        self,
        image_path: str,
        structures: List[str]
    ) -> Tuple[Optional[str], Optional[str]]:
        try:
            with open(image_path, 'rb') as f:
                image_data = f.read()
            
            prompt = LABEL_OVERLAY_PROMPT.format(
                structures=', '.join(structures) if structures else 'main structures visible in the diagram'
            )
            
            response = self.gemini_client.models.generate_content(
                model="gemini-2.5-pro",
                contents=[
                    types.Part.from_bytes(data=image_data, mime_type="image/png"),
                    prompt
                ]
            )
            
            svg = response.text
            
            svg_match = re.search(r'<svg[\s\S]*?</svg>', svg, re.IGNORECASE)
            if svg_match:
                svg = svg_match.group(0)
            else:
                code_match = re.search(r'```(?:svg)?\s*([\s\S]*?)```', svg)
                if code_match:
                    svg = code_match.group(1).strip()
                    if not svg.startswith('<svg'):
                        svg = f'<svg viewBox="0 0 512 512" xmlns="http://www.w3.org/2000/svg">{svg}</svg>'
            
            svg = inject_textbook_style(svg)
            
            return svg, None
            
        except Exception as e:
            return None, f"SVG overlay generation error: {str(e)}"
    
    def _create_combined_html(
        self,
        image_path: str,
        svg_overlay: str
    ) -> str:
        with open(image_path, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode()
        
        html = f'''<!DOCTYPE html>
<html>
<head>
    <style>
        .container {{
            position: relative;
            width: 512px;
            height: 512px;
        }}
        .container img {{
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
        }}
        .container svg {{
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
        }}
    </style>
</head>
<body>
    <div class="container">
        <img src="data:image/png;base64,{image_data}" alt="Biology Diagram">
        {svg_overlay}
    </div>
</body>
</html>'''
        
        return html
    
    async def generate(self, question: str) -> ImagenGenResult:
        image_path, image_error = await self.generate_image(question)
        
        if image_error or not image_path:
            return ImagenGenResult(
                success=False,
                image_path=None,
                svg_overlay=None,
                combined_html=None,
                error=image_error or "Failed to generate image"
            )
        
        structures = self._extract_structures_from_question(question)
        
        svg_overlay, overlay_error = await self.generate_svg_overlay(image_path, structures)
        
        combined_html = None
        if svg_overlay:
            combined_html = self._create_combined_html(image_path, svg_overlay)
        
        if overlay_error:
            print(f"[Imagen] Warning: SVG overlay failed: {overlay_error}")
        
        return ImagenGenResult(
            success=True,
            image_path=image_path,
            svg_overlay=svg_overlay,
            combined_html=combined_html,
            error=None
        )


async def generate_anatomy_diagram(question: str) -> ImagenGenResult:
    generator = ImagenGenerator()
    return await generator.generate(question)
