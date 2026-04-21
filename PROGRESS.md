# Image Generation Flexily - Progress Log

## Session: April 21, 2026

---

## Overview

Building an image generation pipeline for Flexily MCQs. The goal is to generate SVG diagrams for chemistry MCQs that match the Punjab 2nd Year Chemistry textbook style (black-and-white, educational diagrams).

---

## Completed: Phase 1 - Chemistry SMILES to SVG

### Stats
- **Total MCQs with SMILES:** 840
- **Successfully Generated:** 683 SVGs (81.3%)
- **Failed:** 157 (multiple molecules, invalid SMILES)
- **Approved:** 683 (all successful items)

### Input Data
- **Source:** `/root/gcp_app_for_mcqs/finished_mcqs_output/v3/predictions.jsonl`
- **Total MCQs:** 34,330
- **MCQs with SMILES (Phase 1):** 840
- **MCQs needing images (Phase 2/3):** 1,026

### Output Files
```
/root/image_generation_flexily/
├── output/
│   ├── generated/
│   │   └── chemistry/
│   │       ├── batch_results.jsonl     # All 683 results with SVGs
│   │       └── *.svg                   # 683 individual SVG files
│   ├── reviews/
│   │   └── approved.jsonl              # All approved items
│   └── failed/
│       └── phase1_failures.jsonl       # 157 failed items
├── src/
│   └── generators/
│       └── chemistry_generator.py      # Main generator
└── ui/
    └── review_app.py                   # Streamlit review UI
```

---

## How the Generator Works

### 1. Organic vs Inorganic Detection
```python
def _is_organic(mol):
    # Organic if: C-C bonds OR C-H bonds
    # Inorganic: O2, CO2, PCl5, etc.
```

### 2. Organic Molecules
- Custom renderer with connected bonds
- Carbon labels: CH₃, CH₂, CH
- Bonds extend to label positions (no gaps)
- Double bonds: 2 parallel lines
- Triple bonds: 3 parallel lines
- Aromatic bonds: single line (no dots/dashes)

### 3. Inorganic Molecules
- Standard RDKit output
- Heteroatom labels (O, N, Cl, etc.)
- Black-and-white color scheme

---

## Key Design Decisions

### Decision 1: Hybrid Renderer
After user feedback, implemented a hybrid approach:
- Organic molecules → Custom renderer with carbon labels
- Inorganic molecules → Standard RDKit (already approved by user)

### Decision 2: Bond-Label Connection
Bonds extend to label positions, not just atom centers:
```
CH₃────────CH₃   (correct)
CH₃  ────  CH₃   (wrong - gaps)
```

### Decision 3: No Dashed Aromatic Bonds
User rejected dashed lines on aromatic rings ("dots on ring"):
- Before: `stroke-dasharray="4,3"` (dots)
- After: Solid single bonds only

---

## Failed Items Analysis

157 items failed (18.7%):
- **Multiple molecules** (semicolon-separated SMILES): ~57 items
- **Invalid SMILES** (ions, non-standard notation): ~100 items

Examples of failures:
- `Cl.H;O.H.H;N.H.H.H` - Multiple molecules
- `[NH4+].[NO3-]` - Ionic compounds with dot notation
- `CCO.I.NaOH` - Multiple reagents

---

## Textbook Style Reference

**Analyzed:** Punjab 2nd Year Chemistry textbook (pages 250-400, 372 images)

**Key characteristics:**
- Black-and-white line drawings
- Sans-serif font (Arial-like)
- Standard organic chemistry notation
- CH₃, CH₂, CH labels for terminal carbons
- No atom indices (C₁, H₄ not used)
- Benzene: Both Kekulé and circle representations

**Style specification:** `/root/image_generation_flexily/style_specification.md`

---

## Next Steps

### Phase 2: Reference-Based Generation
- MCQs that need images based on textbook references
- Input: `requires_manual_image=True`, has reference image
- Count: ~1,026 MCQs

### Phase 3: AI-Generated Images
- MCQs needing images without references
- Use AI to generate appropriate diagrams

### To Continue:
```bash
cd /root/image_generation_flexily

# Review existing results
streamlit run ui/review_app.py

# Run Phase 2 (when ready)
python scripts/run_phase2.py

# Run Phase 3 (when ready)
python scripts/run_phase3.py
```

---

## Dependencies Installed
- rdkit (2026.3.1)
- streamlit (1.56.0)

---

## Git Repository

All changes committed. Last commit:
- Added chemistry_generator.py with organic/inorganic handling
- Added review_app.py for Streamlit UI
- Generated 683 approved SVGs
- Documented progress in PROGRESS.md
