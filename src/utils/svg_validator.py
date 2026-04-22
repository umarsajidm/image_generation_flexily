import xml.etree.ElementTree as ET
import re
import html
from typing import Tuple, Optional
from dataclasses import dataclass


@dataclass
class ValidationResult:
    is_valid: bool
    svg: Optional[str] = None
    error: Optional[str] = None
    fixes_applied: list = None
    
    def __post_init__(self):
        if self.fixes_applied is None:
            self.fixes_applied = []


def fix_malformed_xml(svg: str) -> Tuple[str, list]:
    fixes = []
    
    svg = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', svg)
    if '&amp;' not in svg:
        svg = re.sub(r'&(?!(?:amp|lt|gt|quot|apos|#\d+|#x[0-9a-fA-F]+);)', '&amp;', svg)
    
    return svg, fixes


def fix_broken_attributes(svg: str) -> Tuple[str, list]:
    fixes = []
    
    patterns = [
        (r'stroke-(?=\s*[/>\s])', 'stroke-width="1"'),
        (r'stroke-(?=\s+)', 'stroke-width="1"'),
        (r'fill-(?=\s*[/>\s])', 'fill="none"'),
        (r'fill-(?=\s+)', 'fill="none"'),
        (r'stroke-width-(?=\s*[/>\s])', 'stroke-width="1"'),
        (r'stroke-opacity-(?=\s*[/>\s])', 'stroke-opacity="1"'),
        (r'fill-opacity-(?=\s*[/>\s])', 'fill-opacity="1"'),
    ]
    
    for pattern, replacement in patterns:
        if re.search(pattern, svg):
            svg = re.sub(pattern, replacement, svg)
            fixes.append(f"Fixed broken attribute: {pattern}")
    
    svg = re.sub(r'(\w)-(\s*/>)', r'\1\2', svg)
    
    return svg, fixes


def fix_missing_attributes(svg: str) -> Tuple[str, list]:
    fixes = []
    
    if 'viewBox' not in svg:
        match = re.search(r'width=["\']?(\d+)["\']?', svg)
        if match:
            width = match.group(1)
            match_h = re.search(r'height=["\']?(\d+)["\']?', svg)
            height = match_h.group(1) if match_h else width
            svg = svg.replace('<svg', f'<svg viewBox="0 0 {width} {height}"', 1)
            fixes.append("Added missing viewBox")
    
    if 'xmlns' not in svg:
        svg = svg.replace('<svg', '<svg xmlns="http://www.w3.org/2000/svg"', 1)
        fixes.append("Added missing xmlns")
    
    return svg, fixes


def extract_svg_from_response(response: str) -> Tuple[Optional[str], Optional[str]]:
    if not response:
        return None, "Empty response"
    
    code_block_match = re.search(r'```(?:svg)?\s*([\s\S]*?)```', response, re.IGNORECASE)
    if code_block_match:
        svg = code_block_match.group(1).strip()
        return svg, None
    
    svg_match = re.search(r'<svg[\s\S]*?</svg>', response, re.IGNORECASE)
    if svg_match:
        svg = svg_match.group(0)
        return svg, None
    
    if '<svg' in response and '</svg>' in response:
        start = response.find('<svg')
        end = response.rfind('</svg>') + 6
        svg = response[start:end]
        return svg, None
    
    return None, "No SVG found in response"


def validate_svg_structure(svg: str) -> Tuple[bool, Optional[str]]:
    try:
        root = ET.fromstring(svg)
    except ET.ParseError as e:
        return False, f"XML parse error: {str(e)}"
    
    if root.tag != 'svg' and not root.tag.endswith('svg'):
        return False, f"Root element is not <svg>, got: {root.tag}"
    
    shape_elements = ['rect', 'circle', 'ellipse', 'line', 'polyline', 'polygon', 'path', 'text', 'g']
    has_content = False
    
    def check_children(element, depth=0):
        nonlocal has_content
        if depth > 20:
            return
        for child in element:
            tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
            if tag in shape_elements:
                has_content = True
                return
            check_children(child, depth + 1)
    
    check_children(root)
    
    if not has_content:
        return False, "SVG has no shape elements"
    
    return True, None


