"""
Reference-based SVG generator using Gemini Vision.
"""
import os
import base64
from typing import Optional, Tuple, Dict, Any
from pathlib import Path
import google.generativeai as genai
from config.settings import GEMINI_MODEL, GCP_PROJECT_ID
from config.prompts import REFERENCE_PROMPT


class ReferenceGenerator:
    """Generate SVG diagrams based on reference images from textbooks."""
    
    def __init__(self):
        self.model = genai.GenerativeModel(GEMINI_MODEL)
        self.textbook_images_dir = Path("/root/organized_data/textbooks/images")
    
    def generate_from_reference(
        self,
        question_text: str,
        subject: str,
        chapter: str,
        reference_image_path: str
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Generate SVG based on reference image and question.
        
        Args:
            question_text: The MCQ question text
            subject: Subject (physics, chemistry, biology, math)
            chapter: Chapter name
            reference_image_path: Path to reference image from textbook
            
        Returns:
            Tuple of (svg_string, error_message)
        """
        try:
            # Load reference image
            ref_path = self._resolve_image_path(reference_image_path)
            if not ref_path or not ref_path.exists():
                return None, f"Reference image not found: {reference_image_path}"
            
            # Read and encode image
            with open(ref_path, 'rb') as f:
                image_data = f.read()
            
            # Create prompt
            prompt = REFERENCE_PROMPT.format(
                question_text=question_text,
                subject=subject,
                chapter=chapter
            )
            
            # Generate with Gemini Vision
            response = self.model.generate_content([
                {"text": prompt},
                {
                    "inline_data": {
                        "mime_type": "image/png",
                        "data": base64.b64encode(image_data).decode()
                    }
                }
            ])
            
            # Extract SVG from response
            svg = self._extract_svg(response.text)
            
            if svg:
                # Validate and optimize
                svg = self._optimize_svg(svg)
                is_valid, issues = self._validate_svg(svg)
                if not is_valid:
                    return None, f"Generated SVG invalid: {', '.join(issues)}"
                return svg, None
            else:
                return None, "Failed to extract SVG from response"
                
        except Exception as e:
            return None, f"Error generating SVG: {str(e)}"
    
    def _resolve_image_path(self, image_path: str) -> Optional[Path]:
        """Resolve image path to actual file location."""
        # Handle different path formats
        if image_path.startswith('/'):
            return Path(image_path)
        
        # Check in textbook images directory
        full_path = self.textbook_images_dir / image_path
        if full_path.exists():
            return full_path
        
        # Try with just the filename
        filename = os.path.basename(image_path)
        full_path = self.textbook_images_dir / filename
        if full_path.exists():
            return full_path
        
        return None
    
    def _extract_svg(self, response_text: str) -> Optional[str]:
        """Extract SVG code from model response."""
        # Remove markdown code blocks if present
        text = response_text.strip()
        
        # Handle ```svg ... ``` blocks
        if '```svg' in text:
            start = text.find('```svg') + 6
            end = text.find('```', start)
            if end > start:
                return text[start:end].strip()
        
        # Handle ``` ... ``` blocks
        if '```' in text:
            start = text.find('```') + 3
            end = text.find('```', start)
            if end > start:
                return text[start:end].strip()
        
        # Check if response is directly SVG
        if text.startswith('<svg'):
            return text
        
        # Try to find SVG tag in response
        start = text.find('<svg')
        end = text.find('</svg>') + 6
        if start >= 0 and end > start:
            return text[start:end]
        
        return None
    
    def _optimize_svg(self, svg: str) -> str:
        """Optimize SVG for web display."""
        # Ensure proper viewBox
        if 'viewBox' not in svg:
            svg = svg.replace('<svg', '<svg viewBox="0 0 400 250"')
        
        # Ensure xmlns
        if 'xmlns' not in svg:
            svg = svg.replace('<svg', '<svg xmlns="http://www.w3.org/2000/svg"')
        
        return svg.strip()
    
    def _validate_svg(self, svg: str) -> Tuple[bool, list]:
        """Validate generated SVG."""
        issues = []
        
        if not svg.startswith('<svg') or not svg.endswith('</svg>'):
            issues.append("Invalid SVG structure")
        
        if len(svg) > 15000:
            issues.append(f"SVG too large: {len(svg)} bytes")
        
        # Check for reasonable dimensions in viewBox
        import re
        viewBox_match = re.search(r'viewBox="(\d+)\s+(\d+)\s+(\d+)\s+(\d+)"', svg)
        if viewBox_match:
            width = int(viewBox_match.group(3))
            height = int(viewBox_match.group(4))
            if width > 500 or height > 350:
                issues.append(f"Dimensions too large: {width}x{height}")
        
        return len(issues) == 0, issues
