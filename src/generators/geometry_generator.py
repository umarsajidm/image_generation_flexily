"""
Geometry Generator
Generates geometric diagrams for physics/math MCQs.
Uses few-shot approach similar to Phase 3B mechanics.
"""
import re
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
from typing import Optional, List, Tuple
from dataclasses import dataclass
import math


@dataclass
class GeometryGenResult:
    success: bool
    svg: Optional[str]
    diagram_subtype: str
    error: Optional[str] = None


GEOMETRY_PROMPTS = {
    'charge_triangle': '''
Generate Python code to draw an equilateral triangle with charges at each corner.

Use this template and adapt for the specific question:

```python
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

fig, ax = plt.subplots(figsize=(8, 8))
ax.set_xlim(-2, 2)
ax.set_ylim(-2, 2)
ax.set_aspect('equal')
ax.axis('off')

# Equilateral triangle vertices
r = 1.0  # distance from center to vertices
angles = [np.pi/2, np.pi/2 + 2*np.pi/3, np.pi/2 + 4*np.pi/3]
vertices = [(r*np.cos(a), r*np.sin(a)) for a in angles]

# Draw triangle
triangle = plt.Polygon(vertices, fill=False, edgecolor='black', linewidth=2)
ax.add_patch(triangle)

# Draw charges at vertices
for i, (x, y) in enumerate(vertices):
    ax.plot(x, y, 'ko', markersize=15)
    ax.text(x, y+0.15, '+q', ha='center', va='bottom', fontsize=12, fontfamily='serif')

# Draw centroid
ax.plot(0, 0, 'ro', markersize=8)
ax.text(0.1, 0.1, 'O', fontsize=12, fontfamily='serif')

plt.tight_layout()
plt.savefig('output.svg', format='svg')
```

Question: {question}
''',

    'charge_square': '''
Generate Python code to draw a square with charges at each corner.

Use this template and adapt for the specific question:

```python
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

fig, ax = plt.subplots(figsize=(8, 8))
ax.set_xlim(-1.5, 1.5)
ax.set_ylim(-1.5, 1.5)
ax.set_aspect('equal')
ax.axis('off')

# Square vertices
a = 1.0  # half side length
vertices = [(-a, -a), (a, -a), (a, a), (-a, a)]

# Draw square
square = plt.Polygon(vertices, fill=False, edgecolor='black', linewidth=2)
ax.add_patch(square)

# Draw charges at vertices
for i, (x, y) in enumerate(vertices):
    ax.plot(x, y, 'ko', markersize=15)
    ax.text(x + 0.1*np.sign(x), y + 0.1*np.sign(y), '+q', ha='center', va='center', fontsize=12, fontfamily='serif')

# Draw center
ax.plot(0, 0, 'ro', markersize=8)
ax.text(0.1, 0.1, 'O', fontsize=12, fontfamily='serif')

plt.tight_layout()
plt.savefig('output.svg', format='svg')
```

Question: {question}
''',

    'circular_motion': '''
Generate Python code to draw circular motion with velocity and path.

Use this template and adapt for the specific question:

```python
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

fig, ax = plt.subplots(figsize=(8, 8))
ax.set_xlim(-2, 2)
ax.set_ylim(-2, 2)
ax.set_aspect('equal')
ax.axis('off')

# Draw circular path
theta = np.linspace(0, 2*np.pi, 100)
R = 1.0
ax.plot(R*np.cos(theta), R*np.sin(theta), 'k--', linewidth=1.5)

# Draw center
ax.plot(0, 0, 'ko', markersize=5)

# Object position (at top)
pos_angle = np.pi/2
x, y = R*np.cos(pos_angle), R*np.sin(pos_angle)
ax.plot(x, y, 'ko', markersize=15)

# Velocity vector (tangent)
v_scale = 0.5
vx = v_scale * np.cos(pos_angle + np.pi/2)
vy = v_scale * np.sin(pos_angle + np.pi/2)
ax.annotate('', xy=(x+vx, y+vy), xytext=(x, y),
           arrowprops=dict(arrowstyle='->', color='blue', lw=2))
ax.text(x+vx+0.1, y+vy+0.1, 'v', fontsize=12, fontfamily='serif', color='blue')

# Label
ax.text(x+0.2, y, 'P', fontsize=12, fontfamily='serif')

# Possible paths after release
ax.annotate('', xy=(x+1.5*v_scale, y+1.5*v_scale), xytext=(x+0.5*v_scale, y+0.5*v_scale),
           arrowprops=dict(arrowstyle='->', color='red', lw=1.5, linestyle='--'))

plt.tight_layout()
plt.savefig('output.svg', format='svg')
```

Question: {question}
''',

    'current_loop': '''
Generate Python code to draw a current loop with magnetic field.

Use this template and adapt for the specific question:

```python
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

fig, ax = plt.subplots(figsize=(10, 6))
ax.set_xlim(-3, 3)
ax.set_ylim(-2, 2)
ax.set_aspect('equal')
ax.axis('off')

# Draw circular loop (side view)
r = 1.0
theta = np.linspace(0, 2*np.pi, 100)
ax.plot(r*np.cos(theta), r*np.sin(theta)*0.3, 'k-', linewidth=2)

# Current direction arrows
ax.annotate('', xy=(r, 0.1), xytext=(r*0.7, 0.3),
           arrowprops=dict(arrowstyle='->', color='blue', lw=2))
ax.text(r*0.85, 0.25, 'I', fontsize=14, fontfamily='serif', color='blue')

# Center point
ax.plot(0, 0, 'ro', markersize=10)
ax.text(0.1, 0.1, 'O', fontsize=12, fontfamily='serif')

# Magnetic field at center (into page - dots)
ax.text(0, 0, '×', fontsize=20, ha='center', va='center', color='red')
ax.text(0, -0.4, 'B (into page)', fontsize=10, fontfamily='serif', ha='center')

plt.tight_layout()
plt.savefig('output.svg', format='svg')
```

Question: {question}
''',

    'resistance_triangle': '''
Generate Python code to draw a triangular resistance network.

Use this template and adapt for the specific question:

```python
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

fig, ax = plt.subplots(figsize=(8, 8))
ax.set_xlim(-1.5, 1.5)
ax.set_ylim(-1.5, 1.5)
ax.set_aspect('equal')
ax.axis('off')

# Equilateral triangle vertices
r = 1.0
angles = [np.pi/2, np.pi/2 + 2*np.pi/3, np.pi/2 + 4*np.pi/3]
vertices = [(r*np.cos(a), r*np.sin(a)) for a in angles]

# Draw triangle edges with resistors
for i in range(3):
    x1, y1 = vertices[i]
    x2, y2 = vertices[(i+1) % 3]
    ax.plot([x1, x2], [y1, y2], 'k-', linewidth=2)
    # Resistor symbol at midpoint
    mx, my = (x1+x2)/2, (y1+y2)/2
    ax.text(mx, my, 'R', fontsize=12, fontfamily='serif', ha='center', va='center',
           bbox=dict(boxstyle='square', facecolor='white', edgecolor='black'))

# Corner points
labels = ['A', 'B', 'C']
for i, (x, y) in enumerate(vertices):
    ax.plot(x, y, 'ko', markersize=8)
    ax.text(x*1.1, y*1.1, labels[i], fontsize=12, fontfamily='serif', ha='center')

plt.tight_layout()
plt.savefig('output.svg', format='svg')
```

Question: {question}
'''
}


