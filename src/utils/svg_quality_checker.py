"""
SVG Quality Checker - validates generated SVG quality.
Checks for common issues like disconnected lines, overlapping text, missing labels, etc.
"""
import re
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import math


@dataclass
class BoundingBox:
    x: float
    y: float
    width: float
    height: float
    
    def overlaps(self, other: 'BoundingBox', padding: float = 5) -> bool:
        return not (
            self.x + self.width + padding < other.x or
            other.x + other.width + padding < self.x or
            self.y + self.height + padding < other.y or
            other.y + other.height + padding < self.y
        )
    
    def center(self) -> Tuple[float, float]:
        return (self.x + self.width / 2, self.y + self.height / 2)


@dataclass
class QualityIssue:
    issue_type: str
    severity: str  # 'error', 'warning', 'info'
    description: str
    location: Optional[str] = None


@dataclass
class QualityScore:
    overall_score: float
    issues: List[QualityIssue]
    should_fallback: bool
    breakdown: Dict[str, float]


def parse_viewbox(svg: str) -> Optional[Tuple[float, float, float, float]]:
    match = re.search(r'viewBox=["\']?([\d\.\s]+)["\']?', svg)
    if match:
        parts = match.group(1).split()
        if len(parts) >= 4:
            return tuple(float(p) for p in parts[:4])
    return None


def parse_dimensions(svg: str) -> Optional[Tuple[float, float]]:
    width_match = re.search(r'width=["\']?(\d+(?:\.\d+)?)', svg)
    height_match = re.search(r'height=["\']?(\d+(?:\.\d+)?)', svg)
    
    if width_match and height_match:
        return (float(width_match.group(1)), float(height_match.group(1)))
    
    viewbox = parse_viewbox(svg)
    if viewbox:
        return (viewbox[2], viewbox[3])
    
    return None


def extract_element_info(element) -> Dict:
    info = {
        'tag': element.tag.split('}')[-1] if '}' in element.tag else element.tag,
        'attrib': element.attrib,
        'bbox': None
    }
    
    tag = info['tag']
    attrib = element.attrib
    
    try:
        if tag == 'rect':
            x = float(attrib.get('x', 0))
            y = float(attrib.get('y', 0))
            w = float(attrib.get('width', 0))
            h = float(attrib.get('height', 0))
            info['bbox'] = BoundingBox(x, y, w, h)
        
        elif tag == 'circle':
            cx = float(attrib.get('cx', 0))
            cy = float(attrib.get('cy', 0))
            r = float(attrib.get('r', 0))
            info['bbox'] = BoundingBox(cx - r, cy - r, 2 * r, 2 * r)
        
        elif tag == 'ellipse':
            cx = float(attrib.get('cx', 0))
            cy = float(attrib.get('cy', 0))
            rx = float(attrib.get('rx', 0))
            ry = float(attrib.get('ry', 0))
            info['bbox'] = BoundingBox(cx - rx, cy - ry, 2 * rx, 2 * ry)
        
        elif tag == 'line':
            x1 = float(attrib.get('x1', 0))
            y1 = float(attrib.get('y1', 0))
            x2 = float(attrib.get('x2', 0))
            y2 = float(attrib.get('y2', 0))
            info['bbox'] = BoundingBox(
                min(x1, x2), min(y1, y2),
                abs(x2 - x1) or 1, abs(y2 - y1) or 1
            )
        
        elif tag == 'text':
            x = float(attrib.get('x', 0))
            y = float(attrib.get('y', 0))
            text = element.text or ''
            font_size = float(re.search(r'\d+', attrib.get('font-size', '14')).group()) if 'font-size' in attrib else 14
            estimated_width = len(text) * font_size * 0.6
            info['bbox'] = BoundingBox(x, y - font_size, estimated_width, font_size * 1.2)
            info['text'] = text
        
        elif tag == 'path':
            info['bbox'] = BoundingBox(0, 0, 100, 100)
    except (ValueError, TypeError):
        pass
    
    return info


def count_elements(svg: str) -> Dict[str, int]:
    counts = {}
    for tag in ['rect', 'circle', 'ellipse', 'line', 'path', 'text', 'polygon', 'polyline']:
        counts[tag] = len(re.findall(f'<{tag}[\\s>]', svg, re.IGNORECASE))
    return counts


def check_structure(svg: str) -> List[QualityIssue]:
    issues = []
    
    if '<svg' not in svg.lower():
        issues.append(QualityIssue('structure', 'error', 'Missing <svg> root element'))
    elif '</svg>' not in svg.lower():
        issues.append(QualityIssue('structure', 'error', 'Missing closing </svg> tag'))
    
    if 'xmlns' not in svg:
        issues.append(QualityIssue('structure', 'warning', 'Missing xmlns attribute'))
    
    if 'viewBox' not in svg:
        issues.append(QualityIssue('structure', 'warning', 'Missing viewBox attribute'))
    
    return issues