def validate_dimensions(svg: str, min_size: int = 50, max_size: int = 1000) -> Tuple[bool, Optional[str]]:
    width_match = re.search(r'width=["\']?(\d+(?:\.\d+)?)', svg)
    height_match = re.search(r'height=["\']?(\d+(?:\.\d+)?)', svg)
    
    if width_match and height_match:
        width = float(width_match.group(1))
        height = float(height_match.group(1))
        
        if width < min_size or height < min_size:
            return False, f"SVG too small: {width}x{height}"
        if width > max_size or height > max_size:
            return False, f"SVG too large: {width}x{height}"
    
    return True, None


def validate_and_fix_svg(svg: str) -> ValidationResult:
    if not svg or not svg.strip():
        return ValidationResult(False, error="Empty SVG input")
    
    svg = svg.strip()
    fixes_applied = []
    
    svg, fixes = fix_malformed_xml(svg)
    fixes_applied.extend(fixes)
    
    svg, fixes = fix_broken_attributes(svg)
    fixes_applied.extend(fixes)
    
    svg, fixes = fix_missing_attributes(svg)
    fixes_applied.extend(fixes)
    
    is_valid, error = validate_svg_structure(svg)
    if not is_valid:
        return ValidationResult(False, error=error, fixes_applied=fixes_applied)
    
    is_valid, error = validate_dimensions(svg)
    if not is_valid:
        return ValidationResult(False, error=error, fixes_applied=fixes_applied)
    
    try:
        ET.fromstring(svg)
    except ET.ParseError as e:
        return ValidationResult(False, error=f"Final parse error: {str(e)}", fixes_applied=fixes_applied)
    
    return ValidationResult(True, svg=svg, fixes_applied=fixes_applied)


def clean_svg(svg: str) -> str:
    if not svg:
        return svg
    
    svg = re.sub(r'\s+', ' ', svg)
    svg = re.sub(r'>\s+<', '><', svg)
    
    svg = svg.replace('<?xml version="1.0" encoding="UTF-8"?>', '')
    svg = svg.strip()
    
    return svg


TEXTBOOK_STYLE_CSS = """
<style type="text/css">
  .textbook-shape {
    fill: none;
    stroke: #111111;
    stroke-width: 2px;
    stroke-linejoin: round;
    stroke-linecap: round;
  }
  .textbook-text {
    font-family: 'Times New Roman', Times, serif;
    font-size: 14px;
    fill: #000000;
    stroke: none;
  }
  .textbook-label {
    font-family: 'Times New Roman', Times, serif;
    font-size: 12px;
    fill: #000000;
    stroke: none;
  }
  .textbook-axis {
    stroke: #000000;
    stroke-width: 1.5px;
    stroke-linecap: round;
  }
  .textbook-grid {
    stroke: #cccccc;
    stroke-width: 0.5px;
    stroke-dasharray: 4,2;
  }
</style>
"""


def inject_textbook_style(svg: str) -> str:
    """
    Inject textbook-style CSS into SVG for consistent appearance.
    
    This forces all diagrams to have:
    - Times New Roman serif fonts (Punjab textbook style)
    - Consistent black stroke colors
    - 2px line widths for shapes
    - Round line joins and caps
    """
    if not svg or not svg.strip():
        return svg
    
    style_block = TEXTBOOK_STYLE_CSS.strip()
    
    if '<style' in svg:
        style_start = svg.find('<style')
        style_end = svg.find('</style>', style_start) + 8
        existing_style = svg[style_start:style_end]
        
        enhanced_style = existing_style.replace('</style>', style_block[7:-8] + '\n  </style>')
        svg = svg[:style_start] + enhanced_style + svg[style_end:]
    else:
        svg_tag_match = re.search(r'(<svg[^>]*>)', svg, re.IGNORECASE)
        if svg_tag_match:
            insert_pos = svg_tag_match.end()
            svg = svg[:insert_pos] + '\n' + style_block + svg[insert_pos:]
    
    svg = re.sub(
        r'<text([^>]*)>',
        lambda m: '<text' + m.group(1) + ' class="textbook-text">',
        svg
    )
    
    svg = re.sub(
        r'font-family=["\'][^"\']*["\']',
        "font-family=\"'Times New Roman', Times, serif\"",
        svg
    )
    
    return svg


def apply_textbook_styling(svg: str) -> str:
    """
    Apply comprehensive textbook styling to an SVG.
    Combines validation, fixing, and style injection.
    """
    validation = validate_and_fix_svg(svg)
    if not validation.is_valid:
        return svg
    
    svg = validation.svg
    
    svg = inject_textbook_style(svg)
    
    return svg