def classify_geometry_question(question: str) -> str:
    """Classify the type of geometry diagram needed."""
    q_lower = question.lower()
    
    if 'equilateral triangle' in q_lower and 'charge' in q_lower:
        return 'charge_triangle'
    elif 'square' in q_lower and 'charge' in q_lower:
        return 'charge_square'
    elif 'triangle' in q_lower and ('charge' in q_lower or 'corner' in q_lower):
        return 'charge_triangle'
    elif any(kw in q_lower for kw in ['circular', 'circle', 'swing', 'horizontal circle']):
        return 'circular_motion'
    elif any(kw in q_lower for kw in ['current loop', 'circular loop', 'coil']):
        return 'current_loop'
    elif any(kw in q_lower for kw in ['resistance', 'resistor', 'triangle']) and 'wire' in q_lower:
        return 'resistance_triangle'
    elif 'charge' in q_lower and ('corner' in q_lower or 'arranged' in q_lower):
        return 'charge_square'
    else:
        return 'generic_geometry'


def get_geometry_prompt(question: str) -> Tuple[str, str]:
    """Get the appropriate prompt for the geometry question."""
    subtype = classify_geometry_question(question)
    
    if subtype in GEOMETRY_PROMPTS:
        prompt = GEOMETRY_PROMPTS[subtype].format(question=question)
        return prompt, subtype
    
    # Generic geometry prompt
    prompt = f'''Generate Python matplotlib code to draw a geometric diagram for this physics question.

Use matplotlib with Agg backend. Draw clean black and white diagrams with:
- Clear labels
- Appropriate aspect ratio
- Textbook style

Question: {question}

Output ONLY the Python code.
'''
    return prompt, subtype


