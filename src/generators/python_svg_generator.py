"""
Python SVG Generator - generates SVG via Python code (schemdraw, matplotlib).
Used as fallback when raw SVG generation produces poor results.
"""
import os
import re
import json
import subprocess
import tempfile
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from io import BytesIO

from google import genai
from google.genai import types

from config.settings import GCP_PROJECT_ID, GCP_LOCATION
from src.utils.diagram_classifier import DiagramType, ClassificationResult
from src.utils.svg_validator import inject_textbook_style
from src.utils.mechanics_router import classify_mechanics_subtype, MechanicsSubtype
from src.generators.mechanics_prompts import build_mechanics_prompt, build_optics_prompt


MATPLOTLIB_TEXTBOOK_SETUP = '''
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

# Textbook-style matplotlib settings
plt.rcParams.update({
    'font.family': 'serif',
    'font.serif': ['Times New Roman', 'DejaVu Serif', 'serif'],
    'font.size': 14,
    'axes.labelsize': 14,
    'axes.titlesize': 16,
    'xtick.labelsize': 12,
    'ytick.labelsize': 12,
    'legend.fontsize': 12,
    'figure.titlesize': 16,
    'axes.linewidth': 1.5,
    'lines.linewidth': 2.0,
    'lines.markersize': 8,
    'axes.edgecolor': 'black',
    'axes.facecolor': 'white',
    'figure.facecolor': 'white',
    'savefig.facecolor': 'white',
    'savefig.edgecolor': 'white',
    'axes.grid': False,
    'axes.spines.top': True,
    'axes.spines.right': True,
    'axes.spines.bottom': True,
    'axes.spines.left': True,
    'xtick.direction': 'in',
    'ytick.direction': 'in',
    'xtick.major.size': 6,
    'ytick.major.size': 6,
    'xtick.minor.size': 3,
    'ytick.minor.size': 3,
})
'''


@dataclass
class PythonGenResult:
    success: bool
    svg: Optional[str]
    code: Optional[str]
    error: Optional[str]


CIRCUIT_PROMPT = """You are an expert at writing Python code to generate circuit diagrams using the schemdraw library.

Generate Python code to draw the circuit described below. The code must:
1. Set matplotlib backend to 'Agg' first: import matplotlib; matplotlib.use('Agg')
2. Use schemdraw library
3. Save the output to 'output.svg' 
4. Be self-contained and executable
5. Use appropriate circuit elements (Battery, Resistor, Capacitor, etc.)
6. Label components properly with fontsize=12
7. Keep circuits simple and educational

Question: {question}

Output ONLY the Python code, no explanations. Use this template:

```python
import matplotlib
matplotlib.use('Agg')
import schemdraw
from schemdraw import elements as elm

d = schemdraw.Drawing()
# Add your circuit elements here
d += elm.Battery().up().label('V', fontsize=12)
d += elm.Resistor().right().label('R', fontsize=12)
d.save('output.svg')
```
"""

GRAPH_PROMPT = """You are an expert at writing Python code to generate graphs using matplotlib.

Generate Python code to draw the graph described below. The code must:
1. Use matplotlib.pyplot
2. Save the output to 'output.svg'
3. Use black and white style (no colors except grayscale)
4. Label axes properly with serif fonts
5. Use appropriate font sizes (14pt minimum)
6. Set figure size to (8, 6) inches
7. Use solid black lines (linewidth=2)
8. Include proper axis labels with units if applicable

Question: {question}

Output ONLY the Python code, no explanations. Use this template:

```python
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

# Textbook-style settings
plt.rcParams.update({{'font.family': 'serif', 'font.size': 14}})

fig, ax = plt.subplots(figsize=(8, 6))

# Generate x and y data
x = np.linspace(0, 10, 100)
y = x**2  # Replace with actual function

# Plot with black line
ax.plot(x, y, 'k-', linewidth=2)

# Labels
ax.set_xlabel('Label (unit)', fontsize=14)
ax.set_ylabel('Label (unit)', fontsize=14)
ax.tick_params(labelsize=12)

plt.tight_layout()
plt.savefig('output.svg', format='svg')
```
"""

