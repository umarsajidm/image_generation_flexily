"""
Chemistry SMILES to SVG generator using RDKit.
"""
from typing import Optional, Tuple
from rdkit import Chem
from rdkit.Chem import Draw, AllChem
from io import BytesIO
import re
from config.settings import SVG_MAX_WIDTH, SVG_MAX_HEIGHT, COLOR_PALETTE


class ChemistryGenerator:
    """Generate SVG diagrams from SMILES strings."""
    
    def __init__(self, width: int = SVG_MAX_WIDTH, height: int = SVG_MAX_HEIGHT):
        self.width = width
        self.height = height
    
    def smiles_to_svg(self, smiles: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Convert SMILES string to minimalistic SVG.
        
        Args:
            smiles: SMILES notation string (e.g., "CCO" for ethanol)
            
        Returns:
            Tuple of (svg_string, error_message)
        """
        if not smiles or len(smiles.strip()) < 2:
            return None, "Invalid or empty SMILES string"
        
        try:
            # Parse SMILES
            mol = Chem.MolFromSmiles(smiles.strip())
            if mol is None:
                return None, f"Failed to parse SMILES: {smiles}"
            
            # Generate 2D coordinates
            AllChem.Compute2DCoords(mol)
            
            # Create drawer with minimalistic settings
            drawer = Draw.MolDraw2DSVG(self.width, self.height)
            
            # Set drawing options for minimalistic style
            drawer.SetLineWidth(2)  # Thinner lines
            drawer.SetFontSize(0.8)  # Smaller font for labels
            
            # Draw molecule
            drawer.DrawMolecule(mol)
            drawer.FinishDrawing()
            
            # Get SVG
            svg = drawer.GetDrawingText()
            
            # Optimize SVG
            svg = self._optimize_svg(svg)
            
            # Validate
            is_valid, issues = self._validate_svg(svg)
            if not is_valid:
                return None, f"Generated SVG invalid: {', '.join(issues)}"
            
            return svg, None
            
        except Exception as e:
            return None, f"Error generating SVG: {str(e)}"
    
    def _optimize_svg(self, svg: str) -> str:
        """Optimize SVG for web display."""
        # Remove unnecessary whitespace
        svg = re.sub(r'\s+', ' ', svg)
        
        # Ensure proper viewBox
        if 'viewBox' not in svg:
            svg = svg.replace('<svg', f'<svg viewBox="0 0 {self.width} {self.height}"')
        
        # Add responsive styling
        svg = svg.replace(
            '<svg',
            f'<svg style="max-width: 100%; height: auto;"'
        )
        
        return svg.strip()
    
    def _validate_svg(self, svg: str) -> Tuple[bool, list]:
        """Validate generated SVG."""
        issues = []
        
        # RDKit may include XML declaration
        svg_content = svg.strip()
        if svg_content.startswith('<?xml'):
            svg_content = svg_content.split('<svg', 1)[-1] if '<svg' in svg_content else svg_content
        
        # Check for SVG tags
        if '<svg' not in svg or '</svg>' not in svg:
            issues.append("Missing SVG tags")
        
        # Check size
        if len(svg) > 15000:
            issues.append(f"SVG too large: {len(svg)} bytes")
        
        return len(issues) == 0, issues
    
    def batch_generate(self, smiles_list: list) -> list:
        """
        Generate SVGs for multiple SMILES strings.
        
        Args:
            smiles_list: List of (mcq_id, smiles) tuples
            
        Returns:
            List of results with (mcq_id, svg, error)
        """
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
