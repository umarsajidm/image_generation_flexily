"""
Biology Diagram Classifier
Classifies biology MCQs into ANATOMY, FLOWCHART, or GRAPH types
for appropriate generation method routing.
"""
import re
from enum import Enum
from dataclasses import dataclass
from typing import List, Optional


class BiologyDiagramType(Enum):
    ANATOMY = "anatomy"
    FLOWCHART = "flowchart"
    GRAPH = "graph"
    CYCLE = "cycle"
    PEDIGREE = "pedigree"
    CELL_STRUCTURE = "cell_structure"
    ORGAN_SYSTEM = "organ_system"
    GENERAL = "general"


@dataclass
class BiologyClassificationResult:
    diagram_type: BiologyDiagramType
    confidence: float
    keywords_matched: List[str]
    suggested_method: str
    description: str


ANATOMY_KEYWORDS = {
    'cell': 4.0,
    'membrane': 4.5,
    'mitochondria': 5.0,
    'mitochondrion': 5.0,
    'nucleus': 4.5,
    'nuclear': 4.0,
    'ribosome': 5.0,
    'golgi': 5.0,
    'endoplasmic': 5.0,
    'reticulum': 4.5,
    'lysosome': 5.0,
    'vacuole': 4.5,
    'chloroplast': 5.0,
    'organelle': 4.5,
    'cytoplasm': 4.0,
    'tissue': 3.5,
    'organ': 3.5,
    'heart': 4.0,
    'kidney': 4.5,
    'liver': 3.5,
    'lung': 3.5,
    'brain': 3.5,
    'neuron': 4.5,
    'synapse': 5.0,
    'synaptic': 5.0,
    'artery': 4.0,
    'vein': 4.0,
    'capillary': 4.5,
    'blood vessel': 4.5,
    'muscle': 3.5,
    'bone': 3.0,
    'skeletal': 3.5,
    'digestive system': 4.5,
    'respiratory system': 4.5,
    'circulatory system': 4.5,
    'nervous system': 4.5,
    'excretory': 4.5,
    'reproductive': 3.5,
    'endocrine': 3.5,
    'gland': 3.5,
    'pituitary': 4.5,
    'thyroid': 4.5,
    'adrenal': 4.5,
    'pancreas': 4.0,
    'bacteria': 4.0,
    'virus': 4.0,
    'pathogen': 3.5,
    'antibody': 4.0,
    'antigen': 4.0,
    'leaf': 3.5,
    'root': 3.0,
    'stem': 3.0,
    'flower': 3.0,
    'stomata': 4.5,
    'xylem': 4.5,
    'phloem': 4.5,
    'cross-section': 5.0,
    'cross section': 5.0,
    'labeled': 3.0,
    'structure labeled': 4.5,
    'diagram shows': 3.5,
    'flatworm': 4.5,
    'protozoa': 4.5,
    'amoeba': 4.5,
    'paramecium': 4.5,
    'euglena': 4.5,
}

FLOWCHART_KEYWORDS = {
    'cycle': 4.5,
    'krebs': 5.0,
    'calvin': 5.0,
    'glycolysis': 5.0,
    'citric acid': 5.0,
    'electron transport': 5.0,
    'food web': 5.0,
    'food chain': 5.0,
    'pedigree': 5.5,
    'inheritance': 3.5,
    'genotype': 3.5,
    'punnett': 5.0,
    'punnet': 5.0,
    'flow': 3.5,
    'pathway': 4.0,
    'metabolic': 4.0,
    'photosynthesis': 3.5,
    'respiration': 3.5,
    'cell cycle': 5.0,
    'mitosis': 4.5,
    'meiosis': 4.5,
    'replication': 4.0,
    'transcription': 4.5,
    'translation': 4.5,
    'protein synthesis': 5.0,
    'energy flow': 4.5,
    'trophic': 4.0,
    'ecosystem': 3.5,
    'carbon cycle': 5.0,
    'nitrogen cycle': 5.0,
    'water cycle': 5.0,
    'oxygen cycle': 5.0,
}

GRAPH_KEYWORDS = {
    'graph': 5.0,
    'plot': 4.5,
    'curve': 4.0,
    'versus': 4.5,
    'vs': 4.0,
    'x-axis': 4.5,
    'y-axis': 4.5,
    'slope': 4.0,
    'intercept': 4.0,
    'relationship between': 4.5,
    'as a function of': 5.0,
    'varies with': 4.5,
    'increasing': 3.0,
    'decreasing': 3.0,
    'action potential': 5.0,
    'threshold': 4.0,
    'depolarization': 4.5,
    'repolarization': 4.5,
    'membrane potential': 5.0,
    'voltage': 3.5,
    'time': 2.5,
    'concentration': 3.0,
    'rate of': 3.5,
    'enzyme activity': 4.5,
    'substrate': 3.5,
    'inhibitor': 3.5,
    'absorption spectrum': 5.0,
    'action spectrum': 5.0,
}

