"""
Mechanics Diagram Templates
Pre-built templates for common physics mechanics diagrams.
"""
import os
import subprocess
import tempfile
from typing import Optional, Tuple


PENDULUM_TEMPLATE = """
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

plt.rcParams.update({'font.family': 'serif', 'font.size': 12})

fig, ax = plt.subplots(figsize=(6, 8))
ax.set_xlim(-3, 3)
ax.set_ylim(-4, 2)
ax.set_aspect('equal')
ax.axis('off')

# Pivot point
pivot = (0, 1)
ax.plot(*pivot, 'ko', markersize=8)

# Pendulum parameters
length = 2.5
angle = 30  # degrees
angle_rad = np.radians(angle)

# Bob position
bob_x = length * np.sin(angle_rad)
bob_y = 1 - length * np.cos(angle_rad)

# Draw rod
ax.plot([pivot[0], bob_x], [pivot[1], bob_y], 'k-', linewidth=2)

# Draw bob
circle = plt.Circle((bob_x, bob_y), 0.2, fill=False, edgecolor='black', linewidth=2)
ax.add_patch(circle)
ax.text(bob_x + 0.3, bob_y, 'm', fontsize=12, ha='left')

# Draw angle arc
arc_angles = np.linspace(-angle_rad, 0, 20)
arc_x = 0.5 * np.sin(arc_angles)
arc_y = 1 - 0.5 * np.cos(arc_angles)
ax.plot(arc_x, arc_y, 'k-', linewidth=1)
ax.text(0.3, 0.6, 'theta', fontsize=12)

# Draw vertical dashed line
ax.plot([0, 0], [1, -1.5], 'k--', linewidth=1, alpha=0.5)

# Label
ax.text(0, 1.3, 'Pivot', fontsize=10, ha='center')

plt.tight_layout()
plt.savefig('output.svg', format='svg')
"""


INCLINED_PLANE_TEMPLATE = """
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

plt.rcParams.update({'font.family': 'serif', 'font.size': 12})

fig, ax = plt.subplots(figsize=(8, 6))
ax.set_xlim(0, 10)
ax.set_ylim(0, 6)
ax.set_aspect('equal')
ax.axis('off')

# Incline parameters
angle = 30  # degrees
angle_rad = np.radians(angle)

# Draw inclined plane
incline_x = [1, 8, 1]
incline_y = [1, 1, 1 + 7 * np.tan(angle_rad)]
ax.fill(incline_x, incline_y, fill=False, edgecolor='black', linewidth=2)

# Block position (center of incline)
block_center_x = 4.5
block_center_y = 1 + 3.5 * np.tan(angle_rad)
block_width = 1.5
block_height = 1

# Draw block (rotated rectangle)
cos_a, sin_a = np.cos(angle_rad), np.sin(angle_rad)
corners = [
    (-block_width/2, -block_height/2),
    (block_width/2, -block_height/2),
    (block_width/2, block_height/2),
    (-block_width/2, block_height/2),
]

rotated = []
for x, y in corners:
    rx = x * cos_a - y * sin_a + block_center_x
    ry = x * sin_a + y * cos_a + block_center_y
    rotated.append((rx, ry))

block = patches.Polygon(rotated, fill=False, edgecolor='black', linewidth=2)
ax.add_patch(block)
ax.text(block_center_x, block_center_y + 0.8, 'm', fontsize=12, ha='center')

# Draw angle arc
arc_angles = np.linspace(0, angle_rad, 20)
arc_r = 1.5
arc_x = 1 + arc_r * np.cos(arc_angles)
arc_y = 1 + arc_r * np.sin(arc_angles)
ax.plot(arc_x, arc_y, 'k-', linewidth=1)
ax.text(2.5, 1.3, 'theta', fontsize=12)

# Draw weight arrow (downward)
ax.annotate('', xy=(block_center_x, block_center_y - 1), 
            xytext=(block_center_x, block_center_y + 0.3),
            arrowprops=dict(arrowstyle='->', color='black', lw=2))
ax.text(block_center_x + 0.2, block_center_y - 0.5, 'mg', fontsize=10)

plt.tight_layout()
plt.savefig('output.svg', format='svg')
"""