MECHANICS_PROMPT = """You are an expert at writing Python code to generate physics mechanics diagrams using matplotlib.

Generate Python code to draw the mechanics diagram described below. The code must:
1. Use matplotlib.pyplot and matplotlib.patches
2. Save the output to 'output.svg'
3. Use black and white style

KEY MODULES:
- patches.Rectangle: Draw blocks, masses, surfaces
- patches.Polygon: Draw inclined planes, wedges
- patches.Circle: Draw pulleys, circular objects
- patches.Arc: Draw angle indicators
- ax.annotate(): Draw force vectors with arrowstyle='->' or arrowstyle='-|>'
- ax.plot(): Draw strings, ropes, tension lines

FORCE VECTORS:
- Draw force arrows with ax.annotate('', xy=(end_x, end_y), xytext=(start_x, start_y),
  arrowprops=dict(arrowstyle='->', color='black', lw=2))
- Common forces: mg (weight), N (normal), T (tension), f (friction), F (applied force)

LABELS:
- Use serif fonts with fontsize=12
- Label forces at arrow midpoints or ends
- Mark angles with Greek letters (theta, alpha, beta)

Question: {question}

Output ONLY the Python code, no explanations. Use this template:

```python
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

plt.rcParams.update({{'font.family': 'serif', 'font.size': 14}})

fig, ax = plt.subplots(figsize=(8, 6))
ax.set_xlim(0, 10)
ax.set_ylim(0, 10)
ax.set_aspect('equal')
ax.axis('off')

# Draw objects
block = patches.Rectangle((2, 2), 2, 1, fill=False, edgecolor='black', linewidth=2)
ax.add_patch(block)

# Draw force arrow
ax.annotate('', xy=(4, 2.5), xytext=(2, 2.5),
            arrowprops=dict(arrowstyle='->', color='black', lw=2))
ax.text(3, 3, 'F', fontsize=14, ha='center')

plt.tight_layout()
plt.savefig('output.svg', format='svg')
```
"""

OPTICS_PROMPT = """You are an expert at writing Python code to generate optical ray diagrams using matplotlib.

Generate Python code to draw the optics diagram described below. The code must:
1. Use matplotlib.pyplot and matplotlib.patches
2. Save the output to 'output.svg'
3. Use black and white style

KEY CONCEPTS:
- Thin lens equation: 1/f = 1/do + 1/di (f=focal length, do=object distance, di=image distance)
- Magnification: m = -di/do = hi/ho
- Ray tracing: Draw 3 principal rays from object through lens/mirror

DRAWING ELEMENTS:
- patches.Arc: Draw lenses (convex/concave) and mirrors (spherical)
- ax.plot(): Draw light rays as straight lines with arrow markers
- ax.annotate(): Draw arrows on ray lines to show direction
- patches.FancyArrow: Show ray direction

PRINCIPAL RAYS FOR LENSES:
1. Ray parallel to axis → passes through focal point
2. Ray through center → continues straight
3. Ray through focal point → exits parallel to axis

PRINCIPAL RAYS FOR MIRRORS:
1. Ray parallel to axis → reflects through focal point
2. Ray through center → reflects back on itself
3. Ray through focal point → reflects parallel to axis

Question: {question}

Output ONLY the Python code, no explanations. Use this template:

```python
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

plt.rcParams.update({{'font.family': 'serif', 'font.size': 14}})

fig, ax = plt.subplots(figsize=(10, 6))
ax.set_xlim(-5, 15)
ax.set_ylim(-5, 5)
ax.set_aspect('equal')

# Draw principal axis
ax.axhline(y=0, color='gray', linewidth=0.5, linestyle='--')

# Draw lens at x=5
lens_x = 5
ax.plot([lens_x, lens_x], [-2, 2], 'k-', linewidth=3)
ax.text(lens_x, 2.5, 'Lens', fontsize=12, ha='center')

# Draw focal points
f = 3  # focal length
ax.plot([lens_x - f, lens_x - f], [-0.1, 0.1], 'ko', markersize=5)
ax.plot([lens_x + f, lens_x + f], [-0.1, 0.1], 'ko', markersize=5)
ax.text(lens_x - f, -0.5, 'F', fontsize=12, ha='center')
ax.text(lens_x + f, -0.5, "F'", fontsize=12, ha='center')

# Draw object (arrow at left)
obj_x, obj_y = 1, 0
obj_height = 1.5
ax.annotate('', xy=(obj_x, obj_height), xytext=(obj_x, obj_y),
            arrowprops=dict(arrowstyle='->', color='black', lw=2))

# Draw rays (example: parallel ray through focal point)
# Ray 1: Parallel to axis, then through F'
ax.plot([obj_x, lens_x], [obj_height, obj_height], 'b-', linewidth=1.5)
ax.plot([lens_x, lens_x + f + 2], [obj_height, obj_height * (lens_x + f + 2 - lens_x) / f], 'b-', linewidth=1.5)

ax.set_xlabel('Distance', fontsize=14)
ax.set_ylabel('Height', fontsize=14)
ax.axis('off')

plt.tight_layout()
plt.savefig('output.svg', format='svg')
```
"""