def check_dimensions(svg: str) -> List[QualityIssue]:
    issues = []
    dims = parse_dimensions(svg)
    
    if not dims:
        issues.append(QualityIssue('dimensions', 'warning', 'Could not parse SVG dimensions'))
        return issues
    
    width, height = dims
    
    if width < 50 or height < 50:
        issues.append(QualityIssue('dimensions', 'error', f'SVG too small: {width}x{height}'))
    elif width > 1000 or height > 1000:
        issues.append(QualityIssue('dimensions', 'warning', f'SVG very large: {width}x{height}'))
    
    aspect = width / height if height > 0 else 0
    if aspect < 0.3 or aspect > 3:
        issues.append(QualityIssue('dimensions', 'info', f'Unusual aspect ratio: {aspect:.2f}'))
    
    return issues


def check_content(svg: str) -> List[QualityIssue]:
    issues = []
    counts = count_elements(svg)
    
    total = sum(counts.values())
    
    if total == 0:
        issues.append(QualityIssue('content', 'error', 'No shape elements found'))
    elif total < 2:
        issues.append(QualityIssue('content', 'warning', 'Very few elements - may be incomplete'))
    
    if counts.get('text', 0) == 0:
        issues.append(QualityIssue('content', 'info', 'No text labels found'))
    
    if counts.get('path', 0) > 10:
        issues.append(QualityIssue('content', 'warning', 'Many path elements - may be complex'))
    
    return issues


def check_text_overlap(svg: str) -> List[QualityIssue]:
    issues = []
    
    try:
        root = ET.fromstring(svg)
        texts = []
        
        def find_texts(element, depth=0):
            if depth > 20:
                return
            info = extract_element_info(element)
            if info['tag'] == 'text' and info.get('bbox'):
                texts.append(info)
            for child in element:
                find_texts(child, depth + 1)
        
        find_texts(root)
        
        for i, t1 in enumerate(texts):
            for t2 in texts[i+1:]:
                if t1['bbox'].overlaps(t2['bbox']):
                    issues.append(QualityIssue(
                        'overlap', 'warning',
                        f'Text elements may overlap: "{t1.get("text", "")[:20]}" and "{t2.get("text", "")[:20]}"'
                    ))
    except ET.ParseError:
        pass
    
    return issues


def check_styling(svg: str) -> List[QualityIssue]:
    issues = []
    
    if 'stroke=' not in svg and 'stroke:' not in svg:
        issues.append(QualityIssue('style', 'info', 'No stroke defined - shapes may be invisible'))
    
    if 'fill=' not in svg and 'fill:' not in svg:
        issues.append(QualityIssue('style', 'info', 'No fill defined'))
    
    color_patterns = [
        (r'red', 'red'),
        (r'blue', 'blue'),
        (r'green', 'green'),
        (r'yellow', 'yellow'),
        (r'orange', 'orange'),
        (r'purple', 'purple'),
        (r'pink', 'pink'),
    ]
    
    for pattern, color in color_patterns:
        if re.search(pattern, svg, re.IGNORECASE):
            issues.append(QualityIssue('style', 'info', f'Contains color: {color} - should be black/white for textbook'))
    
    return issues


def check_coordinate_sanity(svg: str) -> List[QualityIssue]:
    issues = []
    
    viewbox = parse_viewbox(svg)
    if not viewbox:
        return issues
    
    min_x, min_y, max_x, max_y = 0, 0, viewbox[2], viewbox[3]
    
    coord_pattern = r'(\d+\.?\d*)'
    coords = re.findall(coord_pattern, svg)
    
    if coords:
        try:
            coords_float = [float(c) for c in coords]
            out_of_bounds = 0
            
            for coord in coords_float:
                if coord < min_x - 50 or coord > max_x + 50:
                    out_of_bounds += 1
            
            if out_of_bounds > len(coords_float) * 0.2:
                issues.append(QualityIssue('coordinates', 'warning', f'{out_of_bounds} coordinates may be outside viewBox'))
        except ValueError:
            pass
    
    return issues


def calculate_quality_score(svg: str) -> QualityScore:
    all_issues = []
    
    all_issues.extend(check_structure(svg))
    all_issues.extend(check_dimensions(svg))
    all_issues.extend(check_content(svg))
    all_issues.extend(check_text_overlap(svg))
    all_issues.extend(check_styling(svg))
    all_issues.extend(check_coordinate_sanity(svg))
    
    error_count = sum(1 for i in all_issues if i.severity == 'error')
    warning_count = sum(1 for i in all_issues if i.severity == 'warning')
    info_count = sum(1 for i in all_issues if i.severity == 'info')
    
    structure_score = max(0, 100 - error_count * 30)
    content_score = max(0, 100 - warning_count * 15)
    style_score = max(0, 100 - info_count * 5)
    
    overall = (structure_score * 0.5 + content_score * 0.35 + style_score * 0.15)
    
    should_fallback = error_count > 0 or overall < 50
    
    return QualityScore(
        overall_score=overall,
        issues=all_issues,
        should_fallback=should_fallback,
        breakdown={
            'structure': structure_score,
            'content': content_score,
            'style': style_score
        }
    )


def quick_quality_check(svg: str) -> Tuple[bool, float]:
    if not svg or len(svg) < 50:
        return False, 0.0
    
    score = calculate_quality_score(svg)
    return not score.should_fallback, score.overall_score
