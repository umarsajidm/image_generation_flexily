"""
Chemistry Molecule Generator
Generates molecular diagrams for chemistry MCQs without SMILES strings.
Uses RDKit when possible, falls back to matplotlib structural formulas.
"""
import re
import os
import subprocess
import tempfile
from typing import Optional, Tuple, List
from dataclasses import dataclass
from pathlib import Path

try:
    from pubchempy import get_compounds
    HAS_PUBCHEMPY = True
except ImportError:
    HAS_PUBCHEMPY = False

try:
    from rdkit import Chem
    from rdkit.Chem import Draw
    from rdkit.Chem.Draw import rdMolDraw2D
    HAS_RDKIT = True
except ImportError:
    HAS_RDKIT = False


@dataclass
class MoleculeGenResult:
    success: bool
    svg: Optional[str]
    smiles: Optional[str]
    compound_name: Optional[str]
    method: str
    error: Optional[str]


LATEX_FORMULAS = {
    'ch4': 'C',
    'c2h6': 'CC',
    'c2h4': 'C=C',
    'c2h2': 'C#C',
    'ch3oh': 'CO',
    'c2h5oh': 'CCO',
    'h2so4': 'OS(=O)(=O)O',
    'hcl': 'Cl',
    'hno3': 'O=[N+]([O-])O',
    'naoh': '[Na+].[OH-]',
    'nacl': '[Na+].[Cl-]',
    'h2o': 'O',
    'co2': 'O=C=O',
    'co': '[C-]#[O+]',
    'nh3': 'N',
    'ch3cooh': 'CC(=O)O',
    'c6h6': 'c1ccccc1',
    'c6h5oh': 'Oc1ccccc1',
    'c6h5nh2': 'Nc1ccccc1',
    'ch3cho': 'CC=O',
    'hcho': 'C=O',
    'ch3coch3': 'CC(=O)C',
}

COMMON_COMPOUNDS = {
    'benzene': 'c1ccccc1',
    'toluene': 'Cc1ccccc1',
    'phenol': 'Oc1ccccc1',
    'aniline': 'Nc1ccccc1',
    'ethanol': 'CCO',
    'methanol': 'CO',
    'ethanoic acid': 'CC(=O)O',
    'acetic acid': 'CC(=O)O',
    'methanoic acid': 'C(=O)O',
    'formic acid': 'C(=O)O',
    'ethane': 'CC',
    'methane': 'C',
    'propane': 'CCC',
    'butane': 'CCCC',
    'ethene': 'C=C',
    'ethyne': 'C#C',
    'acetone': 'CC(=O)C',
    'propanone': 'CC(=O)C',
    'formaldehyde': 'C=O',
    'methanal': 'C=O',
    'ethanal': 'CC=O',
    'acetaldehyde': 'CC=O',
    'chloroform': 'ClC(Cl)Cl',
    'carbon tetrachloride': 'ClC(Cl)(Cl)Cl',
    'urea': 'NC(=O)N',
    'glycine': 'NCC(=O)O',
    'alanine': 'CC(N)C(=O)O',
    'glucose': 'OC[C@H]1OC(O)[C@H](O)[C@@H](O)[C@@H]1O',
    'fructose': 'OC[C@H]1O[C@@H](O)[C@H](O)[C@@H]1O',
    'sucrose': 'OC[C@H]1O[C@@H](O)[C@H](O)[C@@H]1OC[C@H]2O[C@@H](O)[C@H](O)[C@@H]2O',
    'pyridine': 'c1ccncc1',
    'naphthalene': 'c1ccc2ccccc2c1',
    'anthracene': 'c1ccc2ccccc2c1',
    'cyclohexane': 'C1CCCCC1',
    'cyclopentane': 'C1CCCC1',
    'cyclohexene': 'C1=CCCCC1',
    'styrene': 'C=Cc1ccccc1',
    'ethylbenzene': 'CCc1ccccc1',
    'xylene': 'Cc1c(C)cccc1',
    'paraxylene': 'Cc1ccc(C)cc1',
    'nitrobenzene': 'O=[N+]([O-])c1ccccc1',
    'benzoic acid': 'O=C(O)c1ccccc1',
    'benzaldehyde': 'O=Cc1ccccc1',
    'acetophenone': 'CC(=O)c1ccccc1',
}


