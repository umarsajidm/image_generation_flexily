# Phase 3B Implementation Plan - Hybrid Mechanics/Optics Generation

## Overview

**Goal**: Generate SVG diagrams for 91 Mechanics + Optics MCQs using a hybrid soft-template approach with few-shot code examples.

**Expected Success Rate**: 85-95% (vs 45.9% circuits in Phase 3A)

---

## Current Status

- **Phase 3A**: ✅ COMPLETE - 340 MCQs processed, 75.4% success rate
  - Graph: 98.1% (151/154)
  - Circuit: 45.9% (68/148) - struggled with XML parsing
  - Waves: 100% (38/38)

- **Phase 3B**: ⏳ READY TO IMPLEMENT - 91 MCQs
  - Mechanics: 86 MCQs
  - Optics: 5 MCQs

---

## Architecture

```
MCQ Input
    ↓
diagram_classifier.py → DiagramType.MECHANICS or DiagramType.OPTICS
    ↓
┌─────────────────────────────────────────────────────────────┐
│  mechanics_router.py (NEW)                                  │
│  classify_mechanics_subtype() → Pendulum | Collision | etc.│
└─────────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────────┐
│  mechanics_prompts.py (NEW)                                 │
│  Maps subtype → Few-shot code example                       │
│  Includes: aspect ratio, ax.annotate, tight_layout          │
└─────────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────────┐
│  python_svg_generator.py (MODIFY)                           │
│  Gemini generates adapted Python code                       │
│  Execute in venv → SVG                                      │
└─────────────────────────────────────────────────────────────┘
    ↓ (if fails)
┌─────────────────────────────────────────────────────────────┐
│  Raw SVG Fallback (Gemini direct)                           │
└─────────────────────────────────────────────────────────────┘
    ↓
SVG Output + Quality Score
```

---

## File Changes

### NEW Files to Create

| File | Purpose | Lines |
|------|---------|-------|
| `src/utils/mechanics_router.py` | Subtype classification via keyword matching | ~80 |
| `src/generators/mechanics_prompts.py` | Few-shot code examples for each subtype | ~450 |
| `scripts/process_phase3b.py` | Batch processor for mechanics/optics | ~280 |

### EXISTING Files to Modify

| File | Changes Needed |
|------|----------------|
| `src/generators/python_svg_generator.py` | Add subtype parameter, prompt selection logic, markdown cleanup |
| `src/generators/multi_reference_generator.py` | Add mechanics subtype routing |
| `streamlit_app.py` | Add Phase 3B monitoring tab |

### FILES to Archive

| File | Action |
|------|--------|
| `src/generators/mechanics_templates.py` | Move to `legacy/` folder (keep for reference) |

---

## Mechanics MCQ Breakdown

| Subtype | Count | Template Available |
|---------|-------|-------------------|
| Pendulum | 12 | ✅ Few-shot example |
| Inclined Plane | 2 | ✅ Few-shot example |
| Pulley | 0 | ✅ Few-shot example (adapt) |
| Collision | 4 | ✅ Few-shot example |
| Projectile | 2 | ✅ Few-shot example |
| Spring | 3 | ✅ Few-shot example |
| Torque | ~15 | ✅ Few-shot example |
| Generic | ~48 | ✅ Generic fallback |

**Templates cover**: 18 MCQs (21%) with specific examples
**Gemini adapts**: 68 MCQs (79%) using generic + specific examples

---

## Technical Gotchas to Handle

### 1. Markdown Code Block Cleanup
Gemini wraps output in markdown ticks even when told not to:
```python
# In python_svg_generator.py, clean the response:
clean_code = raw_response.replace("```python\n", "").replace("```python", "").replace("```", "").strip()
```

### 2. All-Zero Edge Case in Router
If no keywords match, `max()` returns first key. Already handled:
```python
return best_subtype if scores[best_subtype] > 0.5 else MechanicsSubtype.GENERIC
```

### 3. Matplotlib Backend
All examples include `matplotlib.use('Agg')` at the very top for headless execution. Parser must not strip this.

---

## Implementation Steps

### Phase 1: Create Core Files (~1 hour)

#### Step 1.1: Create `src/utils/mechanics_router.py`

```python
"""Mechanics diagram subtype classification."""
from enum import Enum

class MechanicsSubtype(Enum):
    PENDULUM = "pendulum"
    INCLINED_PLANE = "inclined_plane"
    PULLEY = "pulley"
    COLLISION = "collision"
    PROJECTILE = "projectile"
    SPRING = "spring"
    TORQUE = "torque"
    GENERIC = "generic"

