"""Few-shot code examples for mechanics diagram generation."""

from src.utils.mechanics_router import MechanicsSubtype


PENDULUM_CODE_EXAMPLE = '''
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

fig, ax = plt.subplots(figsize=(8, 8))
ax.set_aspect('equal')
ax.axis('off')

pivot_x, pivot_y = 5, 8
length = 4
angle = 30
angle_rad = np.radians(angle)

bob_x = pivot_x + length * np.sin(angle_rad)
bob_y = pivot_y - length * np.cos(angle_rad)

ax.plot([pivot_x, bob_x], [pivot_y, bob_y], 'k-', linewidth=2)

pivot_circle = patches.Circle((pivot_x, pivot_y), 0.15, fill=True, facecolor='black')
ax.add_patch(pivot_circle)

bob_circle = patches.Circle((bob_x, bob_y), 0.4, fill=False, edgecolor='black', linewidth=2)
ax.add_patch(bob_circle)

equilibrium_x = pivot_x
equilibrium_y = pivot_y - length
ax.plot([pivot_x, equilibrium_x], [pivot_y, equilibrium_y], 'k--', linewidth=1, alpha=0.5)

arc = patches.Arc((pivot_x, pivot_y), 1.5, 1.5, angle=-90, theta1=0, theta2=angle, linewidth=1.5)
ax.add_patch(arc)
ax.text(pivot_x + 1.0, pivot_y - 0.8, 'θ', fontsize=14, ha='center')

ax.text(bob_x + 0.3, bob_y, 'X', fontsize=14, fontweight='bold')
ax.text(equilibrium_x + 0.3, equilibrium_y, 'Y', fontsize=14, fontweight='bold')

ax.annotate('', xy=(bob_x, bob_y - 1.2), xytext=(bob_x, bob_y - 0.4),
            arrowprops=dict(arrowstyle='->', color='black', lw=2))
ax.text(bob_x + 0.5, bob_y - 0.8, 'mg', fontsize=12)

ax.set_xlim(0, 10)
ax.set_ylim(0, 10)
plt.tight_layout()
plt.savefig('output.svg')
'''

INCLINED_PLANE_CODE_EXAMPLE = '''
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

fig, ax = plt.subplots(figsize=(10, 6))
ax.set_aspect('equal')
ax.axis('off')

wedge = patches.Polygon([[1, 1], [8, 1], [8, 5]], closed=True, fill=False, edgecolor='black', linewidth=2)
ax.add_patch(wedge)

block_width, block_height = 1.5, 1.0
angle = 30
angle_rad = np.radians(angle)

block_center_x = 4.5
block_center_y = 1 + (block_center_x - 1) * np.tan(angle_rad) + block_height/2 * np.cos(angle_rad)

block = patches.Rectangle((block_center_x - block_width/2, block_center_y - block_height/2),
                           block_width, block_height, angle=angle,
                           fill=False, edgecolor='black', linewidth=2)
ax.add_patch(block)

ax.annotate('', xy=(3, 1.0), xytext=(3, 0.3),
            arrowprops=dict(arrowstyle='->', color='black', lw=1.5))
ax.text(3, 0.15, 'θ', fontsize=14, ha='center')

ax.annotate('', xy=(block_center_x - 0.8, block_center_y - 1.5), xytext=(block_center_x, block_center_y),
            arrowprops=dict(arrowstyle='->', color='black', lw=2))
ax.text(block_center_x - 1.2, block_center_y - 1.0, 'mg', fontsize=12)

ax.annotate('', xy=(block_center_x + 1.2, block_center_y + 0.7), xytext=(block_center_x, block_center_y),
            arrowprops=dict(arrowstyle='->', color='black', lw=2))
ax.text(block_center_x + 1.4, block_center_y + 0.9, 'N', fontsize=12)

ax.set_xlim(0, 10)
ax.set_ylim(0, 7)
plt.tight_layout()
plt.savefig('output.svg')
'''

