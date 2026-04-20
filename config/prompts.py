"""
Prompt templates for AI image generation.
"""

REFERENCE_PROMPT = """You are creating educational diagrams. Analyze the reference image and MCQ question, then generate a NEW minimalistic SVG.

REFERENCE IMAGE: [attached PNG from textbook]

MCQ QUESTION: {question_text}
SUBJECT: {subject}
CHAPTER: {chapter}

DESIGN REQUIREMENTS:
1. Create a SIMPLE, MINIMALISTIC diagram
2. Clean lines, minimal colors (black + 1-2 accent colors maximum)
3. Clear labels in English (font-size >= 14, readable on mobile)
4. Max dimensions: 400x250 pixels
5. Use viewBox="0 0 400 250" for responsiveness
6. Original design inspired by reference, NOT a copy
7. Focus on the specific concept in the question
8. Suitable for both mobile (small screen) and desktop viewing
9. No gradients, shadows, or complex effects
10. Simple geometric shapes preferred

SVG STRUCTURE (use exactly):
<svg viewBox="0 0 400 250" xmlns="http://www.w3.org/2000/svg">
  <!-- Your minimalistic diagram here -->
</svg>

Output ONLY the SVG code, no explanations or markdown."""

PURE_GENERATION_PROMPT = """Create a SIMPLE educational SVG diagram for this MCQ:

QUESTION: {question_text}
SUBJECT: {subject}
CHAPTER: {chapter}
DIAGRAM TYPE: {diagram_type}

DESIGN REQUIREMENTS:
1. SIMPLE and MINIMALISTIC - no unnecessary details
2. Clean black lines, minimal colors (max 2-3 colors)
3. Clear labels (font-size >= 14, readable on mobile)
4. Max dimensions: 400x250 pixels
5. Use viewBox="0 0 400 250"
6. Professional educational style
7. Suitable for mobile AND desktop viewing
8. Use simple shapes: lines, circles, rectangles, arrows
9. No complex effects, gradients, or shadows

SVG STRUCTURE (use exactly):
<svg viewBox="0 0 400 250" xmlns="http://www.w3.org/2000/svg">
  <!-- Your minimalistic diagram here -->
</svg>

Output ONLY the SVG code, no explanations or markdown."""

DIAGRAM_TYPE_KEYWORDS = {
    'circuit': ['circuit', 'resistor', 'capacitor', 'battery', 'current', 'voltage', 'ohm', 'ampere'],
    'graph': ['graph', 'plot', 'curve', 'axis', 'slope', 'x-axis', 'y-axis', 'versus'],
    'wave': ['wave', 'frequency', 'amplitude', 'wavelength', 'oscillation', 'periodic'],
    'cell': ['cell', 'membrane', 'nucleus', 'organism', 'tissue', 'organ', 'mitochondria'],
    'molecule': ['structure', 'bond', 'atom', 'compound', 'molecular', 'chemical formula'],
    'vector': ['force', 'vector', 'direction', 'magnitude', 'resultant', 'component'],
    'geometry': ['angle', 'triangle', 'circle', 'rectangle', 'polygon', 'radius', 'diameter'],
    'process': ['cycle', 'flow', 'step', 'reaction', 'pathway', 'sequence'],
    'anatomy': ['heart', 'brain', 'kidney', 'liver', 'lung', 'bone', 'muscle'],
    'optics': ['lens', 'mirror', 'reflection', 'refraction', 'ray', 'focal'],
}