class GeometryGenerator:
    def __init__(self):
        pass
    
    def get_prompt(self, question: str) -> Tuple[str, str]:
        """Get the prompt and subtype for a geometry question."""
        return get_geometry_prompt(question)
    
    def generate_direct(self, question: str) -> GeometryGenResult:
        """Generate geometry diagram directly (for simple cases)."""
        subtype = classify_geometry_question(question)
        
        # For simple cases, generate directly
        if subtype == 'charge_triangle':
            svg = self._generate_charge_triangle()
        elif subtype == 'charge_square':
            svg = self._generate_charge_square()
        else:
            return GeometryGenResult(
                success=False,
                svg=None,
                diagram_subtype=subtype,
                error=f'Direct generation not implemented for: {subtype}'
            )
        
        if svg:
            return GeometryGenResult(
                success=True,
                svg=svg,
                diagram_subtype=subtype,
                error=None
            )
        return GeometryGenResult(
            success=False,
            svg=None,
            diagram_subtype=subtype,
            error='Failed to generate SVG'
        )
    
    def _generate_charge_triangle(self) -> Optional[str]:
        """Generate equilateral triangle with charges."""
        fig, ax = plt.subplots(figsize=(8, 8))
        ax.set_xlim(-2, 2)
        ax.set_ylim(-2, 2)
        ax.set_aspect('equal')
        ax.axis('off')
        
        r = 1.0
        angles = [np.pi/2, np.pi/2 + 2*np.pi/3, np.pi/2 + 4*np.pi/3]
        vertices = [(r*np.cos(a), r*np.sin(a)) for a in angles]
        
        triangle = plt.Polygon(vertices, fill=False, edgecolor='black', linewidth=2)
        ax.add_patch(triangle)
        
        for i, (x, y) in enumerate(vertices):
            ax.plot(x, y, 'ko', markersize=15)
            ax.text(x, y+0.15, '+q', ha='center', va='bottom', fontsize=12, fontfamily='serif')
        
        ax.plot(0, 0, 'ro', markersize=8)
        ax.text(0.1, 0.1, 'O', fontsize=12, fontfamily='serif')
        
        plt.tight_layout()
        
        svg_path = '/tmp/geom_triangle.svg'
        plt.savefig(svg_path, format='svg', bbox_inches='tight', facecolor='white')
        plt.close()
        
        with open(svg_path, 'r') as f:
            svg = f.read()
        
        svg = re.sub(r'<\?xml[^>]*\?>', '', svg)
        svg = re.sub(r'<!DOCTYPE[^>]*>', '', svg)
        
        return svg.strip()
    
    def _generate_charge_square(self) -> Optional[str]:
        """Generate square with charges."""
        fig, ax = plt.subplots(figsize=(8, 8))
        ax.set_xlim(-1.5, 1.5)
        ax.set_ylim(-1.5, 1.5)
        ax.set_aspect('equal')
        ax.axis('off')
        
        a = 1.0
        vertices = [(-a, -a), (a, -a), (a, a), (-a, a)]
        
        square = plt.Polygon(vertices, fill=False, edgecolor='black', linewidth=2)
        ax.add_patch(square)
        
        for i, (x, y) in enumerate(vertices):
            ax.plot(x, y, 'ko', markersize=15)
            ax.text(x + 0.1*np.sign(x) if x != 0 else x, 
                   y + 0.1*np.sign(y) if y != 0 else y + 0.15, 
                   '+q', ha='center', va='center', fontsize=12, fontfamily='serif')
        
        ax.plot(0, 0, 'ro', markersize=8)
        ax.text(0.1, 0.1, 'O', fontsize=12, fontfamily='serif')
        
        plt.tight_layout()
        
        svg_path = '/tmp/geom_square.svg'
        plt.savefig(svg_path, format='svg', bbox_inches='tight', facecolor='white')
        plt.close()
        
        with open(svg_path, 'r') as f:
            svg = f.read()
        
        svg = re.sub(r'<\?xml[^>]*\?>', '', svg)
        svg = re.sub(r'<!DOCTYPE[^>]*>', '', svg)
        
        return svg.strip()


if __name__ == "__main__":
    test_questions = [
        "XYZ is an equilateral triangle. Charges +q are placed at each corner.",
        "Four identical point charges are arranged at the corners of a square.",
        "A girl swings a rock attached to a string counter-clockwise in a horizontal circle.",
    ]
    
    gen = GeometryGenerator()
    
    for q in test_questions:
        print(f"\nQ: {q[:60]}...")
        prompt, subtype = gen.get_prompt(q)
        print(f"  Subtype: {subtype}")
        print(f"  Prompt length: {len(prompt)} chars")
