# Image Generation Pipeline

## Overview

This pipeline generates textbook-style SVG diagrams for Punjab Board Physics/Chemistry MCQs. It uses a multi-phase approach with Python-first code generation (matplotlib/schemdraw) and fallback to raw SVG generation.

## Architecture

```
predictions.jsonl (MCQs)
       ↓
   data_loader.py
       ↓
   MCQData objects
       ↓
   diagram_classifier.py → DiagramType (graph, circuit, molecule, etc.)
       ↓
   multi_reference_generator.py
       ↓
   Generation Methods (priority order):
   1. python_code → Gemini generates matplotlib/schemdraw code → Execute locally
   2. gemini_svg  → Raw SVG via Gemini 2.5 Pro (fallback)
   3. rdkit       → Molecular structures (chemistry)
   4. mermaid     → Flowcharts/diagrams (biology)
   5. imagen      → Image generation (complex bio)
       ↓
   svg_quality_checker.py → Quality Score (0-100)
       ↓
   make_svg_responsive.py → Responsive SVG conversion
       ↓
   Output: SVG + metadata
```

## Diagram Types & Methods

| Diagram Type | MCQs | Primary Method | Fallback |
|-------------|------|----------------|----------|
| **graph** | 154 | matplotlib | Gemini SVG |
| **circuit** | 148 | schemdraw | Gemini SVG |
| **waves** | 38 | matplotlib | Gemini SVG |
| **mechanics** | 86 | matplotlib | Pre-built templates |
| **optics** | 5 | matplotlib | Gemini SVG |
| **molecule** | 67 | RDKit | Matplotlib structural |
| **atom** | 31 | raw_svg | matplotlib |
| **apparatus** | 2 | raw_svg | matplotlib |
| **biology** | TBD | mermaid/imagen | Gemini SVG |

## Quality Thresholds

| Score | Action | Description |
|-------|--------|-------------|
| **70+** | Auto-accept | High-quality textbook style |
| **50-70** | Manual review | Acceptable but may need tweaks |
| **<50** | Auto-reject | Triggers fallback |

## Phase Structure

### Phase 3A: High Confidence (340 MCQs)
- Graph (154): matplotlib line/bar/scatter plots
- Circuit (148): schemdraw electrical diagrams
- Waves (38): matplotlib sine/cosine waves

### Phase 3B: Medium Confidence (91 MCQs)
- Mechanics (86): Pendulum, inclined plane, pulley, collision
- Optics (5): Ray diagrams, lens/mirror

### Phase 3C: Chemistry Molecules (67 MCQs)
- Uses RDKit for SMILES → SVG
- Falls back to matplotlib structural formulas
- Compound name extraction from question text

### Phase 3D: Low Confidence (80 MCQs)
- Atom (31): Orbital diagrams
- Apparatus (2): Lab equipment
- General (47): Miscellaneous diagrams

### Phase 3E: Biology (TBD MCQs)
- Flowcharts/Cycles: Mermaid.js → SVG
- Anatomy/Structures: Imagen 3 with Gemini Vision labels

## Key Files

### Core Generators
- `src/generators/multi_reference_generator.py` - Main orchestrator
- `src/generators/python_svg_generator.py` - Matplotlib/Schemdraw generation
- `src/generators/chemistry_molecule_generator.py` - RDKit molecule generation
- `src/generators/mechanics_templates.py` - Pre-built physics templates

### Utilities
- `src/utils/data_loader.py` - Load MCQs from predictions.jsonl
- `src/utils/diagram_classifier.py` - Classify diagram type from question text
- `src/utils/svg_quality_checker.py` - Quality scoring
- `src/utils/svg_validator.py` - SVG validation and cleaning

### Scripts
- `scripts/process_phase3a.py` - Phase 3A batch processor
- `scripts/make_svg_responsive.py` - Responsive SVG conversion

## Running the Pipeline

### Setup
```bash
cd /root/image_generation_flexily
source venv/bin/activate
```

### Run Phase 3A
```bash
PYTHONPATH=/root/image_generation_flexily python scripts/process_phase3a.py
```

### Monitor Progress
```bash
# Check progress
/tmp/monitor_phase3a.sh

# Watch live log
tail -f /tmp/phase3a.log

# Streamlit dashboard
streamlit run streamlit_app.py --server.port 8502
```

### Make SVGs Responsive
```bash
python scripts/make_svg_responsive.py output/generated/phase3a
```

## Responsive SVGs

All generated SVGs are made responsive for web/mobile:

### Golden Rule
SVG with `viewBox` + `width="100%"` = perfect scaling

### Conversion Process
1. Remove hardcoded `width="Xpt"` and `height="Ypt"`
2. Add `width="100%"` and `height="auto"`
3. Add `preserveAspectRatio="xMidYMid meet"`
4. Remove `pt` units from font sizes

### Frontend Usage
```html
<div style="max-width: 600px; padding: 10px; margin: 0 auto;">
    <img src="diagram.svg" style="width: 100%; height: auto;">
</div>
```

## API Configuration

```python
# config/settings.py
GCP_PROJECT_ID = "lensproj-444309"
GCP_LOCATION = "us-central1"
MODEL = "gemini-2.5-pro"
```

## Dependencies

```
google-genai        # Gemini 2.5 Pro API
matplotlib          # Graph/chart generation
schemdraw           # Circuit diagrams
rdkit               # Molecular structures
pubchempy           # Compound name → SMILES
mermaid-cli         # Mermaid diagram rendering (npm)
streamlit           # Dashboard
```

## Output Structure

```
output/generated/
├── phase3a/
│   ├── mcq_*.svg              # Generated diagrams (responsive)
│   ├── checkpoint.jsonl       # Progress checkpoint
│   ├── phase3a_results.jsonl  # Final results
│   └── view_results.html      # HTML viewer
├── phase3a_test/              # Test outputs
├── phase3c_test/              # Chemistry test outputs
└── reference/                 # Reference images
```

## Troubleshooting

### Python code generation fails
- Check matplotlib backend is set to 'Agg'
- Ensure schemdraw doesn't call blocking `draw()` method
- Use `d.save('output.svg')` directly

### SVG not responsive
- Run `python scripts/make_svg_responsive.py <directory>`
- Verify `viewBox` attribute exists
- Check `width="100%"` is present

### Low quality score
- For graphs/circuits: Python generation should score 88+
- If quality < 70, check prompt template
- Ensure textbook-style CSS is applied

## Rate Limiting

| Parameter | Value | Reason |
|-----------|-------|--------|
| `rate_limit_delay` | 1.0s | Gemini API quota |
| `max_attempts` | 1 | Primary method is reliable |
| `batch_size` | 10 | Progress checkpoints |