PULLEY_CODE_EXAMPLE = '''
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

fig, ax = plt.subplots(figsize=(8, 8))
ax.set_aspect('equal')
ax.axis('off')

pulley_x, pulley_y = 5, 7
pulley_radius = 0.5

pulley = patches.Circle((pulley_x, pulley_y), pulley_radius, fill=False, edgecolor='black', linewidth=2)
ax.add_patch(pulley)
ax.plot([pulley_x, pulley_x], [pulley_y, pulley_y + 0.5], 'k-', linewidth=2)

mass1_x, mass1_y = 3, 4
mass1 = patches.Rectangle((mass1_x - 0.5, mass1_y - 0.5), 1, 1, fill=False, edgecolor='black', linewidth=2)
ax.add_patch(mass1)
ax.text(mass1_x, mass1_y, 'm₁', fontsize=12, ha='center', va='center')

mass2_x, mass2_y = 7, 3
mass2 = patches.Rectangle((mass2_x - 0.5, mass2_y - 0.5), 1, 1, fill=False, edgecolor='black', linewidth=2)
ax.add_patch(mass2)
ax.text(mass2_x, mass2_y, 'm₂', fontsize=12, ha='center', va='center')

ax.plot([mass1_x, pulley_x - pulley_radius], [mass1_y + 0.5, pulley_y], 'k-', linewidth=1.5)
ax.plot([pulley_x + pulley_radius, mass2_x], [pulley_y, mass2_y + 0.5], 'k-', linewidth=1.5)

ax.annotate('', xy=(mass1_x, mass1_y + 1.8), xytext=(mass1_x, mass1_y + 0.5),
            arrowprops=dict(arrowstyle='->', color='black', lw=2))
ax.text(mass1_x - 0.4, mass1_y + 1.2, 'T', fontsize=12)

ax.annotate('', xy=(mass2_x, mass2_y + 1.8), xytext=(mass2_x, mass2_y + 0.5),
            arrowprops=dict(arrowstyle='->', color='black', lw=2))
ax.text(mass2_x + 0.4, mass2_y + 1.2, 'T', fontsize=12)

ax.set_xlim(0, 10)
ax.set_ylim(0, 10)
plt.tight_layout()
plt.savefig('output.svg')
'''

COLLISION_CODE_EXAMPLE = '''
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

fig, ax = plt.subplots(figsize=(10, 5))
ax.set_aspect('equal')
ax.axis('off')

ax.plot([1, 9], [2, 2], 'k-', linewidth=1)

mass1_x, mass1_y = 3, 2.5
mass1 = patches.Circle((mass1_x, mass1_y), 0.6, fill=False, edgecolor='black', linewidth=2)
ax.add_patch(mass1)
ax.text(mass1_x, mass1_y, 'm₁', fontsize=12, ha='center', va='center')

mass2_x, mass2_y = 7, 2.5
mass2 = patches.Circle((mass2_x, mass2_y), 0.8, fill=False, edgecolor='black', linewidth=2)
ax.add_patch(mass2)
ax.text(mass2_x, mass2_y, 'm₂', fontsize=12, ha='center', va='center')

ax.annotate('', xy=(mass1_x + 1.5, mass1_y), xytext=(mass1_x + 0.7, mass1_y),
            arrowprops=dict(arrowstyle='->', color='black', lw=2))
ax.text(mass1_x + 1.1, mass1_y + 0.5, 'v₁', fontsize=12)

ax.annotate('', xy=(mass2_x - 1.5, mass2_y), xytext=(mass2_x - 0.9, mass2_y),
            arrowprops=dict(arrowstyle='->', color='black', lw=2))
ax.text(mass2_x - 1.2, mass2_y + 0.5, 'v₂', fontsize=12)

ax.text(5, 4, 'Before Collision', fontsize=14, ha='center', fontweight='bold')

ax.set_xlim(0, 10)
ax.set_ylim(0, 6)
plt.tight_layout()
plt.savefig('output.svg')
'''

