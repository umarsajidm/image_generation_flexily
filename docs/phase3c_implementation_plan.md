# Phase 3C Implementation Plan - Chemistry Molecules

**Status**: Ready to implement
**Expected Duration**: ~30 minutes
**Expected Success Rate**: 90-95%

---

## Overview

Phase 3C processes **67 chemistry molecule MCQs** using RDKit library for deterministic molecular diagram generation.

### Key Differences from Phase 3A/3B

| Aspect | Phase 3A | Phase 3B | Phase 3C |
|--------|----------|----------|----------|
| **Approach** | Generic templates | Few-shot hybrid | Library-based (RDKit) |
| **AI Involvement** | High | Medium | Low (fallback only) |
| **Speed** | ~3 sec/MCQ | ~3 sec/MCQ | ~0.1 sec/MCQ |
| **Determinism** | Variable | Medium | High (same SMILES = same SVG) |
| **Few-shot Examples** | No | Yes (9) | No |

---

## Architecture

```
MCQ Input
    ↓
extract_compound_names() → ["toluene", "benzene"]
    ↓
get_smiles_from_name() → "Cc1ccccc1"
    ├── COMMON_COMPOUNDS dict (44 compounds)
    ├── PubChemPy API (111M+ compounds)
    └── IUPAC pattern matching
    ↓
generate_rdkit_svg() → SVG
    ├── MolDraw2DSVG for textbook quality
    ├── Transparent background
    └── Bond width: 2.0, Stereo annotations
    ↓
inject_textbook_style() → Final SVG
    ↓
Quality Check → Score (0-100)
```

---

## Implementation Steps

### Step 1: Install PubChemPy
```bash
cd /root/image_generation_flexily
./venv/bin/pip install pubchempy
```

### Step 2: Enhance chemistry_molecule_generator.py

**File**: `src/generators/chemistry_molecule_generator.py`

**Changes**:
1. Import MolDraw2D:
   ```python
   from rdkit.Chem.Draw import rdMolDraw2D
   ```

2. Replace `Draw.MolToFile()` with `MolDraw2DSVG()`:
   ```python
   def generate_rdkit_svg(smiles: str, size: Tuple[int, int] = (400, 300)) -> Optional[str]:
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
   ```

3. Add reaction handling (multiple compounds):
   ```python
   def generate_reaction_svg(smiles_list: List[str], size: Tuple[int, int] = (600, 300)) -> Optional[str]:
       """Generate SVG for reactions (multiple molecules side-by-side)."""
       if not smiles_list or not HAS_RDKIT:
           return None
       
       combined_smiles = ".".join(smiles_list)
       return generate_rdkit_svg(combined_smiles, size)
   ```

4. Enhance compound extraction with more IUPAC patterns:
   ```python
   def extract_compound_names(text: str) -> List[str]:
       text_lower = text.lower()
       compounds = []
       
       # Check dictionary first
       for name in COMMON_COMPOUNDS.keys():
           if name in text_lower:
               compounds.append(name)
       
       # Enhanced IUPAC patterns
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
       ]
       
       for pattern in iupac_patterns:
           matches = re.findall(pattern, text_lower)
           compounds.extend(matches)
       
       # Dedupe
       seen = set()
       unique = []
       for c in compounds:
           if c not in seen and len(c) > 3:
               seen.add(c)
               unique.append(c)
       
       return unique
   ```

5. Update `generate()` to handle reactions:
   ```python
   def generate(self, question: str, subject: str = 'chemistry') -> MoleculeGenResult:
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
       
       # Try each compound
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
       
       # Generate SVG
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
   ```

### Step 3: Create scripts/process_phase3c.py

**File**: `scripts/process_phase3c.py`

**Purpose**: Batch processor for MOLECULE type MCQs

**Key features**:
- No rate limiting (RDKit is local)
- Track failed compounds in `failed_compounds.txt`
- Generate HTML viewer
- Expected execution: ~10 seconds for 67 MCQs

See full implementation in `/root/image_generation_flexily/docs/phase3c_script_template.py`

### Step 4: Test with Sample MCQs
```bash
cd /root/image_generation_flexily
./venv/bin/python scripts/process_phase3c.py --test-limit 5
```

### Step 5: Run Full Batch
```bash
cd /root/image_generation_flexily
./venv/bin/python scripts/process_phase3c.py
```

### Step 6: Post-Processing
```bash
# Check failed compounds
cat /root/image_generation_flexily/output/generated/phase3c/failed_compounds.txt

# If failures > 5%, add to COMMON_COMPOUNDS dict and re-run
```

---

## Expected Results

| Metric | Expected |
|--------|----------|
| Total MCQs | 67 |
| RDKit Success | 60-63 (90-95%) |
| PubChemPy Resolved | 2-5 |
| Fallback to Gemini | 2-4 |
| Execution Time | ~10 seconds |
| Avg Quality | 85+ |

---

## Common Compounds Dictionary

Current dictionary has 44 compounds. Key entries:

```python
COMMON_COMPOUNDS = {
    # Aromatics
    'benzene': 'c1ccccc1',
    'toluene': 'Cc1ccccc1',
    'phenol': 'Oc1ccccc1',
    'aniline': 'Nc1ccccc1',
    
    # Alcohols
    'ethanol': 'CCO',
    'methanol': 'CO',
    
    # Aldehydes/Ketones
    'formaldehyde': 'C=O',
    'acetaldehyde': 'CC=O',
    'acetone': 'CC(=O)C',
    
    # Carboxylic Acids
    'acetic acid': 'CC(=O)O',
    'formic acid': 'C(=O)O',
    
    # Alkanes
    'methane': 'C',
    'ethane': 'CC',
    'propane': 'CCC',
    'butane': 'CCCC',
    
    # Alkenes/Alkynes
    'ethene': 'C=C',
    'ethyne': 'C#C',
    
    # Cyclic
    'cyclohexane': 'C1CCCCC1',
    'cyclopentane': 'C1CCCC1',
    'naphthalene': 'c1ccc2ccccc2c1',
    
    # ... and 26 more
}
```

---

## Failure Scenarios & Solutions

| Scenario | Cause | Solution |
|----------|-------|----------|
| Compound not found | Rare IUPAC name | PubChemPy API → Add to dict |
| No compound extracted | Vague question | Fallback to Gemini |
| Complex biomolecule | DNA, ATP, proteins | Fallback to Gemini |
| PubChemPy timeout | Network issue | Retry or use dictionary |
| Multiple compounds | Reaction question | Join SMILES with "." |

---

## Files to Create/Modify

### Create
- `scripts/process_phase3c.py` - Batch processor

### Modify
- `src/generators/chemistry_molecule_generator.py` - Add MolDraw2D, reactions

### Output
- `output/generated/phase3c/checkpoint.jsonl`
- `output/generated/phase3c/phase3c_results.jsonl`
- `output/generated/phase3c/failed_compounds.txt`
- `output/generated/phase3c/view_results.html`
- `output/generated/phase3c/*.svg`

---

## Commands Reference

```bash
# Install PubChemPy
cd /root/image_generation_flexily
./venv/bin/pip install pubchempy

# Test generator
./venv/bin/python src/generators/chemistry_molecule_generator.py

# Run with test limit
./venv/bin/python scripts/process_phase3c.py --test-limit 5

# Run full batch
./venv/bin/python scripts/process_phase3c.py

# View results
open /root/image_generation_flexily/output/generated/phase3c/view_results.html
```

---

## After Session Compact

Say: **"proceed with Phase 3C implementation"**

---

*Created: 2026-04-23*
