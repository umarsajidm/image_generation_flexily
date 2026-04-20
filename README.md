# Image Generation for Flexily MCQs

Automated SVG diagram generation for MCQs using AI and chemistry libraries.

## Overview

This standalone repository generates simple, minimalistic SVG diagrams for MCQs in the Flexily database. It operates with **read-only access** to the Flexily database and outputs generated images to files for review before integration.

## Phases

| Phase | Description | Tool | Target |
|-------|-------------|------|--------|
| **0** | Pilot Mode (testing) | All | 30 samples |
| **1** | Chemistry (SMILES → SVG) | RDKit | 758 MCQs |
| **2** | Reference-based | Gemini Vision | ~500-800 MCQs |
| **3** | Pure AI generation | Gemini Flash | ~400+ MCQs |

## Architecture

```
MCQ (no image) → Vector Search → Reference Found? → Generate SVG → Review → Integration
                        ↓
                   No Reference
                        ↓
                   Pure Generation
```

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run pilot mode (30 samples)
python scripts/run_pilot.py

# Launch review UI
streamlit run ui/review_app.py

# Run full phases
python scripts/run_phase1.py
python scripts/run_phase2.py
python scripts/run_phase3.py
```

## Output Structure

```
output/
├── generated/          # Successfully generated SVGs
│   ├── chemistry/
│   ├── reference/
│   └── pure/
├── review/             # Pending review batches
├── failed/             # Persistent failures log
└── logs/               # Processing logs
```

## Configuration

Edit `config/settings.py` for:
- Database connection (read-only)
- GCP project settings
- Batch sizes and retry limits

## Review Process

1. Generated SVGs saved to `output/generated/`
2. Review via Streamlit UI (`ui/review_app.py`)
3. Approve/reject each image
4. Only approved images will be integrated later

## Integration

After review and approval, run integration separately in the main Flexily repository.