PROJECTILE_CODE_EXAMPLE = '''
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

fig, ax = plt.subplots(figsize=(10, 6))
ax.set_aspect('equal')
ax.axis('off')

ax.plot([0.5, 9.5], [1, 1], 'k-', linewidth=2)
ax.plot([0.5, 0.5], [1, 1.3], 'k-', linewidth=2)

t = np.linspace(0, 2, 100)
v0 = 10
angle = 45
angle_rad = np.radians(angle)
g = 9.8

x = v0 * np.cos(angle_rad) * t
y = v0 * np.sin(angle_rad) * t - 0.5 * g * t**2
y = y + 1
x = x / 2 + 1

ax.plot(x, y, 'k-', linewidth=2)

launch_x, launch_y = 1, 1
ax.annotate('', xy=(launch_x + 1.5*np.cos(angle_rad), launch_y + 1.5*np.sin(angle_rad)),
            xytext=(launch_x, launch_y),
            arrowprops=dict(arrowstyle='->', color='black', lw=2))
ax.text(launch_x + 0.8, launch_y + 1.0, 'v₀', fontsize=12)

ax.annotate('', xy=(launch_x + 1.2, launch_y), xytext=(launch_x + 0.8*np.cos(angle_rad), launch_y + 0.8*np.sin(angle_rad)),
            arrowprops=dict(arrowstyle='->', color='gray', lw=1, linestyle='--'))
arc = patches.Arc((launch_x, launch_y), 1.2, 1.2, angle=0, theta1=0, theta2=angle, linewidth=1.5)
ax.add_patch(arc)
ax.text(launch_x + 0.8, launch_y + 0.4, 'θ', fontsize=14)

max_height_idx = np.argmax(y)
ax.plot([x[max_height_idx]], [y[max_height_idx]], 'ko', markersize=6)
ax.text(x[max_height_idx], y[max_height_idx] + 0.5, 'Max Height', fontsize=10, ha='center')

ax.plot([launch_x, x[-1]], [1, 1], 'k--', linewidth=1)
ax.text((launch_x + x[-1])/2, 0.6, 'Range (R)', fontsize=12, ha='center')

ax.set_xlim(0, 10)
ax.set_ylim(0, 7)
plt.tight_layout()
plt.savefig('output.svg')
'''

SPRING_CODE_EXAMPLE = '''
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

fig, ax = plt.subplots(figsize=(10, 5))
ax.set_aspect('equal')
ax.axis('off')

wall_x = 2
ax.plot([wall_x, wall_x], [2, 4], 'k-', linewidth=3)

spring_start = wall_x
spring_end = 5
num_coils = 8
coil_width = 0.3
spring_length = spring_end - spring_start

spring_x = [spring_start]
spring_y = [3]

for i in range(num_coils):
    progress = (i + 0.5) / num_coils
    x = spring_start + progress * spring_length
    spring_x.append(x)
    spring_y.append(3 + coil_width * (1 if i % 2 == 0 else -1))

spring_x.append(spring_end)
spring_y.append(3)

ax.plot(spring_x, spring_y, 'k-', linewidth=2)

mass_x = spring_end
mass = patches.Rectangle((mass_x, 2.5), 1.5, 1, fill=False, edgecolor='black', linewidth=2)
ax.add_patch(mass)
ax.text(mass_x + 0.75, 3, 'm', fontsize=14, ha='center', va='center')

eq_x = mass_x + 2
ax.plot([mass_x + 1.5, eq_x + 1], [3, 3], 'k--', linewidth=1, alpha=0.5)
ax.text(eq_x, 2.3, 'x=0', fontsize=10, ha='center')

ax.annotate('', xy=(mass_x + 2.5, 3), xytext=(mass_x + 1.5, 3),
            arrowprops=dict(arrowstyle='<->', color='black', lw=1.5))
ax.text(mass_x + 2.0, 3.5, 'x', fontsize=12, ha='center')

ax.text(3.5, 4.5, 'k', fontsize=14, ha='center')

ax.set_xlim(0, 10)
ax.set_ylim(0, 6)
plt.tight_layout()
plt.savefig('output.svg')
'''

