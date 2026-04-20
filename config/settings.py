"""
Configuration settings for image generation pipeline.
"""
import os
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
OUTPUT_DIR = PROJECT_ROOT / "output"
GENERATED_DIR = OUTPUT_DIR / "generated"
REVIEW_DIR = OUTPUT_DIR / "review"
FAILED_DIR = OUTPUT_DIR / "failed"
LOGS_DIR = OUTPUT_DIR / "logs"

# Database (read-only connection to Flexily)
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/flexily"
)

# GCP Configuration
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID", "flexily-data-processing")
GCP_LOCATION = os.getenv("GCP_LOCATION", "europe-north1")
GEMINI_MODEL = "gemini-1.5-flash"

# Batch Processing
BATCH_SIZE = 50
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 5

# Pilot Mode
PILOT_SAMPLE_SIZE = 10  # per phase

# SVG Guidelines
SVG_MAX_WIDTH = 400
SVG_MAX_HEIGHT = 250
SVG_MAX_SIZE_BYTES = 15000

# Color palette for diagrams
COLOR_PALETTE = {
    'primary': '#0071e3',
    'secondary': '#34c759',
    'accent': '#ff9500',
    'highlight': '#5856d6',
    'dark': '#1d1d1f',
    'light': '#f5f5f7',
    'white': '#ffffff',
    'black': '#000000',
}

# Vector search thresholds
SIMILARITY_THRESHOLD_HIGH = 0.85
SIMILARITY_THRESHOLD_LOW = 0.70