# Keyword patterns with confidence weights
SUBTYPE_PATTERNS = {
    MechanicsSubtype.PENDULUM: [
        ('pendulum', 1.0), ('swing', 0.8), ('bob', 0.7),
        ('oscillat', 0.5), ("simple pendulum", 1.0)
    ],
    MechanicsSubtype.INCLINED_PLANE: [
        ('inclined', 1.0), ('slope', 0.8), ('ramp', 0.8),
        ('wedge', 0.9)
    ],
    MechanicsSubtype.PULLEY: [
        ('pulley', 1.0), ('atwood', 1.0),
        ('block.*rope', 0.7), ('tension.*string', 0.6)
    ],
    MechanicsSubtype.COLLISION: [
        ('collid', 1.0), ('collision', 1.0), ('impact', 0.8),
        ('strikes', 0.7), ('elastic', 0.6), ('inelastic', 0.9)
    ],
    MechanicsSubtype.PROJECTILE: [
        ('projectile', 1.0), ('thrown', 0.7), ('launch', 0.8),
        ('parabolic', 0.9), ('trajectory', 0.8)
    ],
    MechanicsSubtype.SPRING: [
        ('spring', 1.0), ('oscillat.*mass', 0.7),
        ('hook', 0.6), ('compress', 0.5)
    ],
    MechanicsSubtype.TORQUE: [
        ('torque', 1.0), ('pivot', 0.8), ('moment', 0.7),
        ('lever', 0.8), ('fulcrum', 0.9), ('rotat', 0.6),
        ('beam', 0.5), ('rod', 0.4)
    ],
}

def classify_mechanics_subtype(question: str) -> MechanicsSubtype:
    q_lower = question.lower()
    scores = {subtype: 0.0 for subtype in MechanicsSubtype}
    
    for subtype, patterns in SUBTYPE_PATTERNS.items():
        for keyword, weight in patterns:
            if keyword in q_lower:
                scores[subtype] += weight
    
    best_subtype = max(scores, key=scores.get)
    return best_subtype if scores[best_subtype] > 0.5 else MechanicsSubtype.GENERIC
```

#### Step 1.2: Create `src/generators/mechanics_prompts.py`

**Contains few-shot code examples for each subtype.**

Key examples:
- `PENDULUM_CODE_EXAMPLE` - Pivot, bob, angle arc, labeled points X/Y
- `INCLINED_PLANE_CODE_EXAMPLE` - Angle, block with forces (mg, N)
- `COLLISION_CODE_EXAMPLE` - Two objects with velocity arrows
- `SPRING_CODE_EXAMPLE` - Zig-zag spring, mass, displacement
- `TORQUE_CODE_EXAMPLE` - Beam, pivot, force, curved rotation arrow
- `PROJECTILE_CODE_EXAMPLE` - Parabola trajectory, launch angle
- `GENERIC_MECHANICS_CODE_EXAMPLE` - Block, force arrow, labeled point
- `OPTICS_CODE_EXAMPLE` - Lens, principal axis, focal points, ray tracing

**ALL examples MUST include**:
1. `matplotlib.use('Agg')` at top
2. `ax.set_aspect('equal')` after creating axes
3. `ax.annotate()` for vectors (NOT `plt.arrow()`)
4. `plt.tight_layout()` before saving
5. `plt.savefig('output.svg')`

#### Step 1.3: Create `scripts/process_phase3b.py`

Based on `process_phase3a.py` with:
- Filter for `mechanics` + `optics` diagram types
- Use `classify_mechanics_subtype()` for routing
- Output to `phase3b/` directory
- Same checkpoint/resume functionality

---

### Phase 2: Modify Existing Files (~30 min)

#### Step 2.1: Modify `src/generators/python_svg_generator.py`

1. Add imports:
```python
from src.utils.mechanics_router import classify_mechanics_subtype, MechanicsSubtype
from src.generators.mechanics_prompts import get_mechanics_code_example, get_optics_code_example
```

2. Add `mechanics_subtype` parameter to `generate()` method

3. Add `_build_mechanics_prompt()` method

4. Add markdown cleanup:
```python
code = code.replace("```python\n", "").replace("```python", "").replace("```", "").strip()
```

#### Step 2.2: Modify `src/generators/multi_reference_generator.py`

1. Add import:
```python
from src.utils.mechanics_router import classify_mechanics_subtype
```

2. In `_try_python_fallback()`, add mechanics routing

#### Step 2.3: Modify `streamlit_app.py`

Add Phase 3B tab similar to Phase 3A tab.

---

### Phase 3: Archive Legacy Files (~5 min)

```bash
mkdir -p /root/image_generation_flexily/legacy
mv /root/image_generation_flexily/src/generators/mechanics_templates.py \
   /root/image_generation_flexily/legacy/
