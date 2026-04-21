"""
Custom SVG renderer for chemistry diagrams.
Generates textbook-style black-and-white diagrams with proper atom labels.
"""
from typing import List, Tuple, Optional
from rdkit import Chem
from rdkit.Chem import AllChem
import math


FUNCTIONAL_GROUPS = {
    'COOH': ['C(=O)O', 'C(=O)[OH]'],
    'OH': ['O'],
    'NH2': ['N'],
    'CHO': ['C=O'],
    'COO': ['C(=O)[O-]'],
    'CN': ['C#N'],
    'NO2': ['[N+](=O)[O-]'],
}


class AtomInfo:
    def __init__(self, idx: int, symbol: str, x: float, y: float, 
                 charge: int = 0, num_h: int = 0, is_aromatic: bool = False):
        self.idx = idx
        self.symbol = symbol
        self.x = x
        self.y = y
        self.charge = charge
        self.num_h = num_h
        self.is_aromatic = is_aromatic
        self.neighbors: List[int] = []
        self.bonds: List[Tuple[int, int]] = []  # (neighbor_idx, bond_type)


class BondInfo:
    def __init__(self, idx1: int, idx2: int, bond_type: int):
        self.idx1 = idx1
        self.idx2 = idx2
        self.bond_type = bond_type  # 1=single, 2=double, 3=triple, 4=aromatic


