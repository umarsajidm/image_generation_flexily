"""
Atom Generator
Generates atomic diagrams for chemistry/physics MCQs.
Handles:
- Periodic trend graphs (melting point, ionization energy, atomic radius)
- Bohr atomic models (electron shells)
- Nuclear decay diagrams
"""
import re
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from typing import Optional, List, Tuple
from dataclasses import dataclass
from pathlib import Path


@dataclass
class AtomGenResult:
    success: bool
    svg: Optional[str]
    diagram_subtype: str
    error: Optional[str] = None


PERIOD3_ELEMENTS = ['Na', 'Mg', 'Al', 'Si', 'P', 'S', 'Cl', 'Ar']
PERIOD3_MELTING_POINTS = [371, 923, 933, 1687, 317, 388, 172, 84]  # Kelvin
PERIOD3_ATOMIC_RADII = [186, 160, 143, 117, 110, 104, 99, 71]  # pm
PERIOD3_IONIZATION_ENERGY = [496, 738, 578, 787, 1012, 1000, 1251, 1521]  # kJ/mol
PERIOD3_ELECTRONEGATIVITY = [0.93, 1.31, 1.61, 1.90, 2.19, 2.58, 3.16, 3.0]

PERIOD2_ELEMENTS = ['Li', 'Be', 'B', 'C', 'N', 'O', 'F', 'Ne']
PERIOD2_MELTING_POINTS = [454, 1560, 2349, 3823, 63, 54, 53, 25]  # Kelvin


def classify_atom_question(question: str) -> str:
    """Classify the type of atom diagram needed."""
    q_lower = question.lower()
    
    if any(kw in q_lower for kw in ['melting point', 'melting', 'boiling point']):
        return 'periodic_melting_point'
    elif any(kw in q_lower for kw in ['ionization energy', 'ionisation', 'ionization']):
        return 'periodic_ionization'
    elif any(kw in q_lower for kw in ['atomic radius', 'radius', 'size']):
        return 'periodic_radius'
    elif any(kw in q_lower for kw in ['electronegativity', 'electroneg']):
        return 'periodic_electronegativity'
    elif any(kw in q_lower for kw in ['physical property', 'property along']):
        return 'periodic_property'
    elif any(kw in q_lower for kw in ['bohr', 'electron orbit', 'atomic model']):
        return 'bohr_model'
    elif any(kw in q_lower for kw in ['decay', 'alpha', 'beta', 'nuclear reaction']):
        return 'nuclear_decay'
    elif any(kw in q_lower for kw in ['orbital', 'p-orbital', 's-orbital', 'd-orbital']):
        return 'orbital_shape'
    elif any(kw in q_lower for kw in ['benzenonium', 'carbocation', 'hybridization']):
        return 'organic_structure'
    elif any(kw in q_lower for kw in ['electronic configuration', 'electron configuration']):
        return 'electron_config'
    else:
        return 'generic_atom'


def extract_period(question: str) -> int:
    """Extract which period is being discussed."""
    if 'period 3' in question.lower() or '3rd period' in question.lower():
        return 3
    elif 'period 2' in question.lower() or '2nd period' in question.lower():
        return 2
    return 3  # Default