def extract_compound_names(text: str) -> List[str]:
    """
    Extract potential compound names from question text.
    Returns list of candidate compound names.
    """
    text_lower = text.lower()
    
    compounds = []
    
    for name in COMMON_COMPOUNDS.keys():
        if name in text_lower:
            compounds.append(name)
    
    latex_clean = re.sub(r'\\text\{([^}]+)\}', r'\1', text_lower)
    latex_clean = re.sub(r'\$([^$]+)\$', r' \1 ', latex_clean)
    latex_clean = re.sub(r'[^a-z0-9]', ' ', latex_clean)
    
    for latex_key in LATEX_FORMULAS.keys():
        if latex_key in latex_clean:
            compounds.append(latex_key)
    
    FALSE_POSITIVES = {
        'functional', 'isomer', 'isomerism', 'isomers', 'structural',
        'identical', 'radical', 'chemical', 'cis-trans', 'trans-isomer',
        'general', 'natural', 'material', 'mineral', 'element',
        'proton', 'neutron', 'electron', 'nuclear', 'optical',
        'molar', 'mole', 'normal', 'molecular', 'thermal',
    }
    
    iupac_patterns = [
        r'\b(\d+-?methyl-?\w+)\b',
        r'\b(\d+-?ethyl-?\w+)\b',
        r'\b(tert-?but\w+)\b',
        r'\b(iso-?\w+)\b',
        r'\b(cis-?\w+)\b',
        r'\b(trans-?\w+)\b',
        r'\b(\w+ane)\b',
        r'\b(\w+ene)\b',
        r'\b(\w+yne)\b',
        r'\b(\w+ol)\b',
        r'\b(\w+al)\b',
        r'\b(\w+oic acid)\b',
        r'\b(\w+one)\b',
        r'\b(\w+amine)\b',
        r'\b(\w+oate)\b',
        r'\b(benz\w+)\b',
        r'\b(cyclo\w+)\b',
    ]
    
    for pattern in iupac_patterns:
        matches = re.findall(pattern, text_lower)
        for m in matches:
            if m not in FALSE_POSITIVES and len(m) > 4:
                compounds.append(m)
    
    seen = set()
    unique = []
    for c in compounds:
        if c not in seen and len(c) > 3:
            seen.add(c)
            unique.append(c)
    
    return unique


def get_smiles_from_name(compound_name: str) -> Optional[str]:
    """
    Convert compound name to SMILES string.
    Uses common compounds dict first, then pubchempy.
    """
    name_lower = compound_name.lower().strip()
    
    if name_lower in COMMON_COMPOUNDS:
        return COMMON_COMPOUNDS[name_lower]
    
    if name_lower in LATEX_FORMULAS:
        return LATEX_FORMULAS[name_lower]
    
    if HAS_PUBCHEMPY:
        try:
            results = get_compounds(compound_name, 'name')
            if results:
                return results[0].smiles
        except Exception:
            pass
    
    return None


def generate_rdkit_svg(smiles: str, size: Tuple[int, int] = (400, 300)) -> Optional[str]:
    """
    Generate SVG from SMILES using RDKit with textbook-quality rendering.
    """
    if not HAS_RDKIT:
        return None
    
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return None
        
        d2d = rdMolDraw2D.MolDraw2DSVG(size[0], size[1])
        
        opts = d2d.drawOptions()
        opts.clearBackground = False
        opts.bondLineWidth = 2.0
        opts.addStereoAnnotation = True
        
        d2d.DrawMolecule(mol)
        d2d.FinishDrawing()
        
        svg = d2d.GetDrawingText()
        
        svg = re.sub(r'<\?xml[^>]*\?>', '', svg)
        svg = re.sub(r'<!DOCTYPE[^>]*>', '', svg)
        
        return svg.strip()
        
    except Exception:
        return None


def generate_reaction_svg(smiles_list: List[str], size: Tuple[int, int] = (600, 300)) -> Optional[str]:
    """
    Generate SVG for reactions (multiple molecules side-by-side).
    Joins SMILES with "." for RDKit to render as separate molecules.
    """
    if not smiles_list or not HAS_RDKIT:
        return None
    
    combined_smiles = ".".join(smiles_list)
    return generate_rdkit_svg(combined_smiles, size)