ANATOMY_PHRASES = [
    'cross-section of',
    'cross section of',
    'structure of cell',
    'structure of the cell',
    'labeled diagram',
    'the diagram shows',
    'structure labeled',
    'structures labeled',
    'anatomy of',
    'internal structure',
    'cell membrane',
    'plasma membrane',
    'synaptic junction',
    'synaptic cleft',
    'neuromuscular junction',
    'plant cell',
    'animal cell',
    'blood cell',
    'red blood cell',
    'white blood cell',
]

FLOWCHART_PHRASES = [
    'pedigree chart',
    'pedigree for',
    'punnett square',
    'punnet square',
    'krebs cycle',
    'calvin cycle',
    'cell cycle',
    'food web',
    'food chain',
    'carbon cycle',
    'nitrogen cycle',
    'water cycle',
    'electron transport chain',
    'glycolysis pathway',
    'metabolic pathway',
]

GRAPH_PHRASES = [
    'action potential graph',
    'action potential curve',
    'graph shows',
    'plot of',
    'graph of',
    'versus time',
    'vs time',
    'concentration versus',
    'rate versus',
]


def classify_biology_diagram(
    question_text: str,
    options: dict = None
) -> BiologyClassificationResult:
    """
    Classify a biology MCQ into ANATOMY, FLOWCHART, or GRAPH type.
    
    Returns:
        BiologyClassificationResult with diagram type and suggested method
    """
    text_lower = question_text.lower()
    
    if options:
        for opt in options.values() if isinstance(options, dict) else options:
            if opt:
                text_lower += ' ' + opt.lower()
    
    anatomy_score = 0.0
    anatomy_keywords = []
    for kw, weight in ANATOMY_KEYWORDS.items():
        if kw in text_lower:
            anatomy_score += weight
            anatomy_keywords.append(kw)
    
    flowchart_score = 0.0
    flowchart_keywords = []
    for kw, weight in FLOWCHART_KEYWORDS.items():
        if kw in text_lower:
            flowchart_score += weight
            flowchart_keywords.append(kw)
    
    graph_score = 0.0
    graph_keywords = []
    for kw, weight in GRAPH_KEYWORDS.items():
        if kw in text_lower:
            graph_score += weight
            graph_keywords.append(kw)
    
    for phrase in ANATOMY_PHRASES:
        if phrase in text_lower:
            anatomy_score += 5.0
            if phrase not in anatomy_keywords:
                anatomy_keywords.append(phrase)
    
    for phrase in FLOWCHART_PHRASES:
        if phrase in text_lower:
            flowchart_score += 5.0
            if phrase not in flowchart_keywords:
                flowchart_keywords.append(phrase)
    
    for phrase in GRAPH_PHRASES:
        if phrase in text_lower:
            graph_score += 5.0
            if phrase not in graph_keywords:
                graph_keywords.append(phrase)
    
    scores = {
        BiologyDiagramType.ANATOMY: anatomy_score,
        BiologyDiagramType.FLOWCHART: flowchart_score,
        BiologyDiagramType.GRAPH: graph_score,
    }
    
    max_score = max(scores.values())
    
    if max_score == 0:
        return BiologyClassificationResult(
            diagram_type=BiologyDiagramType.GENERAL,
            confidence=0.0,
            keywords_matched=[],
            suggested_method='python_svg',
            description='General biology diagram - no specific type detected'
        )
    
    if anatomy_score == max_score:
        diagram_type = BiologyDiagramType.ANATOMY
        keywords = anatomy_keywords
        method = 'imagen'
        description = 'Anatomical diagram (cell, organ, tissue structure)'
    elif flowchart_score == max_score:
        diagram_type = BiologyDiagramType.FLOWCHART
        keywords = flowchart_keywords
        method = 'mermaid'
        description = 'Flowchart/cycle diagram (metabolic pathway, pedigree)'
    else:
        diagram_type = BiologyDiagramType.GRAPH
        keywords = graph_keywords
        method = 'matplotlib'
        description = 'Graph/plot (action potential, concentration vs time)'
    
    confidence = min(max_score / 15.0, 1.0)
    
    return BiologyClassificationResult(
        diagram_type=diagram_type,
        confidence=confidence,
        keywords_matched=keywords[:10],
        suggested_method=method,
        description=description
    )


def get_biology_generation_method(question_text: str, options: dict = None) -> str:
    """
    Quick helper to get the suggested generation method for a biology MCQ.
    
    Returns:
        One of: 'imagen', 'mermaid', 'matplotlib', 'python_svg'
    """
    result = classify_biology_diagram(question_text, options)
    return result.suggested_method


if __name__ == "__main__":
    test_questions = [
        "The diagram shows the synaptic junction at a muscle endplate. Which chemical substances were released?",
        "Based on the provided pedigree for hemophilia, determine the genotype of individual 5.",
        "At which point on the action potential graph is the membrane most permeable to sodium ions?",
        "Identify the structure labeled X in the plant cell diagram.",
        "The Krebs cycle occurs in which part of the cell?",
    ]
    
    for q in test_questions:
        result = classify_biology_diagram(q)
        print(f"\nQ: {q[:60]}...")
        print(f"  Type: {result.diagram_type.value}")
        print(f"  Method: {result.suggested_method}")
        print(f"  Keywords: {result.keywords_matched[:3]}")