PULLEY_TEMPLATE = """
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

plt.rcParams.update({'font.family': 'serif', 'font.size': 12})

fig, ax = plt.subplots(figsize=(6, 8))
ax.set_xlim(0, 6)
ax.set_ylim(0, 8)
ax.set_aspect('equal')
ax.axis('off')

# Pulley position
pulley_x, pulley_y = 3, 6
radius = 0.3

# Draw pulley
circle = plt.Circle((pulley_x, pulley_y), radius, fill=False, edgecolor='black', linewidth=2)
ax.add_patch(circle)
ax.plot(pulley_x, pulley_y, 'ko', markersize=4)

# Draw rope (left side)
ax.plot([pulley_x, pulley_x - radius], [pulley_y + radius, 7.5], 'k-', linewidth=2)
ax.plot([pulley_x - radius, pulley_x - radius], [7.5, 4], 'k-', linewidth=2)

# Draw rope (right side)
ax.plot([pulley_x + radius, pulley_x + radius], [pulley_y, 2], 'k-', linewidth=2)

# Left mass
ax.add_patch(patches.Rectangle((pulley_x - radius - 0.3, 3), 0.6, 1, 
                                fill=False, edgecolor='black', linewidth=2))
ax.text(pulley_x - radius, 3.5, 'm1', fontsize=10, ha='center')

# Right mass
ax.add_patch(patches.Rectangle((pulley_x + radius - 0.3, 1), 0.6, 1,
                                fill=False, edgecolor='black', linewidth=2))
ax.text(pulley_x + radius, 1.5, 'm2', fontsize=10, ha='center')

# Support
ax.plot([pulley_x - 0.5, pulley_x + 0.5], [7.5, 7.5], 'k-', linewidth=3)
ax.plot([pulley_x, pulley_x], [7.5, pulley_y + radius], 'k-', linewidth=2)

# Labels
ax.text(pulley_x, pulley_y - 0.6, 'T', fontsize=10, ha='center')

plt.tight_layout()
plt.savefig('output.svg', format='svg')
"""


COLLISION_TEMPLATE = """
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

plt.rcParams.update({'font.family': 'serif', 'font.size': 12})

fig, ax = plt.subplots(figsize=(8, 4))
ax.set_xlim(0, 10)
ax.set_ylim(0, 4)
ax.set_aspect('equal')
ax.axis('off')

# Draw surface
ax.plot([0, 10], [1, 1], 'k-', linewidth=2)

# Object 1 (before)
ax.add_patch(patches.Rectangle((1, 1), 1.5, 1.5, fill=False, edgecolor='black', linewidth=2))
ax.text(1.75, 1.75, 'm1', fontsize=10, ha='center')

# Velocity arrow 1
ax.annotate('', xy=(3.5, 1.75), xytext=(2.6, 1.75),
            arrowprops=dict(arrowstyle='->', color='black', lw=2))
ax.text(3, 2.1, 'v1', fontsize=10, ha='center')

# Object 2 (before)
ax.add_patch(patches.Rectangle((5, 1), 1.5, 1.5, fill=False, edgecolor='black', linewidth=2))
ax.text(5.75, 1.75, 'm2', fontsize=10, ha='center')

# Velocity arrow 2
ax.annotate('', xy=(7.2, 1.75), xytext=(6.6, 1.75),
            arrowprops=dict(arrowstyle='->', color='black', lw=2))
ax.text(6.9, 2.1, 'v2', fontsize=10, ha='center')

plt.tight_layout()
plt.savefig('output.svg', format='svg')
"""


def execute_template(template: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """Execute a template and return (success, svg, error)."""
    working_dir = tempfile.mkdtemp()
    code_path = os.path.join(working_dir, 'generate_svg.py')
    output_svg = os.path.join(working_dir, 'output.svg')
    
    # Update template to save to correct path
    template = template.replace("plt.savefig('output.svg'", f"plt.savefig('{output_svg}'")
    
    with open(code_path, 'w') as f:
        f.write(template)
    
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
            return False, None, f"Execution error: {result.stderr[:200]}"
        
        if not os.path.exists(output_svg):
            return False, None, f"SVG file not created. Stdout: {result.stdout[:100]}"
        
        with open(output_svg, 'r') as f:
            svg = f.read()
        
        return True, svg, None
        
    except subprocess.TimeoutExpired:
        return False, None, "Template execution timed out"
    except Exception as e:
        return False, None, str(e)
    finally:
        import shutil
        shutil.rmtree(working_dir, ignore_errors=True)


def generate_pendulum_svg() -> Optional[str]:
    """Generate a simple pendulum SVG."""
    success, svg, _ = execute_template(PENDULUM_TEMPLATE)
    return svg if success else None


def generate_inclined_plane_svg() -> Optional[str]:
    """Generate an inclined plane SVG."""
    success, svg, _ = execute_template(INCLINED_PLANE_TEMPLATE)
    return svg if success else None


def generate_pulley_svg() -> Optional[str]:
    """Generate a pulley system SVG."""
    success, svg, _ = execute_template(PENDULUM_TEMPLATE)
    return svg if success else None


if __name__ == "__main__":
    print("Testing mechanics templates...")
    
    templates = [
        ("Pendulum", PENDULUM_TEMPLATE),
        ("Inclined Plane", INCLINED_PLANE_TEMPLATE),
        ("Pulley", PULLEY_TEMPLATE),
        ("Collision", COLLISION_TEMPLATE),
    ]
    
    for name, template in templates:
        success, svg, error = execute_template(template)
        if success:
            print(f"✓ {name}: {len(svg)} bytes")
        else:
            print(f"✗ {name}: {error[:50]}")
