# Image Generation Scripts

## Overview

Scripts for processing MCQs through the image generation pipeline.

## Scripts

### `process_phase3a.py`

Full batch processor for Phase 3A (Graph, Circuit, Waves).

**Usage:**
```bash
PYTHONPATH=/root/image_generation_flexily python scripts/process_phase3a.py
```

**Features:**
- Checkpoint support (resumes from last processed MCQ)
- Rate limiting for API quotas
- Quality scoring with auto-accept/reject
- Responsive SVG conversion

**Output:**
- `output/generated/phase3a/mcq_*.svg` - Generated diagrams
- `output/generated/phase3a/checkpoint.jsonl` - Progress tracking
- `output/generated/phase3a/view_results.html` - HTML viewer

---

### `make_svg_responsive.py`

Convert SVGs to responsive format for web/mobile.

**Usage:**
```bash
# Convert specific directory
python scripts/make_svg_responsive.py output/generated/phase3a

# Verify responsiveness
python scripts/make_svg_responsive.py output/generated/phase3a
```

**What it does:**
1. Removes hardcoded `width` and `height` attributes
2. Adds `width="100%"` and `height="auto"`
3. Adds `preserveAspectRatio="xMidYMid meet"`
4. Removes `pt` units from font sizes

**Golden Rule:** SVG with `viewBox` + responsive width = perfect scaling

---

### `test_phase3a.py`

Test script for validating Phase 3A before full batch processing.

**Usage:**
```bash
PYTHONPATH=/root/image_generation_flexily python scripts/test_phase3a.py
```

**Output:**
- `output/generated/phase3a_test/test_results.json` - Test results
- `output/generated/phase3a_test/view_results.html` - HTML viewer

---

## Monitoring

### Live Monitoring Script

```bash
/tmp/monitor_phase3a.sh
```

Shows:
- Process status
- Checkpoint count
- SVG count
- Responsive conversion status
- Latest log entries

### Streamlit Dashboard

```bash
streamlit run streamlit_app.py --server.port 8502
```

Features:
- Real-time progress tracking
- Quality metrics by diagram type
- SVG preview with responsive display
- Filter by success/failure

---

## Adding New Phases

To create a new phase processor:

1. Copy `process_phase3a.py` to `process_phase3{X}.py`
2. Update diagram types in `get_mcqs_by_type()`
3. Adjust prompts in `python_svg_generator.py` if needed
4. Update output directory paths

Template:
```python
by_type = {
    'mechanics': [],
    'optics': [],
}
```

---

## Checkpoint Format

Each line in `checkpoint.jsonl`:
```json
{
    "mcq_id": "mcq_KIPS_PHYSICS_PRACTICE_BOOK_part2_pdf_211",
    "question_text": "Which graph correctly represents...",
    "subject": "physics",
    "diagram_type": "graph",
    "generation_method": "python_code",
    "quality_score": 88.75,
    "success": true,
    "svg_path": "/root/image_generation_flexily/output/generated/phase3a/mcq_*.svg",
    "error": null,
    "generated_at": "2026-04-22T18:00:00.000000"
}
```