TORQUE_CODE_EXAMPLE = '''
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

fig, ax = plt.subplots(figsize=(10, 6))
ax.set_aspect('equal')
ax.axis('off')

beam_start_x, beam_start_y = 2, 3
beam_length = 6
beam_height = 0.3

beam = patches.Rectangle((beam_start_x, beam_start_y - beam_height/2),
                          beam_length, beam_height, fill=False, edgecolor='black', linewidth=2)
ax.add_patch(beam)

pivot_x = beam_start_x + beam_length/2
pivot_y = beam_start_y

pivot = patches.Triangle((pivot_x, pivot_y - 1), (pivot_x - 0.4, pivot_y - 1.5), (pivot_x + 0.4, pivot_y - 1.5),
                          fill=True, facecolor='black')
ax.add_patch(pivot)
ax.plot([pivot_x, pivot_x], [pivot_y - 1, pivot_y], 'k-', linewidth=2)

force1_x = beam_start_x + 1.5
ax.annotate('', xy=(force1_x, beam_start_y + 1.5), xytext=(force1_x, beam_start_y + 0.2),
            arrowprops=dict(arrowstyle='->', color='black', lw=2))
ax.text(force1_x - 0.3, beam_start_y + 1.0, 'F₁', fontsize=12)

force2_x = beam_start_x + 4.5
ax.annotate('', xy=(force2_x, beam_start_y - 1.5), xytext=(force2_x, beam_start_y - 0.2),
            arrowprops=dict(arrowstyle='->', color='black', lw=2))
ax.text(force2_x + 0.3, beam_start_y - 1.0, 'F₂', fontsize=12)

ax.annotate('', xy=(force1_x, beam_start_y), xytext=(pivot_x, beam_start_y),
            arrowprops=dict(arrowstyle='<->', color='gray', lw=1))
ax.text((force1_x + pivot_x)/2, beam_start_y + 0.5, 'r₁', fontsize=10, ha='center', color='gray')

ax.annotate('', xy=(force2_x, beam_start_y), xytext=(pivot_x, beam_start_y),
            arrowprops=dict(arrowstyle='<->', color='gray', lw=1))
ax.text((force2_x + pivot_x)/2, beam_start_y - 0.5, 'r₂', fontsize=10, ha='center', color='gray')

arc = patches.Arc((pivot_x, pivot_y), 1.5, 1.5, angle=0, theta1=0, theta2=60, linewidth=2)
ax.add_patch(arc)
ax.annotate('', xy=(pivot_x + 1.0, pivot_y + 0.8), xytext=(pivot_x + 1.2, pivot_y + 0.5),
            arrowprops=dict(arrowstyle='->', color='black', lw=1.5))
ax.text(pivot_x + 1.0, pivot_y + 1.2, 'τ', fontsize=12)

ax.set_xlim(0, 10)
ax.set_ylim(0, 7)
plt.tight_layout()
plt.savefig('output.svg')
'''

GENERIC_MECHANICS_CODE_EXAMPLE = '''
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

fig, ax = plt.subplots(figsize=(8, 6))
ax.set_aspect('equal')
ax.axis('off')

ax.plot([1, 9], [2, 2], 'k-', linewidth=2)

block_x, block_y = 5, 2.5
block = patches.Rectangle((block_x - 1, block_y - 0.5), 2, 1, fill=False, edgecolor='black', linewidth=2)
ax.add_patch(block)
ax.text(block_x, block_y, 'm', fontsize=14, ha='center', va='center')

ax.annotate('', xy=(block_x + 2, block_y), xytext=(block_x + 1, block_y),
            arrowprops=dict(arrowstyle='->', color='black', lw=2))
ax.text(block_x + 2.3, block_y + 0.3, 'F', fontsize=12)

ax.annotate('', xy=(block_x, block_y - 1.5), xytext=(block_x, block_y - 0.5),
            arrowprops=dict(arrowstyle='->', color='black', lw=2))
ax.text(block_x - 0.5, block_y - 1.0, 'mg', fontsize=12)

ax.annotate('', xy=(block_x, block_y + 1.0), xytext=(block_x, block_y + 0.5),
            arrowprops=dict(arrowstyle='->', color='black', lw=2))
ax.text(block_x + 0.3, block_y + 0.8, 'N', fontsize=12)

ax.annotate('', xy=(block_x - 2, block_y), xytext=(block_x - 1, block_y),
            arrowprops=dict(arrowstyle='->', color='black', lw=2))
ax.text(block_x - 1.5, block_y + 0.3, 'f', fontsize=12)

point_a = patches.Circle((block_x - 0.7, block_y), 0.1, fill=True, facecolor='black')
ax.add_patch(point_a)
ax.text(block_x - 0.7, block_y - 0.5, 'A', fontsize=12, ha='center')

ax.set_xlim(0, 10)
ax.set_ylim(0, 7)
plt.tight_layout()
plt.savefig('output.svg')
'''

