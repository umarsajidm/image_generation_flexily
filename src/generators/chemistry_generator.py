"""
Chemistry SMILES to SVG generator with proper bond-label connections.
For organic molecules: bonds extend to label positions.
For inorganic molecules: standard RDKit output.
"""
from typing import Optional, Tuple, List, Dict
import re
import math
from rdkit import Chem
from rdkit.Chem import Draw, AllChem
from rdkit.Chem.Draw import MolDrawOptions

SVG_MAX_WIDTH = 400
SVG_MAX_HEIGHT = 250


class ChemistryGenerator:
    """Generate SVG diagrams from SMILES in textbook style."""
    
    def __init__(self, width: int = SVG_MAX_WIDTH, height: int = SVG_MAX_HEIGHT):
        self.width = width
        self.height = height
        self.font_size = 14
        self.label_padding = 5
    
    def smiles_to_svg(self, smiles: str) -> Tuple[Optional[str], Optional[str]]:
        """Convert SMILES to textbook-style diagram."""
        if not smiles or len(smiles.strip()) < 2:
            return None, "Invalid or empty SMILES string"
        
        smiles = smiles.strip()
        
        if ';' in smiles:
            return None, f"Multiple molecules not supported: {smiles}"
        
        try:
            mol = Chem.MolFromSmiles(smiles)
            if mol is None:
                return None, f"Failed to parse SMILES: {smiles}"
            
            AllChem.Compute2DCoords(mol)
            
            if self._is_organic(mol):
                svg = self._render_organic(mol)
            else:
                svg = self._render_inorganic(mol)
            
            if svg is None:
                return None, "Failed to generate SVG"
            
            return svg, None
            
        except Exception as e:
            return None, f"Error generating SVG: {str(e)}"
    
    def _is_organic(self, mol: Chem.Mol) -> bool:
        """Check if molecule is organic (has C-C bonds or C-H bonds)."""
        for atom in mol.GetAtoms():
            if atom.GetSymbol() == 'C':
                for neighbor in atom.GetNeighbors():
                    if neighbor.GetSymbol() == 'C':
                        return True
                if atom.GetTotalNumHs() > 0:
                    return True
        return False
    
    def _render_inorganic(self, mol: Chem.Mol) -> str:
        """Render inorganic molecule using standard RDKit."""
        drawer = Draw.MolDraw2DSVG(self.width, self.height)
        opts = MolDrawOptions()
        opts.useBWAtomPalette = True
        drawer.SetDrawOptions(opts)
        drawer.SetLineWidth(2)
        drawer.DrawMolecule(mol)
        drawer.FinishDrawing()
        svg = drawer.GetDrawingText()
        return self._clean_colors(svg)
    
    def _render_organic(self, mol: Chem.Mol) -> str:
        """Render organic molecule with proper bond-label connections."""
        conf = mol.GetConformer()
        
        coords = []
        for i in range(mol.GetNumAtoms()):
            pos = conf.GetAtomPosition(i)
            coords.append((pos.x, pos.y))
        
        scaled = self._scale_coords(coords)
        
        atom_labels = self._get_atom_labels(mol, scaled)
        
        svg_parts = []
        svg_parts.append(self._svg_header())
        
        for bond in mol.GetBonds():
            svg_parts.append(self._render_bond(bond, mol, scaled, atom_labels))
        
        for i, (label, x, y) in atom_labels.items():
            if label:
                svg_parts.append(self._render_label(label, x, y))
        
        svg_parts.append('</svg>')
        
        return '\n'.join(svg_parts)
    
    def _scale_coords(self, coords: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
        """Scale coordinates to fit in SVG viewport."""
        if not coords:
            return coords
        
        xs = [c[0] for c in coords]
        ys = [c[1] for c in coords]
        
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        
        range_x = max_x - min_x if max_x != min_x else 1
        range_y = max_y - min_y if max_y != min_y else 1
        
        padding = 50
        available_width = self.width - 2 * padding
        available_height = self.height - 2 * padding
        
        scale = min(available_width / range_x, available_height / range_y)
        
        center_x = (min_x + max_x) / 2
        center_y = (min_y + max_y) / 2
        
        scaled = []
        for x, y in coords:
            sx = self.width / 2 + (x - center_x) * scale
            sy = self.height / 2 - (y - center_y) * scale
            scaled.append((sx, sy))
        
        return scaled
    
    def _get_atom_labels(self, mol: Chem.Mol, scaled: List[Tuple[float, float]]) -> Dict[int, Tuple[str, float, float]]:
        """Get labels for each atom with positions."""
        labels = {}
        
        for i in range(mol.GetNumAtoms()):
            atom = mol.GetAtomWithIdx(i)
            x, y = scaled[i]
            
            if atom.GetSymbol() == 'C':
                num_h = atom.GetTotalNumHs()
                neighbors = list(atom.GetNeighbors())
                num_c_neighbors = sum(1 for n in neighbors if n.GetSymbol() == 'C')
                
                if num_c_neighbors >= 2:
                    labels[i] = (None, x, y)
                elif num_h == 3:
                    labels[i] = ('CH₃', x, y)
                elif num_h == 2:
                    labels[i] = ('CH₂', x, y)
                elif num_h == 1:
                    labels[i] = ('CH', x, y)
                else:
                    if len(neighbors) == 1 and neighbors[0].GetSymbol() in ['O', 'N', 'S']:
                        labels[i] = (None, x, y)
                    else:
                        labels[i] = ('C', x, y)
            elif atom.GetSymbol() in ['O', 'N', 'S', 'P', 'F', 'Cl', 'Br', 'I']:
                label = atom.GetSymbol()
                num_h = atom.GetTotalNumHs()
                if num_h > 0:
                    label += 'H'
                    if num_h > 1:
                        label += self._subscript(str(num_h))
                labels[i] = (label, x, y)
            else:
                labels[i] = (atom.GetSymbol(), x, y)
        
        return labels
    
    def _render_bond(self, bond, mol: Chem.Mol, scaled: List[Tuple[float, float]], 
                     atom_labels: Dict[int, Tuple[str, float, float]]) -> str:
        """Render a bond with proper endpoints."""
        idx1 = bond.GetBeginAtomIdx()
        idx2 = bond.GetEndAtomIdx()
        
        x1, y1 = scaled[idx1]
        x2, y2 = scaled[idx2]
        
        label1, lx1, ly1 = atom_labels.get(idx1, (None, x1, y1))
        label2, lx2, ly2 = atom_labels.get(idx2, (None, x2, y2))
        
        start_offset = self._get_label_offset(label1, x1, y1, x2, y2)
        end_offset = self._get_label_offset(label2, x2, y2, x1, y1)
        
        bx1 = x1 + start_offset[0]
        by1 = y1 + start_offset[1]
        bx2 = x2 + end_offset[0]
        by2 = y2 + end_offset[1]
        
        bond_type = bond.GetBondType()
        
        if bond_type == Chem.BondType.SINGLE:
            return f'<line x1="{bx1:.1f}" y1="{by1:.1f}" x2="{bx2:.1f}" y2="{by2:.1f}" stroke="#000000" stroke-width="2"/>'
        elif bond_type == Chem.BondType.DOUBLE:
            dx = x2 - x1
            dy = y2 - y1
            length = math.sqrt(dx*dx + dy*dy)
            if length > 0:
                px = -dy / length * 3
                py = dx / length * 3
            else:
                px, py = 0, 3
            
            return (f'<line x1="{bx1+px:.1f}" y1="{by1+py:.1f}" x2="{bx2+px:.1f}" y2="{by2+py:.1f}" stroke="#000000" stroke-width="2"/>\n'
                    f'<line x1="{bx1-px:.1f}" y1="{by1-py:.1f}" x2="{bx2-px:.1f}" y2="{by2-py:.1f}" stroke="#000000" stroke-width="2"/>')
        elif bond_type == Chem.BondType.TRIPLE:
            dx = x2 - x1
            dy = y2 - y1
            length = math.sqrt(dx*dx + dy*dy)
            if length > 0:
                px = -dy / length * 4
                py = dx / length * 4
            else:
                px, py = 0, 4
            
            return (f'<line x1="{bx1:.1f}" y1="{by1:.1f}" x2="{bx2:.1f}" y2="{by2:.1f}" stroke="#000000" stroke-width="2"/>\n'
                    f'<line x1="{bx1+px:.1f}" y1="{by1+py:.1f}" x2="{bx2+px:.1f}" y2="{by2+py:.1f}" stroke="#000000" stroke-width="2"/>\n'
                    f'<line x1="{bx1-px:.1f}" y1="{by1-py:.1f}" x2="{bx2-px:.1f}" y2="{by2-py:.1f}" stroke="#000000" stroke-width="2"/>')
        elif bond_type == Chem.BondType.AROMATIC:
            return f'<line x1="{bx1:.1f}" y1="{by1:.1f}" x2="{bx2:.1f}" y2="{by2:.1f}" stroke="#000000" stroke-width="2"/>'
        
        return f'<line x1="{bx1:.1f}" y1="{by1:.1f}" x2="{bx2:.1f}" y2="{by2:.1f}" stroke="#000000" stroke-width="2"/>'
    
    def _get_label_offset(self, label: Optional[str], x: float, y: float, 
                          other_x: float, other_y: float) -> Tuple[float, float]:
        """Calculate offset from atom position to where bond should start."""
        if not label:
            return (0, 0)
        
        dx = other_x - x
        dy = other_y - y
        length = math.sqrt(dx*dx + dy*dy)
        
        if length == 0:
            return (0, 0)
        
        label_width = len(label) * self.font_size * 0.5
        
        offset = label_width / 2 + self.label_padding
        
        ux = dx / length
        uy = dy / length
        
        return (ux * offset, uy * offset)
    
    def _render_label(self, label: str, x: float, y: float) -> str:
        """Render a text label at position."""
        text_y = y + self.font_size / 3
        
        if '₃' in label or '₂' in label:
            main = label[0:2]
            sub = label[2] if len(label) > 2 else ''
            return f'<text x="{x:.1f}" y="{text_y:.1f}" text-anchor="middle" style="font-family: Arial, sans-serif; font-size: {self.font_size}px; fill: #000000;">{main}<tspan style="font-size: {int(self.font_size*0.7)}px;">{sub}</tspan></text>'
        
        return f'<text x="{x:.1f}" y="{text_y:.1f}" text-anchor="middle" style="font-family: Arial, sans-serif; font-size: {self.font_size}px; fill: #000000;">{label}</text>'
    
    def _svg_header(self) -> str:
        """Generate SVG header."""
        return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{self.width}" height="{self.height}" viewBox="0 0 {self.width} {self.height}">
<rect width="{self.width}" height="{self.height}" fill="white"/>'''
    
    def _subscript(self, s: str) -> str:
        """Convert to subscript."""
        subs = {'0': '₀', '1': '₁', '2': '₂', '3': '₃', '4': '₄', '5': '₅', '6': '₆', '7': '₇', '8': '₈', '9': '₉'}
        return ''.join(subs.get(c, c) for c in s)
    
    def _clean_colors(self, svg: str) -> str:
        """Ensure black-and-white."""
        svg = re.sub(r"fill='(#[0-9A-Fa-f]{6})'", 
                     lambda m: f"fill='#000000'" if m.group(1).upper() not in ['#FFFFFF', '#000000'] else m.group(0), svg)
        svg = re.sub(r'fill="(#[0-9A-Fa-f]{6})"', 
                     lambda m: f'fill="#000000"' if m.group(1).upper() not in ['#FFFFFF', '#000000'] else m.group(0), svg)
        svg = re.sub(r"stroke:'(#[0-9A-Fa-f]{6})'", r"stroke:'#000000'", svg)
        svg = re.sub(r'stroke:(#[0-9A-Fa-f]{6})', r'stroke:#000000', svg)
        return svg
    
    def _validate_svg(self, svg: str) -> Tuple[bool, List[str]]:
        """Validate SVG."""
        issues = []
        if '<svg' not in svg or '</svg>' not in svg:
            issues.append("Missing SVG tags")
        if len(svg) > 15000:
            issues.append(f"SVG too large: {len(svg)} bytes")
        return len(issues) == 0, issues
    
    def batch_generate(self, smiles_list: List[Tuple[str, str]]) -> List[Dict]:
        """Generate SVGs for multiple SMILES."""
        results = []
        for mcq_id, smiles in smiles_list:
            svg, error = self.smiles_to_svg(smiles)
            results.append({
                'mcq_id': mcq_id,
                'smiles': smiles,
                'svg': svg,
                'error': error,
                'success': svg is not None
            })
        return results