STRUCTURAL_FORMULA_PROMPT = """You are an expert at drawing molecular structural formulas using matplotlib.

Generate Python code to draw the molecular structure described below. The code must:
1. Use matplotlib with Agg backend
2. Draw atoms as labeled circles (C, O, N, H, etc.)
3. Draw bonds as lines between atoms
4. Use black and white style
5. Save to 'output.svg'

Compound: {compound_name}

Output ONLY the Python code. Use this template:

```python
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

fig, ax = plt.subplots(figsize=(8, 6))
ax.set_xlim(0, 10)
ax.set_ylim(0, 8)
ax.set_aspect('equal')
ax.axis('off')

def draw_atom(x, y, label, radius=0.3):
    circle = patches.Circle((x, y), radius, fill=False, edgecolor='black', linewidth=2)
    ax.add_patch(circle)
    ax.text(x, y, label, ha='center', va='center', fontsize=12, fontfamily='serif')

def draw_bond(x1, y1, x2, y2, bond_type='single'):
    if bond_type == 'double':
        ax.plot([x1, x2], [y1+0.1, y2+0.1], 'k-', linewidth=2)
        ax.plot([x1, x2], [y1-0.1, y2-0.1], 'k-', linewidth=2)
    elif bond_type == 'triple':
        ax.plot([x1, x2], [y1, y2], 'k-', linewidth=2)
        ax.plot([x1, x2], [y1+0.15, y2+0.15], 'k-', linewidth=2)
        ax.plot([x1, x2], [y1-0.15, y2-0.15], 'k-', linewidth=2)
    else:
        ax.plot([x1, x2], [y1, y2], 'k-', linewidth=2)

# Draw your molecule here
# Example: draw_atom(5, 5, 'C')
#          draw_bond(5, 5, 6, 5)

plt.tight_layout()
plt.savefig('output.svg', format='svg')
```
"""


class ChemistryMoleculeGenerator:
    def __init__(self):
        self.use_rdkit = HAS_RDKIT
        self.use_pubchempy = HAS_PUBCHEMPY
    
    def generate(
        self,
        question: str,
        subject: str = 'chemistry'
    ) -> MoleculeGenResult:
        """
        Generate molecular diagram from question text.
        Tries RDKit first, falls back to matplotlib structural formula.
        Handles reactions by joining multiple SMILES with ".".
        """
        compound_names = extract_compound_names(question)
        
        if not compound_names:
            return MoleculeGenResult(
                success=False,
                svg=None,
                smiles=None,
                compound_name=None,
                method='none',
                error='No compound names found in question'
            )
        
        smiles_list = []
        resolved_names = []
        
        for compound_name in compound_names:
            smiles = get_smiles_from_name(compound_name)
            if smiles:
                smiles_list.append(smiles)
                resolved_names.append(compound_name)
        
        if not smiles_list:
            return MoleculeGenResult(
                success=False,
                svg=None,
                smiles=None,
                compound_name=compound_names[0],
                method='fallback_needed',
                error=f'Could not resolve SMILES for: {compound_names}'
            )
        
        if len(smiles_list) == 1:
            svg = generate_rdkit_svg(smiles_list[0])
        else:
            svg = generate_reaction_svg(smiles_list)
        
        if svg:
            return MoleculeGenResult(
                success=True,
                svg=svg,
                smiles=".".join(smiles_list),
                compound_name=", ".join(resolved_names),
                method='rdkit',
                error=None
            )
        
        return MoleculeGenResult(
            success=False,
            svg=None,
            smiles=None,
            compound_name=", ".join(resolved_names),
            method='fallback_needed',
            error='RDKit rendering failed'
        )
    
    def get_matplotlib_prompt(self, compound_name: str) -> str:
        """Get matplotlib structural formula prompt for fallback."""
        return STRUCTURAL_FORMULA_PROMPT.format(compound_name=compound_name)


if __name__ == "__main__":
    test_questions = [
        "Upon oxidation of toluene by acidified potassium permanganate, which product is obtained?",
        "The benzene ring undergoes electrophilic substitution. What is the product?",
        "Ethanol is oxidized to form which compound?",
        "Identify the functional group in acetophenone.",
    ]
    
    gen = ChemistryMoleculeGenerator()
    
    for q in test_questions:
        print(f"\nQ: {q[:60]}...")
        result = gen.generate(q)
        
        if result.success:
            print(f"  ✓ Method: {result.method}")
            print(f"    Compound: {result.compound_name}")
            print(f"    SMILES: {result.smiles}")
            print(f"    SVG length: {len(result.svg)} chars")
        else:
            print(f"  ✗ Error: {result.error}")
