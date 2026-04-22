"""
Prompt templates for AI image generation.
"""

REFERENCE_PROMPT = """You are creating educational diagrams for MCQ questions.
Analyze the reference image carefully and generate a detailed, accurate SVG diagram.

REFERENCE IMAGE: [attached from textbook]

MCQ QUESTION: {question_text}
SUBJECT: {subject}

BASE REQUIREMENTS:
- Use viewBox="0 0 400 250" with white background
- Include ALL elements from the reference image that are relevant to the question
- Use font-size 14-18px for clear readability
- stroke-width 2 for main elements, 1 for details
- Black lines; use one accent color (blue #0066cc) only for emphasis if needed
- Center the diagram with 20px margins

SUBJECT-SPECIFIC GUIDELINES:

For PHYSICS graphs:
- Draw clear X and Y axes with arrowheads pointing right and up
- Label both axes with variable names (use proper symbols)
- Mark the origin (0)
- Draw accurate curves matching the mathematical relationship
- Include grid lines or tick marks if reference has them
- Label key points on curves

For PHYSICS diagrams (pendulums, circuits, optics, forces):
- Show ALL labeled components from reference
- Include position markers (X, Y, A, B, P, Q, etc.)
- Draw motion paths with dashed lines and arrows
- Label all forces, angles, measurements (h, v, θ, F, etc.)
- Show energy levels or equilibrium positions

For CHEMISTRY structures and reactions:
- Draw atoms and bonds clearly
- Label all functional groups and elements
- Show reaction arrows with conditions
- Include electron movements if applicable
- Use proper bond notation (single/double/triple lines)

For BIOLOGY diagrams:
- Label ALL parts mentioned in question
- Show processes with numbered arrows
- Use simple shapes for cells/organelles
- Include membrane boundaries
- Add scale bars if relevant

For MATH graphs and geometry:
- Draw axes with proper scale
- Show all labeled points
- Include tangents, asymptotes, or regions if shown
- Use proper geometric notation

SVG TEMPLATE (use exactly):
<svg width="400" height="250" viewBox="0 0 400 250" xmlns="http://www.w3.org/2000/svg">
  <rect width="400" height="250" fill="white"/>
  <!-- Your detailed diagram here -->
</svg>

Study the reference image carefully. Include the SAME level of detail.
Output ONLY valid SVG code, no explanations."""

PURE_GENERATION_PROMPT = """Create a detailed educational SVG diagram for this MCQ question.

QUESTION: {question_text}
SUBJECT: {subject}
DIAGRAM TYPE: {diagram_type}

BASE REQUIREMENTS:
- Use viewBox="0 0 400 250" with white background
- Include ALL relevant elements for the question
- Use font-size 14-18px for clear readability
- stroke-width 2 for main elements
- Black lines, optionally one accent color for emphasis
- Center the diagram with 20px margins

DIAGRAM-SPECIFIC GUIDELINES:

For graphs:
- Draw X and Y axes with arrowheads
- Label both axes with variable names
- Draw curves that accurately represent the relationship
- Mark key points and intersections

For circuits:
- Use standard symbols or simple boxes
- Label all components (R, C, L, V, I)
- Show current direction with arrows

For physics diagrams:
- Label all forces and vectors
- Show motion with dashed arrows
- Include measurements and angles

For chemical structures:
- Draw bonds as lines
- Label atoms and functional groups
- Show reaction conditions if applicable

For biology diagrams:
- Label all structures
- Show processes with arrows
- Use simple cell/organ shapes

SVG TEMPLATE:
<svg width="400" height="250" viewBox="0 0 400 250" xmlns="http://www.w3.org/2000/svg">
  <rect width="400" height="250" fill="white"/>
  <!-- Your detailed diagram here -->
</svg>

Output ONLY valid SVG code."""

DIAGRAM_TYPE_KEYWORDS = {
    'circuit': ['circuit', 'resistor', 'capacitor', 'battery', 'current', 'voltage', 'ohm', 'ampere', 'inductor', 'transformer'],
    'graph': ['graph', 'plot', 'curve', 'axis', 'slope', 'x-axis', 'y-axis', 'versus', 'versus', 'function', 'equation'],
    'wave': ['wave', 'frequency', 'amplitude', 'wavelength', 'oscillation', 'periodic', 'sine', 'harmonic'],
    'cell': ['cell', 'membrane', 'nucleus', 'organism', 'tissue', 'organ', 'mitochondria', 'ribosome', 'organelle'],
    'molecule': ['structure', 'bond', 'atom', 'compound', 'molecular', 'chemical formula', 'isomer', 'functional group'],
    'vector': ['force', 'vector', 'direction', 'magnitude', 'resultant', 'component', 'torque', 'moment'],
    'geometry': ['angle', 'triangle', 'circle', 'rectangle', 'polygon', 'radius', 'diameter', 'perimeter', 'area'],
    'process': ['cycle', 'flow', 'step', 'reaction', 'pathway', 'sequence', 'metabolism', 'photosynthesis'],
    'anatomy': ['heart', 'brain', 'kidney', 'liver', 'lung', 'bone', 'muscle', 'artery', 'vein', 'nerve'],
    'optics': ['lens', 'mirror', 'reflection', 'refraction', 'ray', 'focal', 'prism', 'convex', 'concave'],
    'pendulum': ['pendulum', 'swing', 'oscillat', 'bob', 'string', 'period', 'amplitude', 'equilibrium'],
    'thermodynamics': ['heat', 'temperature', 'entropy', 'enthalpy', 'gas', 'pressure', 'volume', 'isothermal', 'adiabatic'],
}