class SVGRenderer:
    """Renders chemistry diagrams as SVG with proper atom labels."""
    
    def __init__(self, width: int = 400, height: int = 250, padding: int = 30):
        self.width = width
        self.height = height
        self.padding = padding
        self.font_family = "Arial, sans-serif"
        self.font_size = 14
        self.stroke_width = 1.5
        self.double_bond_spacing = 3
        self.triple_bond_spacing = 3
    
    def render_molecule(self, mol: Chem.Mol) -> str:
        """Render an RDKit molecule to SVG."""
        if mol is None:
            return None
        
        conf = mol.GetConformer()
        if conf is None:
            AllChem.Compute2DCoords(mol)
            conf = mol.GetConformer()
        
        atoms = self._extract_atoms(mol, conf)
        bonds = self._extract_bonds(mol)
        
        coords = [(a.x, a.y) for a in atoms]
        scaled_coords = self._scale_coordinates(coords)
        
        for i, atom in enumerate(atoms):
            atom.x, atom.y = scaled_coords[i]
        
        svg_parts = []
        svg_parts.append(self._svg_header())
        
        for bond in bonds:
            svg_parts.append(self._render_bond(bond, atoms))
        
        for atom in atoms:
            label_svg = self._get_atom_label(atom, mol)
            if label_svg:
                svg_parts.append(label_svg)
        
        svg_parts.append(self._svg_footer())
        
        return '\n'.join(svg_parts)
    
    def _extract_atoms(self, mol: Chem.Mol, conf) -> List[AtomInfo]:
        """Extract atom information from molecule."""
        atoms = []
        
        for i in range(mol.GetNumAtoms()):
            atom = mol.GetAtomWithIdx(i)
            pos = conf.GetAtomPosition(i)
            
            atom_info = AtomInfo(
                idx=i,
                symbol=atom.GetSymbol(),
                x=pos.x,
                y=pos.y,
                charge=atom.GetFormalCharge(),
                num_h=atom.GetTotalNumHs(),
                is_aromatic=atom.GetIsAromatic()
            )
            
            for neighbor in atom.GetNeighbors():
                atom_info.neighbors.append(neighbor.GetIdx())
            
            atoms.append(atom_info)
        
        for i in range(mol.GetNumAtoms()):
            atom = mol.GetAtomWithIdx(i)
            for neighbor in atom.GetNeighbors():
                bond = mol.GetBondBetweenAtoms(i, neighbor.GetIdx())
                if bond and neighbor.GetIdx() > i:
                    atoms[i].bonds.append((neighbor.GetIdx(), bond.GetBondType()))
        
        return atoms
    
    def _extract_bonds(self, mol: Chem.Mol) -> List[BondInfo]:
        """Extract bond information from molecule."""
        bonds = []
        
        for bond in mol.GetBonds():
            bond_type = 1
            bt = bond.GetBondType()
            if bt == Chem.BondType.SINGLE:
                bond_type = 1
            elif bt == Chem.BondType.DOUBLE:
                bond_type = 2
            elif bt == Chem.BondType.TRIPLE:
                bond_type = 3
            elif bt == Chem.BondType.AROMATIC:
                bond_type = 4
            
            bonds.append(BondInfo(
                idx1=bond.GetBeginAtomIdx(),
                idx2=bond.GetEndAtomIdx(),
                bond_type=bond_type
            ))
        
        return bonds
    
    def _scale_coordinates(self, coords: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
        """Scale coordinates to fit in SVG viewport."""
        if not coords:
            return coords
        
        xs = [c[0] for c in coords]
        ys = [c[1] for c in coords]
        
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        
        range_x = max_x - min_x if max_x != min_x else 1
        range_y = max_y - min_y if max_y != min_y else 1
        
        available_width = self.width - 2 * self.padding
        available_height = self.height - 2 * self.padding
        
        scale = min(available_width / range_x, available_height / range_y)
        
        center_x = (min_x + max_x) / 2
        center_y = (min_y + max_y) / 2
        
        scaled = []
        for x, y in coords:
            sx = self.width / 2 + (x - center_x) * scale
            sy = self.height / 2 - (y - center_y) * scale
            scaled.append((sx, sy))
        
        return scaled
    
    def _svg_header(self) -> str:
        """Generate SVG opening tag."""
        return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{self.width}" height="{self.height}" viewBox="0 0 {self.width} {self.height}">
<rect width="{self.width}" height="{self.height}" fill="white"/>
<style>
.atom-label {{ font-family: {self.font_family}; font-size: {self.font_size}px; fill: #000000; }}
.subscript {{ font-size: {int(self.font_size * 0.7)}px; }}
</style>'''
    
    def _svg_footer(self) -> str:
        """Generate SVG closing tag."""
        return '</svg>'
    
    def _render_bond(self, bond: BondInfo, atoms: List[AtomInfo]) -> str:
        """Render a bond as SVG path(s)."""
        a1 = atoms[bond.idx1]
        a2 = atoms[bond.idx2]
        
        dx = a2.x - a1.x
        dy = a2.y - a1.y
        length = math.sqrt(dx * dx + dy * dy)
        
        if length < 0.1:
            return ''
        
        ux = dx / length
        uy = dy / length
        
        perpx = -uy
        perpy = ux
        
        offset = 8
        start_x = a1.x + ux * offset
        start_y = a1.y + uy * offset
        end_x = a2.x - ux * offset
        end_y = a2.y - uy * offset
        
        paths = []
        
        if bond.bond_type == 1:
            paths.append(f'<path d="M {start_x:.1f} {start_y:.1f} L {end_x:.1f} {end_y:.1f}" stroke="#000000" stroke-width="{self.stroke_width}" fill="none"/>')
        
        elif bond.bond_type == 2:
            spacing = self.double_bond_spacing
            x1a = start_x + perpx * spacing
            y1a = start_y + perpy * spacing
            x2a = end_x + perpx * spacing
            y2a = end_y + perpy * spacing
            x1b = start_x - perpx * spacing
            y1b = start_y - perpy * spacing
            x2b = end_x - perpx * spacing
            y2b = end_y - perpy * spacing
            
            paths.append(f'<path d="M {x1a:.1f} {y1a:.1f} L {x2a:.1f} {y2a:.1f}" stroke="#000000" stroke-width="{self.stroke_width}" fill="none"/>')
            paths.append(f'<path d="M {x1b:.1f} {y1b:.1f} L {x2b:.1f} {y2b:.1f}" stroke="#000000" stroke-width="{self.stroke_width}" fill="none"/>')
        
        elif bond.bond_type == 3:
            spacing = self.triple_bond_spacing
            for i in [-1, 0, 1]:
                x1 = start_x + perpx * spacing * i
                y1 = start_y + perpy * spacing * i
                x2 = end_x + perpx * spacing * i
                y2 = end_y + perpy * spacing * i
                paths.append(f'<path d="M {x1:.1f} {y1:.1f} L {x2:.1f} {y2:.1f}" stroke="#000000" stroke-width="{self.stroke_width}" fill="none"/>')
        
        elif bond.bond_type == 4:
            paths.append(f'<path d="M {start_x:.1f} {start_y:.1f} L {end_x:.1f} {end_y:.1f}" stroke="#000000" stroke-width="{self.stroke_width}" fill="none"/>')
        
        return '\n'.join(paths)
    
    def _get_atom_label(self, atom: AtomInfo, mol: Chem.Mol) -> str:
        """Get SVG text element for atom label."""
        
        if atom.symbol == 'C':
            if len(atom.neighbors) >= 2:
                return ''
            
            if len(atom.neighbors) == 0:
                label = 'CH₄'
            elif len(atom.neighbors) == 1:
                if atom.num_h == 3:
                    label = 'CH₃'
                elif atom.num_h == 2:
                    label = 'CH₂'
                elif atom.num_h == 1:
                    label = 'CH'
                else:
                    label = 'C'
            else:
                return ''
            
            return self._render_text_label(atom.x, atom.y, label)
        
        elif atom.symbol in ['O', 'N', 'S', 'P', 'F', 'Cl', 'Br', 'I']:
            label = atom.symbol
            if atom.num_h > 0:
                label += 'H'
                if atom.num_h > 1:
                    label += self._subscript(str(atom.num_h))
            return self._render_text_label(atom.x, atom.y, label)
        
        return self._render_text_label(atom.x, atom.y, atom.symbol)
    
    def _subscript(self, num: str) -> str:
        """Convert number to subscript."""
        subscripts = {'0': '₀', '1': '₁', '2': '₂', '3': '₃', '4': '₄',
                     '5': '₅', '6': '₆', '7': '₇', '8': '₈', '9': '₉'}
        return ''.join(subscripts.get(c, c) for c in num)
    
    def _render_text_label(self, x: float, y: float, label: str) -> str:
        """Render a text label at the given position."""
        text_y = y + self.font_size / 3
        
        parts = []
        current = ''
        in_subscript = False
        
        i = 0
        while i < len(label):
            c = label[i]
            if c in '₀₁₂₃₄₅₆₇₈₉':
                if current:
                    parts.append(('normal', current))
                    current = ''
                parts.append(('sub', c))
            else:
                current += c
            i += 1
        
        if current:
            parts.append(('normal', current))
        
        if len(parts) == 1 and parts[0][0] == 'normal':
            return f'<text x="{x:.1f}" y="{text_y:.1f}" text-anchor="middle" class="atom-label">{parts[0][1]}</text>'
        
        tspans = []
        for style, text in parts:
            if style == 'sub':
                tspans.append(f'<tspan class="subscript">{text}</tspan>')
            else:
                tspans.append(f'<tspan>{text}</tspan>')
        
        return f'<text x="{x:.1f}" y="{text_y:.1f}" text-anchor="middle" class="atom-label">{"".join(tspans)}</text>'