WAVE_PROMPT = """You are an expert at writing Python code to generate wave diagrams using matplotlib.

Generate Python code to draw the wave diagram described below. The code must:
1. Use matplotlib.pyplot and numpy
2. Save the output to 'output.svg'
3. Use black and white style
4. Show wave properties clearly (amplitude, wavelength, etc.)
5. Label important features with serif fonts
6. Use linewidth=2 for wave curves
7. Add annotations for amplitude, wavelength, etc.

Question: {question}

Output ONLY the Python code, no explanations. Use this template:

```python
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

plt.rcParams.update({{'font.family': 'serif', 'font.size': 14}})

fig, ax = plt.subplots(figsize=(10, 4))

t = np.linspace(0, 4*np.pi, 1000)
amplitude = 1
frequency = 1
y = amplitude * np.sin(frequency * t)

ax.plot(t, y, 'k-', linewidth=2)
ax.axhline(y=0, color='gray', linewidth=0.5, linestyle='--')
ax.set_xlabel('Time', fontsize=14)
ax.set_ylabel('Amplitude', fontsize=14)
ax.set_ylim(-1.5, 1.5)
ax.tick_params(labelsize=12)

# Add wavelength annotation
ax.annotate('', xy=(0, -1.2), xytext=(2*np.pi, -1.2),
            arrowprops=dict(arrowstyle='<->', color='black', lw=1.5))
ax.text(np.pi, -1.4, 'λ', fontsize=14, ha='center')

plt.tight_layout()
plt.savefig('output.svg', format='svg')
```
"""

BIOLOGY_PROMPT = """You are an expert at writing Python code to generate biological diagrams using matplotlib.

Generate Python code to draw the biological diagram described below. The code must:
1. Use matplotlib.pyplot and matplotlib.patches
2. Save the output to 'output.svg'
3. Use black and white style (no colors)
4. Draw cell structures, membranes, organelles as simple shapes
5. Label all important structures with serif fonts
6. Use circles for cells, ellipses for organelles, lines for membranes
7. Use linewidth=2 for all shapes
8. Position labels carefully to avoid overlap

Question: {question}

Output ONLY the Python code, no explanations. Use this template:

```python
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches

plt.rcParams.update({{'font.family': 'serif', 'font.size': 12}})

fig, ax = plt.subplots(figsize=(8, 6))
ax.set_xlim(0, 10)
ax.set_ylim(0, 10)
ax.set_aspect('equal')
ax.axis('off')

# Draw cell membrane (circle or ellipse)
cell = patches.Circle((5, 5), 3, fill=False, edgecolor='black', linewidth=2)
ax.add_patch(cell)

# Draw nucleus
nucleus = patches.Circle((5, 5), 1, fill=False, edgecolor='black', linewidth=2)
ax.add_patch(nucleus)

# Labels with arrows
ax.annotate('Nucleus', xy=(5, 5), xytext=(7, 7),
            fontsize=12, ha='center',
            arrowprops=dict(arrowstyle='->', color='black', lw=1))

plt.tight_layout()
plt.savefig('output.svg', format='svg')
```
"""