OPTICS_CODE_EXAMPLE = '''
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

fig, ax = plt.subplots(figsize=(12, 6))
ax.set_aspect('equal')
ax.axis('off')

lens_x = 6
lens_height = 3
ax.plot([lens_x, lens_x], [-lens_height/2, lens_height/2], 'k-', linewidth=3)

ax.axhline(y=0, color='gray', linewidth=0.5, linestyle='--', xmin=0.05, xmax=0.95)

f = 2
ax.plot([lens_x - f], [0], 'ko', markersize=6)
ax.plot([lens_x + f], [0], 'ko', markersize=6)
ax.text(lens_x - f, -0.4, 'F', fontsize=12, ha='center')
ax.text(lens_x + f, -0.4, "F'", fontsize=12, ha='center')

obj_x = 2.5
obj_height = 1.5
ax.annotate('', xy=(obj_x, obj_height), xytext=(obj_x, 0),
            arrowprops=dict(arrowstyle='->', color='black', lw=2))
ax.text(obj_x, obj_height + 0.3, 'Object', fontsize=10, ha='center')

ax.plot([obj_x, lens_x], [obj_height, obj_height], 'b-', linewidth=1.5)
ax.plot([lens_x, lens_x + f + 3], [obj_height, obj_height - (obj_height/f)*(f+3)], 'b-', linewidth=1.5)

ax.plot([obj_x, lens_x], [obj_height, 0], 'r-', linewidth=1.5)
ax.plot([lens_x, lens_x + f + 3], [0, 0], 'r-', linewidth=1.5)

ax.plot([obj_x, lens_x], [obj_height, obj_height], 'g-', linewidth=1.5)

ax.set_xlim(0, 12)
ax.set_ylim(-3, 4)
plt.tight_layout()
plt.savefig('output.svg')
'''


SUBTYPE_CODE_EXAMPLES = {
    MechanicsSubtype.PENDULUM: PENDULUM_CODE_EXAMPLE,
    MechanicsSubtype.INCLINED_PLANE: INCLINED_PLANE_CODE_EXAMPLE,
    MechanicsSubtype.PULLEY: PULLEY_CODE_EXAMPLE,
    MechanicsSubtype.COLLISION: COLLISION_CODE_EXAMPLE,
    MechanicsSubtype.PROJECTILE: PROJECTILE_CODE_EXAMPLE,
    MechanicsSubtype.SPRING: SPRING_CODE_EXAMPLE,
    MechanicsSubtype.TORQUE: TORQUE_CODE_EXAMPLE,
    MechanicsSubtype.GENERIC: GENERIC_MECHANICS_CODE_EXAMPLE,
}


def get_mechanics_code_example(subtype: MechanicsSubtype) -> str:
    """Get the few-shot code example for a mechanics subtype."""
    return SUBTYPE_CODE_EXAMPLES.get(subtype, GENERIC_MECHANICS_CODE_EXAMPLE)


def get_optics_code_example() -> str:
    """Get the few-shot code example for optics diagrams."""
    return OPTICS_CODE_EXAMPLE


def build_mechanics_prompt(question: str, subtype: MechanicsSubtype) -> str:
    """Build a prompt for mechanics diagram generation with few-shot example."""
    code_example = get_mechanics_code_example(subtype)
    
    return f"""You are an expert physics diagram generator using matplotlib.

KEY RULES:
1. Always use ax.set_aspect('equal') to prevent distortion
2. Use ax.annotate() for vectors and arrows, NOT plt.arrow()
3. Label ALL points mentioned in the question (use uppercase letters like X, Y, A, B)
4. Use plt.tight_layout() before saving
5. Use serif fonts (Times New Roman style)
6. Draw force vectors with arrowstyle='->'
7. Mark angles with arcs using patches.Arc()
8. Use black lines only (no colors except grayscale)

SUBTYPE: {subtype.value.upper()}

EXAMPLE CODE FOR {subtype.value.upper()} DIAGRAMS:
{code_example}

Question: {question}

Output ONLY the Python code. No markdown formatting. No explanations. The code must:
- Start with: import matplotlib; matplotlib.use('Agg')
- End with: plt.savefig('output.svg')
- Be self-contained and executable"""


def build_optics_prompt(question: str) -> str:
    """Build a prompt for optics diagram generation with few-shot example."""
    code_example = get_optics_code_example()
    
    return f"""You are an expert optics diagram generator using matplotlib.

KEY RULES:
1. Always use ax.set_aspect('equal') to prevent distortion
2. Draw the principal axis as a horizontal dashed line
3. Mark focal points (F, F') with dots and labels
4. Draw lenses as thick vertical lines
5. Use different colors for different rays (black, blue, red, green)
6. Label object and image clearly
7. Use plt.tight_layout() before saving

OPTICS DIAGRAM EXAMPLE:
{code_example}

Question: {question}

Output ONLY the Python code. No markdown formatting. No explanations. The code must:
- Start with: import matplotlib; matplotlib.use('Agg')
- End with: plt.savefig('output.svg')
- Be self-contained and executable"""