```

---

### Phase 4: Testing (~30 min)

#### Test 1: Unit Test Router
```bash
cd /root/image_generation_flexily
./venv/bin/python -c "
from src.utils.mechanics_router import classify_mechanics_subtype
test_cases = [
    ('A simple pendulum is released from point X', 'pendulum'),
    ('A block slides down an inclined plane', 'inclined_plane'),
    ('Two objects collide on a frictionless surface', 'collision'),
    ('A projectile is launched at 45 degrees', 'projectile'),
    ('A spring is compressed by 0.5m', 'spring'),
    ('A torque is applied to a rod at the pivot', 'torque'),
    ('What is the work done by the force', 'generic'),
]
for question, expected in test_cases:
    result = classify_mechanics_subtype(question)
    status = '✓' if result.value == expected else '✗'
    print(f'  {status} {result.value:15s} (expected: {expected})')
"
```

#### Test 2: Single MCQ Generation
Test pendulum MCQ generation with new prompts.

#### Test 3: Integration Test (5 MCQs)
```bash
./venv/bin/python scripts/process_phase3b.py --test-limit 5
```

---

### Phase 5: Full Batch Processing (~45 min)

```bash
cd /root/image_generation_flexily
tmux new-session -d -s phase3b "./venv/bin/python -u scripts/process_phase3b.py 2>&1 | tee logs/phase3b.log"
```

---

## Success Metrics

| Metric | Target | How to Measure |
|--------|--------|----------------|
| Mechanics Success Rate | 85-95% | success_count / 86 |
| Optics Success Rate | 90-100% | success_count / 5 |
| Average Quality Score | > 85 | Mean of successful MCQs |
| Total Failed | < 15 | Count of failed entries |

---

## Timeline

| Phase | Task | Duration |
|-------|------|----------|
| 1 | Create new files | ~1 hour |
| 2 | Modify existing files | ~30 min |
| 3 | Archive legacy | ~5 min |
| 4 | Testing | ~30 min |
| 5 | Full batch processing | ~45 min |
| 6 | Review and document | ~15 min |

**Total**: ~3 hours

---

## Output Locations

- Checkpoint: `/root/image_generation_flexily/output/generated/phase3b/checkpoint.jsonl`
- SVGs: `/root/image_generation_flexily/output/generated/phase3b/*.svg`
- Logs: `/root/image_generation_flexily/logs/phase3b.log`

---

## Rollback Plan

If Phase 3B fails:
1. Phase 3A checkpoint is unchanged (separate directory)
2. Phase 3B output is in `phase3b/` directory
3. Can revert to Phase 3A-style by removing subtype routing
4. Legacy templates preserved in `legacy/` folder

---

## Key Code Snippets

### Few-Shot Example Template (all must follow)
```python
EXAMPLE = '''
import matplotlib
matplotlib.use('Agg')  # CRITICAL: headless backend
import matplotlib.pyplot as plt
import numpy as np

fig, ax = plt.subplots(figsize=(8, 6))
ax.set_aspect('equal')  # CRITICAL: prevents oval distortion
ax.axis('off')

# ... diagram code ...

# Use ax.annotate for vectors (NOT plt.arrow)
ax.annotate('', xy=(end_x, end_y), xytext=(start_x, start_y),
            arrowprops=dict(arrowstyle='->', color='black', lw=2))

plt.tight_layout()  # CRITICAL: prevents label cutoff
plt.savefig('output.svg')
'''
```

### Prompt Builder
```python
def _build_mechanics_prompt(self, question: str, code_example: str) -> str:
    return f"""You are an expert physics diagram generator using matplotlib.

KEY RULES:
1. Always use ax.set_aspect('equal')
2. Use ax.annotate() for vectors, NOT plt.arrow()
3. Label ALL points mentioned in the question
4. Use plt.tight_layout() before saving

EXAMPLE CODE:
{code_example}

Question: {question}

Output ONLY the Python code."""
```

---

*Status: Ready for implementation after session compact*
