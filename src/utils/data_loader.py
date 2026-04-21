"""
Data loader for predictions.jsonl file.
Extracts MCQs with metadata from GCP predictions output.
"""
import json
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Generator
from dataclasses import dataclass, asdict


PREDICTIONS_FILE = Path("/root/gcp_app_for_mcqs/finished_mcqs_output/v3/predictions.jsonl")


@dataclass
class MCQData:
    mcq_id: str
    question_text: str
    options: Dict[str, str]
    correct_answer_key: str
    explanation: str
    requires_manual_image: bool
    smiles_string: Optional[str]
    svg_diagram: Optional[str]
    source_file: Optional[str]
    source_page: Optional[int]
    subject: Optional[str]
    mcq_index: int


def generate_mcq_id(source_file: str, mcq_index: int) -> str:
    """Generate a unique ID for an MCQ."""
    clean_name = re.sub(r'[^a-zA-Z0-9]', '_', source_file)
    return f"mcq_{clean_name[:50]}_{mcq_index}"


def extract_subject_from_filename(filename: str) -> Optional[str]:
    """Extract subject from filename."""
    filename_lower = filename.lower()
    
    if 'biology' in filename_lower:
        return 'biology'
    elif 'chemistry' in filename_lower:
        return 'chemistry'
    elif 'physics' in filename_lower:
        return 'physics'
    elif 'math' in filename_lower or 'mathematics' in filename_lower:
        return 'math'
    elif 'english' in filename_lower:
        return 'english'
    
    return None


def extract_page_from_text(text: str) -> Optional[int]:
    """Extract page number from explanation text."""
    match = re.search(r'page\s*(\d+)', text, re.IGNORECASE)
    if match:
        return int(match.group(1))
    return None


def load_all_mcqs() -> List[MCQData]:
    """Load all MCQs from predictions file."""
    return list(iter_mcqs())


def iter_mcqs() -> Generator[MCQData, None, None]:
    """Iterate over all MCQs in predictions file."""
    global_mcq_index = 0
    
    with open(PREDICTIONS_FILE, 'r') as f:
        for line in f:
            data = json.loads(line)
            
            finish_reason = data.get('response', {}).get('candidates', [{}])[0].get('finishReason', '')
            if finish_reason != 'STOP':
                continue
            
            text = data.get('response', {}).get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '')
            if not text:
                continue
            
            source_file = None
            parts = data.get('request', {}).get('contents', [{}])[0].get('parts', [])
            for part in parts:
                if part.get('fileData'):
                    file_uri = part['fileData'].get('fileUri', '')
                    if file_uri:
                        source_file = file_uri.split('/')[-1]
                    break
            
            subject = extract_subject_from_filename(source_file or '')
            
            try:
                mcqs = json.loads(text)
                if not isinstance(mcqs, list):
                    continue
                
                for mcq in mcqs:
                    global_mcq_index += 1
                    
                    mcq_data = MCQData(
                        mcq_id=generate_mcq_id(source_file or 'unknown', global_mcq_index),
                        question_text=mcq.get('question_text', ''),
                        options=mcq.get('options', {}),
                        correct_answer_key=mcq.get('correct_answer_key', ''),
                        explanation=mcq.get('explanation', ''),
                        requires_manual_image=mcq.get('requires_manual_image', False),
                        smiles_string=mcq.get('smiles_string'),
                        svg_diagram=mcq.get('svg_diagram'),
                        source_file=source_file,
                        source_page=extract_page_from_text(mcq.get('explanation', '')),
                        subject=subject,
                        mcq_index=global_mcq_index
                    )
                    yield mcq_data
                    
            except json.JSONDecodeError:
                continue


def get_mcqs_with_smiles() -> List[MCQData]:
    """Get MCQs that have SMILES strings (Phase 1)."""
    return [mcq for mcq in iter_mcqs() if mcq.smiles_string]


def get_mcqs_needing_images() -> List[MCQData]:
    """Get MCQs that need manual images (Phase 2/3)."""
    return [mcq for mcq in iter_mcqs() if mcq.requires_manual_image and not mcq.smiles_string]


def get_mcqs_without_svg() -> List[MCQData]:
    """Get MCQs that don't have SVG diagrams yet."""
    return [mcq for mcq in iter_mcqs() if not mcq.svg_diagram]


def save_mcqs_to_jsonl(mcqs: List[MCQData], output_path: Path):
    """Save MCQs to JSONL file."""
    with open(output_path, 'w') as f:
        for mcq in mcqs:
            f.write(json.dumps(asdict(mcq)) + '\n')


if __name__ == "__main__":
    print("Loading MCQs from predictions file...")
    
    all_mcqs = load_all_mcqs()
    smiles_mcqs = get_mcqs_with_smiles()
    needing_images = get_mcqs_needing_images()
    
    print(f"Total MCQs: {len(all_mcqs)}")
    print(f"With SMILES (Phase 1): {len(smiles_mcqs)}")
    print(f"Needing images (Phase 2/3): {len(needing_images)}")
    
    if smiles_mcqs:
        print(f"\nSample SMILES MCQ:")
        print(json.dumps(asdict(smiles_mcqs[0]), indent=2)[:500])