MOLECULE_PROMPT = """You are an expert at writing Python code to draw molecular structures.

Generate Python code to draw the molecular structure described below. The code must:
1. Use matplotlib.pyplot
2. Save the output to 'output.svg'
3. Use black and white style
4. Draw atoms as circles with element labels
5. Draw bonds as lines connecting atoms
6. Label all atoms and bonds

Question: {question}

Output ONLY the Python code, no explanations. Use this template:

```python
import matplotlib.pyplot as plt

fig, ax = plt.subplots(figsize=(8, 6))

# Draw atoms as circles
ax.plot(0, 0, 'o', markersize=30, markerfacecolor='white', markeredgecolor='black', markeredgewidth=2)
ax.text(0, 0, 'C', ha='center', va='center', fontsize=12)

# Draw bonds as lines
ax.plot([0, 1], [0, 0], 'k-', linewidth=2)

ax.set_xlim(-1, 2)
ax.set_ylim(-1, 1)
ax.set_aspect('equal')
ax.axis('off')
plt.tight_layout()
plt.savefig('output.svg', format='svg')
```
"""


class PythonSVGGenerator:
    def __init__(self):
        self.client = genai.Client(
            vertexai=True,
            project=GCP_PROJECT_ID,
            location=GCP_LOCATION
        )
        self.model_name = "gemini-2.5-pro"
    
    def _get_prompt_template(self, diagram_type: DiagramType) -> str:
        prompts = {
            DiagramType.CIRCUIT: CIRCUIT_PROMPT,
            DiagramType.GRAPH: GRAPH_PROMPT,
            DiagramType.MECHANICS: MECHANICS_PROMPT,
            DiagramType.WAVES: WAVE_PROMPT,
            DiagramType.OPTICS: OPTICS_PROMPT,
            DiagramType.GEOMETRY: GRAPH_PROMPT,
            DiagramType.BIOLOGY: BIOLOGY_PROMPT,
            DiagramType.MOLECULE: MOLECULE_PROMPT,
            DiagramType.APPARATUS: BIOLOGY_PROMPT,
        }
        return prompts.get(diagram_type, GRAPH_PROMPT)
    
    def _build_enhanced_mechanics_prompt(self, question: str) -> str:
        """Build enhanced mechanics prompt with few-shot code example."""
        subtype = classify_mechanics_subtype(question)
        return build_mechanics_prompt(question, subtype)
    
    def _build_enhanced_optics_prompt(self, question: str) -> str:
        """Build enhanced optics prompt with few-shot code example."""
        return build_optics_prompt(question)
    
    async def generate_code(
        self,
        question: str,
        diagram_type: DiagramType,
        classification: ClassificationResult = None,
        use_enhanced_prompts: bool = True
    ) -> Tuple[Optional[str], Optional[str]]:
        if use_enhanced_prompts and diagram_type == DiagramType.MECHANICS:
            prompt = self._build_enhanced_mechanics_prompt(question)
        elif use_enhanced_prompts and diagram_type == DiagramType.OPTICS:
            prompt = self._build_enhanced_optics_prompt(question)
        else:
            prompt_template = self._get_prompt_template(diagram_type)
            prompt = prompt_template.format(question=question)
        
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            
            code = response.text
            
            code = code.replace("```python\n", "").replace("```python", "").replace("```Python\n", "").replace("```Python", "")
            code_match = re.search(r'```(?:python)?\s*([\s\S]*?)```', code)
            if code_match:
                code = code_match.group(1).strip()
            
            code = code.strip()
            if code.startswith("```"):
                code = code[3:]
            if code.endswith("```"):
                code = code[:-3]
            code = code.strip()
            
            return code, None
        except Exception as e:
            return None, str(e)
    
    def execute_code(self, code: str, working_dir: str = None) -> Tuple[bool, Optional[str], Optional[str]]:
        if working_dir is None:
            working_dir = tempfile.mkdtemp()
        
        code_path = os.path.join(working_dir, 'generate_svg.py')
        output_path = os.path.join(working_dir, 'output.svg')
        
        safe_code = self._sanitize_code(code)
        
        # Add warning suppression
        safe_code = "import warnings\nwarnings.filterwarnings('ignore')\n" + safe_code
        
        with open(code_path, 'w') as f:
            f.write(safe_code)
        
        try:
            venv_python = '/root/image_generation_flexily/venv/bin/python'
            python_exe = venv_python if os.path.exists(venv_python) else 'python3'
            result = subprocess.run(
                [python_exe, '-W', 'ignore', code_path],
                cwd=working_dir,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                return False, None, f"Execution error: {result.stderr[:500]}"
            
            if not os.path.exists(output_path):
                return False, None, f"Output SVG file was not created. Stdout: {result.stdout[:200]}"
            
            with open(output_path, 'r') as f:
                svg = f.read()
            
            return True, svg, None
            
        except subprocess.TimeoutExpired:
            return False, None, "Code execution timed out"
        except Exception as e:
            return False, None, str(e)
    
    def _sanitize_code(self, code: str) -> str:
        dangerous_patterns = [
            (r'import\s+os', '# import os removed for safety'),
            (r'import\s+subprocess', '# import subprocess removed for safety'),
            (r'import\s+sys', '# import sys removed for safety'),
            (r'open\s*\([^)]*["\']w["\']', '# file write removed'),
            (r'eval\s*\(', '# eval removed'),
            (r'exec\s*\(', '# exec removed'),
            (r'__import__', '# __import__ removed'),
        ]
        
        for pattern, replacement in dangerous_patterns:
            code = re.sub(pattern, replacement, code, flags=re.IGNORECASE)
        
        return code
    
    async def generate(
        self,
        question: str,
        diagram_type: DiagramType,
        classification: ClassificationResult = None
    ) -> PythonGenResult:
        code, code_error = await self.generate_code(question, diagram_type, classification)
        
        if code_error or not code:
            return PythonGenResult(
                success=False,
                svg=None,
                code=code,
                error=code_error or "Failed to generate code"
            )
        
        success, svg, exec_error = self.execute_code(code)
        
        if success and svg:
            svg = self._clean_svg(svg)
            return PythonGenResult(
                success=True,
                svg=svg,
                code=code,
                error=None
            )
        else:
            return PythonGenResult(
                success=False,
                svg=None,
                code=code,
                error=exec_error
            )
    
    def _clean_svg(self, svg: str) -> str:
        svg = re.sub(r'<\?xml[^>]*\?>', '', svg)
        
        svg = re.sub(r'<!DOCTYPE[^>]*>', '', svg)
        
        svg = re.sub(r'<metadata>[\s\S]*?</metadata>', '', svg, flags=re.IGNORECASE)
        
        if 'xmlns' not in svg:
            svg = svg.replace('<svg', '<svg xmlns="http://www.w3.org/2000/svg"', 1)
        
        svg = inject_textbook_style(svg)
        
        svg = svg.strip()
        
        return svg


async def generate_with_python_fallback(
    question: str,
    diagram_type: DiagramType,
    classification: ClassificationResult = None
) -> PythonGenResult:
    generator = PythonSVGGenerator()
    return await generator.generate(question, diagram_type, classification)
