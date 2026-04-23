"""
Pure AI SVG generator without reference images.
"""
import re
from typing import Optional, Tuple
import vertexai
from vertexai.generative_models import GenerativeModel
from config.settings import GEMINI_MODEL, GCP_PROJECT_ID, GCP_LOCATION
from config.prompts import PURE_GENERATION_PROMPT, DIAGRAM_TYPE_KEYWORDS
from src.utils.svg_fixer import fix_broken_svg_attributes

vertexai.init(project=GCP_PROJECT_ID, location=GCP_LOCATION)


class PureGenerator:
    """Generate SVG diagrams purely from question text using AI."""
    
    def __init__(self):
        self.model = GenerativeModel(GEMINI_MODEL)
    
    def detect_diagram_type(self, question_text: str) -> str:
        """Detect what type of diagram the question needs."""
        question_lower = question_text.lower()
        
        for diagram_type, keywords in DIAGRAM_TYPE_KEYWORDS.items():
            if any(kw in question_lower for kw in keywords):
                return diagram_type
        
        return 'general'
    
    def generate(
        self,
        question_text: str,
        subject: str,
        chapter: str,
        context: str = ""
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Generate SVG diagram from question text.
        
        Args:
            question_text: The MCQ question text
            subject: Subject (physics, chemistry, biology, math)
            chapter: Chapter name
            context: Optional related context from textbooks
            
        Returns:
            Tuple of (svg_string, error_message)
        """
        try:
            diagram_type = self.detect_diagram_type(question_text)
            
            prompt = PURE_GENERATION_PROMPT.format(
                question_text=question_text,
                subject=subject,
                chapter=chapter,
                diagram_type=diagram_type,
                context=context if context else "No additional context available."
            )
            
            response = self.model.generate_content(prompt)
            
            response_text = response.text
            
            svg = self._extract_svg(response_text)
            
            if svg:
                svg = self._optimize_svg(svg)
                is_valid, issues = self._validate_svg(svg)
                if not is_valid:
                    return None, f"Generated SVG invalid: {', '.join(issues)}"
                return svg, None
            else:
                return None, "Failed to extract SVG from response"
                
        except Exception as e:
            return None, f"Error generating SVG: {str(e)}"
    
    def _extract_svg(self, response_text: str) -> Optional[str]:
        """Extract SVG code from model response."""
        text = response_text.strip()
        
        if '```svg' in text:
            start = text.find('```svg') + 6
            end = text.find('```', start)
            if end > start:
                return text[start:end].strip()
        
        if '```' in text:
            start = text.find('```') + 3
            end = text.find('```', start)
            if end > start:
                return text[start:end].strip()
        
        if text.startswith('<svg'):
            return text
        
        start = text.find('<svg')
        end = text.find('</svg>') + 6
        if start >= 0 and end > start:
            return text[start:end]
        
        return None
    
    def _optimize_svg(self, svg: str) -> str:
        """Optimize SVG for web display with proper attributes."""
        # Fix broken attributes from Gemini
        svg = fix_broken_svg_attributes(svg)
        
        target_width = 400
        target_height = 250
        
        svg = re.sub(r'\s*width=["\'][^"\']*["\']', '', svg)
        svg = re.sub(r'\s*height=["\'][^"\']*["\']', '', svg)
        
        if 'viewBox' not in svg:
            svg = svg.replace('<svg', f'<svg viewBox="0 0 {target_width} {target_height}"', 1)
        
        svg = re.sub(
            r'<svg([^>]*?)viewBox=',
            f'<svg\\1width="{target_width}" height="{target_height}" viewBox=',
            svg,
            count=1
        )
        
        if 'xmlns=' not in svg:
            svg = svg.replace('<svg', '<svg xmlns="http://www.w3.org/2000/svg"', 1)
        
        if '<rect' in svg:
            svg = re.sub(
                r'<rect([^>]*?)fill=["\']white["\']([^>]*)>',
                r'<rect width="400" height="250"\1fill="white"\2>',
                svg
            )
            svg = re.sub(
                r'<rect fill=["\']white["\']([^>]*)>',
                r'<rect width="400" height="250" fill="white"\1>',
                svg
            )
        
        return svg.strip()
    
    def _validate_svg(self, svg: str) -> Tuple[bool, list]:
        """Validate generated SVG with comprehensive checks."""
        issues = []
        
        if not svg.startswith('<svg'):
            issues.append("Missing <svg> opening tag")
        if not svg.endswith('</svg>'):
            issues.append("Missing </svg> closing tag")
        
        if 'width=' not in svg:
            issues.append("Missing width attribute")
        if 'height=' not in svg:
            issues.append("Missing height attribute")
        if 'viewBox=' not in svg:
            issues.append("Missing viewBox attribute")
        if 'xmlns=' not in svg:
            issues.append("Missing xmlns attribute")
        
        if 'fill="white"' not in svg and 'fill="White"' not in svg:
            issues.append("Missing white background")
        
        if len(svg) > 25000:
            issues.append(f"SVG too large: {len(svg)} bytes")
        
        text_matches = re.findall(r'<text[^>]*>', svg)
        for text_tag in text_matches:
            if 'font-size' not in text_tag:
                issues.append("Text element missing font-size")
                break
        
        return len(issues) == 0, issues
