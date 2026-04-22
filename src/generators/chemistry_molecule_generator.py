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
    
    iupac_patterns = [
        r'\b(\w+ane)\b',
        r'\b(\w+ene)\b',
        r'\b(\w+yne)\b',
        r'\b(\w+ol)\b',
        r'\b(\w+al)\b',
        r'\b(\w+oic acid)\b',
        r'\b(\w+one)\b',
        r'\b(\w+amine)\b',
        r'\b(\w+oate)\b',
        r'\b(\w+oic acid)\b',
        r'\b(benz\w+)\b',
        r'\b(cyclo\w+)\b',
    ]
    
    for pattern in iupac_patterns:
        matches = re.findall(pattern, text_lower)
        compounds.extend(matches)
    
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
    
    if HAS_PUBCHEMPY:
        try:
            results = get_compounds(compound_name, 'name')
            if results:
                return results[0].isomeric_smiles
        except Exception:
            pass
    
    return None


def generate_rdkit_svg(smiles: str, size: Tuple[int, int] = (400, 300)) -> Optional[str]:
    """
    Generate SVG from SMILES using RDKit.
    """
    if not HAS_RDKIT:
        return None
    
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return None
        
        with tempfile.NamedTemporaryFile(suffix='.svg', delete=False) as f:
            temp_path = f.name
        
        Draw.MolToFile(mol, temp_path, size=size, 
                       wedgeBonds=True, 
                       fitToFrame=True,
                       kekulize=True)
        
        with open(temp_path, 'r') as f:
            svg = f.read()
        
        os.unlink(temp_path)
        
        svg = re.sub(r'<\?xml[^>]*\?>', '', svg)
        svg = re.sub(r'<!DOCTYPE[^>]*>', '', svg)
        svg = svg.strip()
        
        return svg
        
    except Exception as e:
        return None


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
        
        for compound_name in compound_names:
            smiles = get_smiles_from_name(compound_name)
            
            if smiles and self.use_rdkit:
                svg = generate_rdkit_svg(smiles)
                
                if svg:
                    return MoleculeGenResult(
                        success=True,
                        svg=svg,
                        smiles=smiles,
                        compound_name=compound_name,
                        method='rdkit',
                        error=None
                    )
        
        return MoleculeGenResult(
            success=False,
            svg=None,
            smiles=None,
            compound_name=compound_names[0] if compound_names else None,
            method='fallback_needed',
            error=f'Could not generate SVG via RDKit. Compounds tried: {compound_names}'
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
