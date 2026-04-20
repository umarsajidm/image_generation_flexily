# Detailed Implementation Plan

## Project Overview

Standalone repository for generating SVG images for Flexily MCQs. Operates with **read-only** access to the Flexily database.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                  IMAGE GENERATION PIPELINE                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   ┌─────────────┐                                                  │
│   │ Flexily DB  │  (READ ONLY)                                     │
│   │   MCQs      │──────────────────────┐                           │
│   │   Chunks    │                      │                           │
│   └─────────────┘                      │                           │
│                                        ▼                           │
│   ┌──────────────────────────────────────────────────────────┐    │
│   │              JSONL BATCH PROCESSOR                        │    │
│   │  1 query = 1 MCQ processed                                │    │
│   │  Retry logic: 3 attempts per failure                      │    │
│   └──────────────────────────────────────────────────────────┘    │
│                      │                                             │
│        ┌─────────────┼─────────────┐                              │
│        ▼             ▼             ▼                              │
│   ┌─────────┐  ┌──────────┐  ┌──────────┐                        │
│   │ PHASE 1 │  │ PHASE 2  │  │ PHASE 3  │                        │
│   │Chemistry│  │Reference │  │Pure AI   │                        │
│   │(RDKit)  │  │(Gemini)  │  │(Gemini)  │                        │
│   └─────────┘  └──────────┘  └──────────┘                        │
│        │             │             │                              │
│        └─────────────┴─────────────┘                              │
│                      │                                             │
│                      ▼                                             │
│   ┌──────────────────────────────────────────────────────────┐    │
│   │              OUTPUT FILES (for review)                    │    │
│   │  output/generated/{chemistry,reference,pure}/*.svg       │    │
│   │  output/pilot/pilot_results.jsonl                        │    │
│   │  output/failed/phase*_failures.jsonl                     │    │
│   └──────────────────────────────────────────────────────────┘    │
│                      │                                             │
│                      ▼                                             │
│   ┌──────────────────────────────────────────────────────────┐    │
│   │              REVIEW UI (Streamlit)                        │    │
│   │  - Display MCQ question + options                         │    │
│   │  - Show generated SVG                                     │    │
│   │  - Approve/Reject                                         │    │
│   │  - Export approved items                                  │    │
│   └──────────────────────────────────────────────────────────┘    │
│                      │                                             │
│                      ▼                                             │
│   ┌──────────────────────────────────────────────────────────┐    │
│   │              INTEGRATION (later)                          │    │
│   │  Update Flexily DB with approved SVGs                    │    │
│   └──────────────────────────────────────────────────────────┘    │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Phase Details

### Phase 0: Pilot Mode

**Purpose:** Test pipeline with sample data before full run

**Steps:**
1. Generate 10 sample chemistry molecules using RDKit
2. Save results to `output/pilot/pilot_results.jsonl`
3. Launch review UI to verify quality
4. Adjust prompts/styling if needed
5. Approve or iterate

**Command:**
```bash
python scripts/run_pilot.py
streamlit run ui/review_app.py
```

---

### Phase 1: Chemistry (SMILES → SVG)

**Target:** 758 MCQs with SMILES strings

**Process:**
```
SMILES string → RDKit.MolFromSmiles() → 2D Coordinates → MolToSVG → Optimize
```

**Source:** `/root/gcp_app_for_mcqs/finished_mcqs_output/v3/predictions.jsonl`

**Implementation:**
```python
from rdkit import Chem
from rdkit.Chem import Draw, AllChem

def smiles_to_svg(smiles: str) -> str:
    mol = Chem.MolFromSmiles(smiles)
    AllChem.Compute2DCoords(mol)
    drawer = Draw.MolDraw2DSVG(400, 250)
    drawer.DrawMolecule(mol)
    drawer.FinishDrawing()
    return drawer.GetDrawingText()
```

**JSONL Format (input):**
```json
{"mcq_id": "uuid", "smiles": "CCO", "question_text": "..."}
```

**JSONL Format (output):**
```json
{"mcq_id": "uuid", "phase": 1, "svg": "<svg>...</svg>", "success": true}
```

---

### Phase 2: Reference-Based Generation

**Target:** ~500-800 MCQs with matching textbook content

**Process:**
```
MCQ Question → Embedding → Vector Search (textbook_chunks) → Find Image Path
     ↓
Load Reference Image (PNG)
     ↓
Gemini Vision: "Generate minimalistic SVG based on reference + question"
     ↓
Receive SVG → Validate → Save
```

**Vector Search Query:**
```sql
SELECT id, image_paths, 1 - (embedding <=> query_embedding) as similarity
FROM textbook_chunks
WHERE has_image = true
  AND similarity >= 0.75
ORDER BY similarity DESC
LIMIT 5
```

**Prompt Template:**
```
You are creating educational diagrams. Analyze the reference image and MCQ question.

REFERENCE IMAGE: [attached PNG]

MCQ QUESTION: {question_text}
SUBJECT: {subject}

Requirements:
- SIMPLE, MINIMALISTIC diagram
- Original design (NOT a copy)
- Clean lines, minimal colors
- viewBox="0 0 400 250"
- Readable on mobile

Output ONLY SVG code.
```

---

### Phase 3: Pure AI Generation

**Target:** ~400+ MCQs without reference matches

**Process:**
```
MCQ Question → Detect Diagram Type → Generate Context → Gemini Flash → SVG
```

**Diagram Type Detection:**
```python
DIAGRAM_TYPES = {
    'circuit': ['circuit', 'resistor', 'capacitor', 'battery'],
    'graph': ['graph', 'plot', 'curve', 'axis'],
    'wave': ['wave', 'frequency', 'amplitude'],
    'cell': ['cell', 'membrane', 'nucleus'],
    'vector': ['force', 'vector', 'direction'],
    'geometry': ['angle', 'triangle', 'circle'],
}
```

**Prompt Template:**
```
Create a SIMPLE educational SVG diagram for this MCQ:

QUESTION: {question_text}
SUBJECT: {subject}
DIAGRAM TYPE: {diagram_type}

Requirements:
- Minimalistic style
- Clean black lines
- Clear labels (font-size >= 14)
- Max 400x250 pixels
- Suitable for mobile

Output ONLY SVG code.
```

---

## JSONL Batch Processing

### Input Format (per line)
```json
{
  "mcq_id": "uuid-string",
  "question_text": "Full question text...",
  "subject": "Physics",
  "chapter": "Current Electricity",
  "smiles": "CCO",
  "chapter_id": "uuid-or-null"
}
```

### Output Format (per line)
```json
{
  "mcq_id": "uuid-string",
  "phase": 1,
  "source_type": "chemistry",
  "svg": "<svg>...</svg>",
  "error": null,
  "attempts": 1,
  "generated_at": "2026-04-20T20:00:00Z",
  "reference_image": null,
  "smiles": "CCO",
  "similarity_score": null
}
```

---

## Retry & Error Handling

### Retry Logic
```python
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 5

for attempt in range(MAX_RETRIES):
    result = generate(...)
    if success:
        return result
    log_failure(attempt, error)
    sleep(RETRY_DELAY_SECONDS)

# After 3 failures, log to output/failed/
log_persistent_failure(mcq_id, error, all_attempts)
```

### Failure Logging

File: `output/failed/phase1_failures.jsonl`
```json
{
  "mcq_id": "uuid",
  "phase": 1,
  "error": "Failed to parse SMILES",
  "attempts": [
    {"attempt": 1, "error": "...", "timestamp": "..."},
    {"attempt": 2, "error": "...", "timestamp": "..."},
    {"attempt": 3, "error": "...", "timestamp": "..."}
  ],
  "status": "failed_after_retries"
}
```

---

## SVG Guidelines

### Dimensions & ViewBox
```xml
<svg viewBox="0 0 400 250" xmlns="http://www.w3.org/2000/svg">
```

### Color Palette
| Color | Hex | Use |
|-------|-----|-----|
| Primary | #0071e3 | Physics, circuits |
| Secondary | #34c759 | Biology, positive |
| Accent | #ff9500 | Chemistry, energy |
| Highlight | #5856d6 | Math, emphasis |
| Dark | #1d1d1f | Text, lines |
| Light | #f5f5f7 | Background |

### Style Rules
1. **No gradients** - Solid fills only
2. **No shadows** - Flat design
3. **Minimal colors** - Max 3 colors + black/white
4. **Simple shapes** - Lines, circles, rectangles
5. **Readable text** - Font size >= 14px
6. **Responsive** - Always use viewBox

---

## Review UI Features

### Main View
- List all generated items
- Filter by status (success/failed)
- Filter by phase

### Item Display
- MCQ question text
- MCQ options (A, B, C, D)
- Subject & Chapter
- Generated SVG (rendered)
- SVG code (expandable)
- Source info (SMILES, reference image, etc.)

### Actions
- **Approve** - Mark for integration
- **Reject** - Mark for retry/review
- **Export Approved** - Save approved items
- **Export Failed** - Save failed items for retry

---

## Commands Reference

```bash
# Activate virtual environment
cd /root/image_generation_flexily
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run pilot mode
python scripts/run_pilot.py

# Launch review UI
streamlit run ui/review_app.py

# Run Phase 1 (Chemistry)
python scripts/run_phase1.py --batch-size 100

# Run Phase 2 (Reference-based)
python scripts/run_phase2.py --batch-size 50

# Run Phase 3 (Pure AI)
python scripts/run_phase3.py --batch-size 50
```

---

## File Structure

```
/root/image_generation_flexily/
├── README.md
├── PLAN.md
├── requirements.txt
├── config/
│   ├── __init__.py
│   ├── settings.py
│   └── prompts.py
├── src/
│   ├── __init__.py
│   ├── main.py
│   ├── database/
│   │   ├── __init__.py
│   │   └── connection.py
│   ├── generators/
│   │   ├── __init__.py
│   │   ├── chemistry_generator.py
│   │   ├── reference_generator.py
│   │   └── pure_generator.py
│   ├── matchers/
│   │   ├── __init__.py
│   │   └── vector_matcher.py
│   └── utils/
│       └── __init__.py
├── scripts/
│   ├── run_pilot.py
│   ├── run_phase1.py
│   ├── run_phase2.py
│   └── run_phase3.py
├── ui/
│   └── review_app.py
├── output/
│   ├── generated/
│   │   ├── chemistry/
│   │   ├── reference/
│   │   └── pure/
│   ├── pilot/
│   ├── review/
│   ├── failed/
│   └── logs/
└── tests/
    └── samples/
```

---

## Integration Plan (After Review)

1. **Export approved items** from review UI
2. **Run integration script** in main Flexily repository
3. **Update MCQs** with approved SVGs:
   ```sql
   UPDATE mcqs 
   SET question_image_url = $1,
       image_metadata = jsonb_build_object(
           'generated_at', $2,
           'generator', $3,
           'review_status', 'approved'
       )
   WHERE id = $4
   ```
4. **Verify** in admin UI
5. **Deploy** changes

---

## Cost Estimation

| Phase | MCQs | Method | Cost/MCQ | Total |
|-------|------|--------|----------|-------|
| 1 | 758 | RDKit (local) | $0 | $0 |
| 2 | ~600 | Gemini Vision | ~$0.002 | ~$1.20 |
| 3 | ~400 | Gemini Flash | ~$0.002 | ~$0.80 |
| **Total** | ~1,758 | - | - | **~$2-3** |

---

## Timeline

| Day | Task |
|-----|------|
| 1 | Setup, pilot mode, review Phase 1 samples |
| 2 | Run Phase 1 full, start Phase 2 |
| 3 | Complete Phase 2, start Phase 3 |
| 4 | Complete Phase 3, full review |
| 5 | Integration planning |