def generate_periodic_trend_svg(
    period: int = 3,
    property_type: str = 'melting_point',
    title: Optional[str] = None
) -> Optional[str]:
    """Generate a periodic trend graph."""
    
    if period == 3:
        elements = PERIOD3_ELEMENTS
        if property_type == 'melting_point':
            values = PERIOD3_MELTING_POINTS
            ylabel = 'Melting Point (K)'
            default_title = 'Melting Points of Period 3 Elements'
        elif property_type == 'atomic_radius':
            values = PERIOD3_ATOMIC_RADII
            ylabel = 'Atomic Radius (pm)'
            default_title = 'Atomic Radius of Period 3 Elements'
        elif property_type == 'ionization_energy':
            values = PERIOD3_IONIZATION_ENERGY
            ylabel = 'Ionization Energy (kJ/mol)'
            default_title = 'Ionization Energy of Period 3 Elements'
        elif property_type == 'electronegativity':
            values = PERIOD3_ELECTRONEGATIVITY
            ylabel = 'Electronegativity'
            default_title = 'Electronegativity of Period 3 Elements'
        else:
            values = PERIOD3_MELTING_POINTS
            ylabel = 'Property Value'
            default_title = 'Physical Properties of Period 3 Elements'
    else:
        elements = PERIOD2_ELEMENTS
        values = PERIOD2_MELTING_POINTS
        ylabel = 'Melting Point (K)'
        default_title = 'Melting Points of Period 2 Elements'
    
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.set_facecolor('white')
    
    x = range(len(elements))
    bars = ax.bar(x, values, color='white', edgecolor='black', linewidth=2)
    
    ax.set_xlabel('Element', fontsize=14, fontfamily='serif')
    ax.set_ylabel(ylabel, fontsize=14, fontfamily='serif')
    ax.set_title(title or default_title, fontsize=16, fontfamily='serif', fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(elements, fontsize=12, fontfamily='serif')
    
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_linewidth(1.5)
    ax.spines['bottom'].set_linewidth(1.5)
    ax.tick_params(axis='both', which='major', labelsize=12)
    ax.grid(axis='y', linestyle='--', alpha=0.3)
    
    for i, (elem, val) in enumerate(zip(elements, values)):
        ax.annotate(f'{val}', (i, val), textcoords="offset points", 
                   xytext=(0, 5), ha='center', fontsize=9, fontfamily='serif')
    
    plt.tight_layout()
    
    svg_path = '/tmp/atom_trend.svg'
    plt.savefig(svg_path, format='svg', bbox_inches='tight', facecolor='white')
    plt.close()
    
    with open(svg_path, 'r') as f:
        svg = f.read()
    
    svg = re.sub(r'<\?xml[^>]*\?>', '', svg)
    svg = re.sub(r'<!DOCTYPE[^>]*>', '', svg)
    
    return svg.strip()


def generate_bohr_model_svg(element: str = 'Na', electrons: Optional[List[int]] = None) -> Optional[str]:
    """Generate a Bohr atomic model diagram."""
    
    element_electrons = {
        'H': [1], 'He': [2],
        'Li': [2, 1], 'Be': [2, 2], 'B': [2, 3], 'C': [2, 4], 'N': [2, 5], 'O': [2, 6], 'F': [2, 7], 'Ne': [2, 8],
        'Na': [2, 8, 1], 'Mg': [2, 8, 2], 'Al': [2, 8, 3], 'Si': [2, 8, 4], 
        'P': [2, 8, 5], 'S': [2, 8, 6], 'Cl': [2, 8, 7], 'Ar': [2, 8, 8],
    }
    
    if electrons is None:
        electrons = element_electrons.get(element, [2, 8, 1])
    
    fig, ax = plt.subplots(figsize=(8, 8))
    ax.set_xlim(-5, 5)
    ax.set_ylim(-5, 5)
    ax.set_aspect('equal')
    ax.axis('off')
    
    ax.add_patch(plt.Circle((0, 0), 0.3, color='gray', zorder=5))
    ax.text(0, 0, element, ha='center', va='center', fontsize=14, fontfamily='serif', fontweight='bold', zorder=6)
    
    shell_radii = [1.2, 2.2, 3.2, 4.2]
    for i, radius in enumerate(shell_radii[:len(electrons)]):
        circle = plt.Circle((0, 0), radius, fill=False, edgecolor='black', linewidth=1.5)
        ax.add_patch(circle)
        
        n_electrons = electrons[i]
        angles = np.linspace(0, 2*np.pi, n_electrons, endpoint=False)
        
        for angle in angles:
            x = radius * np.cos(angle)
            y = radius * np.sin(angle)
            ax.add_patch(plt.Circle((x, y), 0.15, color='black', zorder=4))
            ax.text(x, y, 'e⁻', ha='center', va='center', fontsize=8, 
                   color='white', fontfamily='serif', zorder=5)
    
    ax.set_title(f'Bohr Model of {element}', fontsize=16, fontfamily='serif', fontweight='bold')
    
    plt.tight_layout()
    
    svg_path = '/tmp/bohr_model.svg'
    plt.savefig(svg_path, format='svg', bbox_inches='tight', facecolor='white')
    plt.close()
    
    with open(svg_path, 'r') as f:
        svg = f.read()
    
    svg = re.sub(r'<\?xml[^>]*\?>', '', svg)
    svg = re.sub(r'<!DOCTYPE[^>]*>', '', svg)
    
    return svg.strip()


def generate_nuclear_decay_svg(
    parent: str = 'W',
    decay_chain: List[Tuple[str, str]] = None
) -> Optional[str]:
    """Generate a nuclear decay chain diagram."""
    
    if decay_chain is None:
        decay_chain = [('W', 'β'), ('X', 'α'), ('Y', 'β'), ('Z', None)]
    
    fig, ax = plt.subplots(figsize=(12, 4))
    ax.set_xlim(-0.5, len(decay_chain) + 0.5)
    ax.set_ylim(-1, 1)
    ax.axis('off')
    
    for i, (nuclide, decay_type) in enumerate(decay_chain):
        x = i * 1.5
        
        rect = plt.Rectangle((x - 0.4, -0.3), 0.8, 0.6, fill=False, 
                             edgecolor='black', linewidth=2)
        ax.add_patch(rect)
        ax.text(x, 0, nuclide, ha='center', va='center', 
               fontsize=16, fontfamily='serif', fontweight='bold')
        
        if decay_type and i < len(decay_chain) - 1:
            ax.annotate('', xy=(x + 1.0, 0), xytext=(x + 0.5, 0),
                       arrowprops=dict(arrowstyle='->', color='black', lw=2))
            ax.text(x + 0.75, 0.2, decay_type, ha='center', va='bottom',
                   fontsize=12, fontfamily='serif', style='italic')
    
    ax.set_title('Nuclear Decay Chain', fontsize=16, fontfamily='serif', fontweight='bold')
    
    plt.tight_layout()
    
    svg_path = '/tmp/nuclear_decay.svg'
    plt.savefig(svg_path, format='svg', bbox_inches='tight', facecolor='white')
    plt.close()
    
    with open(svg_path, 'r') as f:
        svg = f.read()
    
    svg = re.sub(r'<\?xml[^>]*\?>', '', svg)
    svg = re.sub(r'<!DOCTYPE[^>]*>', '', svg)
    
    return svg.strip()


def generate_orbital_shape_svg(orbital_type: str = 'p') -> Optional[str]:
    """Generate orbital shape diagram (s, p, d orbitals)."""
    
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.set_xlim(-3, 3)
    ax.set_ylim(-2.5, 2.5)
    ax.set_aspect('equal')
    ax.axis('off')
    
    if orbital_type == 's':
        circle = plt.Circle((0, 0), 1.5, fill=True, facecolor='lightgray', 
                           edgecolor='black', linewidth=2)
        ax.add_patch(circle)
        ax.text(0, 0, 's orbital', ha='center', va='center', 
               fontsize=14, fontfamily='serif')
        ax.text(0, -2.2, 'Spherical shape', ha='center', fontsize=12, 
               fontfamily='serif', style='italic')
        
    elif orbital_type == 'p':
        for dx, label in [(-1.2, '-'), (1.2, '+')]:
            ellipse = plt.Circle((dx, 0), 0.8, fill=True, 
                                facecolor='lightgray' if label == '-' else 'gray',
                                edgecolor='black', linewidth=2)
            ax.add_patch(ellipse)
        ax.plot([0, 0], [-1.5, 1.5], 'k-', linewidth=1.5)
        ax.text(-1.2, 0, '-', ha='center', va='center', fontsize=14, fontfamily='serif')
        ax.text(1.2, 0, '+', ha='center', va='center', fontsize=14, fontfamily='serif')
        ax.text(0, 2.2, 'p orbital', ha='center', fontsize=14, 
               fontfamily='serif', fontweight='bold')
        ax.text(0, -2.2, 'Dumbbell shape', ha='center', fontsize=12, 
               fontfamily='serif', style='italic')
    
    ax.set_title('Orbital Shape', fontsize=16, fontfamily='serif', fontweight='bold')
    
    plt.tight_layout()
    
    svg_path = '/tmp/orbital.svg'
    plt.savefig(svg_path, format='svg', bbox_inches='tight', facecolor='white')
    plt.close()
    
    with open(svg_path, 'r') as f:
        svg = f.read()
    
    svg = re.sub(r'<\?xml[^>]*\?>', '', svg)
    svg = re.sub(r'<!DOCTYPE[^>]*>', '', svg)
    
    return svg.strip()


class AtomGenerator:
    def __init__(self):
        pass
    
    def generate(self, question: str, subject: str = 'chemistry') -> AtomGenResult:
        """Generate atomic diagram from question text."""
        
        subtype = classify_atom_question(question)
        period = extract_period(question)
        
        if subtype == 'periodic_melting_point':
            svg = generate_periodic_trend_svg(period, 'melting_point')
        elif subtype == 'periodic_ionization':
            svg = generate_periodic_trend_svg(period, 'ionization_energy')
        elif subtype == 'periodic_radius':
            svg = generate_periodic_trend_svg(period, 'atomic_radius')
        elif subtype == 'periodic_electronegativity':
            svg = generate_periodic_trend_svg(period, 'electronegativity')
        elif subtype == 'periodic_property':
            q_lower = question.lower()
            if 'decreases from na' in q_lower:
                svg = generate_periodic_trend_svg(period, 'ionization_energy')
            else:
                svg = generate_periodic_trend_svg(period, 'melting_point')
        elif subtype == 'bohr_model':
            svg = generate_bohr_model_svg('Na')
        elif subtype == 'nuclear_decay':
            svg = generate_nuclear_decay_svg()
        elif subtype == 'orbital_shape':
            svg = generate_orbital_shape_svg('p')
        else:
            return AtomGenResult(
                success=False,
                svg=None,
                diagram_subtype=subtype,
                error=f'Unsupported atom diagram type: {subtype}'
            )
        
        if svg:
            return AtomGenResult(
                success=True,
                svg=svg,
                diagram_subtype=subtype,
                error=None
            )
        else:
            return AtomGenResult(
                success=False,
                svg=None,
                diagram_subtype=subtype,
                error='Failed to generate SVG'
            )


if __name__ == "__main__":
    test_questions = [
        "The trends in melting points of the elements of the 3rd period are depicted in the figure below.",
        "A graph shows a physical property along the period 3 elements. Which physical property is represented?",
        "Which of the following correctly represents the shape of a p-orbital?",
        "W decays to X by beta emission, then X decays to Y by alpha emission.",
    ]
    
    gen = AtomGenerator()
    
    for q in test_questions:
        print(f"\nQ: {q[:60]}...")
        result = gen.generate(q)
        
        if result.success:
            print(f"  ✓ Type: {result.diagram_subtype}")
            print(f"    SVG length: {len(result.svg)} chars")
        else:
            print(f"  ✗ Error: {result.error}")
