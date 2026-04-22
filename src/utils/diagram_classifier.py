"""
Diagram classifier - detects what type of diagram an MCQ needs.
Used to route to appropriate generation method (raw SVG, schemdraw, matplotlib, etc.)
"""
import re
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass
from enum import Enum


class DiagramType(Enum):
    CIRCUIT = "circuit"
    GRAPH = "graph"
    MECHANICS = "mechanics"
    OPTICS = "optics"
    WAVES = "waves"
    ATOM = "atom"
    APPARATUS = "apparatus"
    MOLECULE = "molecule"
    GEOMETRY = "geometry"
    BIOLOGY = "biology"
    GENERAL = "general"


@dataclass
class ClassificationResult:
    diagram_type: DiagramType
    confidence: float
    keywords_matched: List[str]
    suggested_method: str
    description: str


DIAGRAM_PATTERNS = {
    DiagramType.CIRCUIT: {
        'keywords': {
            'circuit': 3.5, 'resistor': 3.0, 'capacitor': 3.0, 'battery': 3.0,
            'voltage': 2.5, 'current': 2.5, 'resistance': 2.5, 'ohm': 2.5,
            'ampere': 2.5, 'volt': 2.5, 'series': 2.0, 'parallel': 2.0,
            'electric circuit': 3.5, 'dc circuit': 3.5, 'ac circuit': 3.5,
            'emf': 2.5, 'ammeter': 3.0, 'voltmeter': 3.0,
            'galvanometer': 3.0, 'potentiometer': 3.0, 'wheatstone': 3.0,
            'kirchhoff': 2.5, 'power supply': 2.5, 'inductor': 3.0,
            'diode': 3.0, 'transistor': 3.0, 'rc circuit': 3.5, 'rl circuit': 3.5,
            'battery cell': 4.0, 'electrochemical cell': 4.0,
        },
        'method': 'schemdraw',
        'description': 'Electrical circuit diagram'
    },
    DiagramType.GRAPH: {
        'keywords': {
            'graph': 4.0, 'plot': 3.5, 'curve': 3.0, 'versus': 4.0, 'vs': 4.0,
            'x-axis': 3.5, 'y-axis': 3.5, 'slope': 3.0, 'intercept': 3.0,
            'linear': 2.5, 'exponential': 2.5, 'logarithmic': 2.5,
            'relationship between': 4.5, 'as a function of': 4.5, 'varies with': 4.0,
            'increasing': 2.0, 'decreasing': 2.0, 'parabola': 3.0,
            'hyperbola': 3.0, 'straight line': 3.0, 'axis': 2.0,
            'frequency': 2.5, 'wavelength': 2.0, 'energy': 1.5,
            'correctly represents': 3.5, 'which graph': 4.0,
        },
        'method': 'matplotlib',
        'description': 'Graph or plot showing relationship between variables'
    },
    DiagramType.MECHANICS: {
        'keywords': {
            'force': 3.5, 'friction': 3.5, 'pulley': 4.0, 'incline': 3.0,
            'inclined plane': 4.0, 'block': 2.5, 'mass': 2.0, 'weight': 2.5,
            'tension': 3.0, 'acceleration': 2.5, 'velocity': 2.5, 'momentum': 2.5,
            'collision': 3.0, 'projectile': 3.5, 'trajectory': 3.5,
            'lever': 3.5, 'fulcrum': 3.5, 'torque': 3.0, 'moment': 2.5,
            'equilibrium': 2.5, 'newton': 2.0, 'gravity': 2.5, 'free fall': 3.5,
            'pendulum': 4.0, 'spring': 3.0, 'oscillation': 3.0,
            'simple harmonic': 3.5, 'bob': 3.0, 'pivot': 3.0,
        },
        'method': 'matplotlib',
        'description': 'Mechanics diagram with forces, vectors, or motion'
    },
    DiagramType.OPTICS: {
        'keywords': {
            'lens': 4.0, 'mirror': 4.0, 'concave': 3.5, 'convex': 3.5,
            'focal': 3.5, 'focus': 3.0, 'refraction': 3.5, 'reflection': 3.5,
            'ray': 3.0, 'light': 2.5, 'prism': 4.0, 'optical': 3.0,
            'image': 2.0, 'object distance': 3.0, 'image distance': 3.0,
            'magnification': 2.5, 'spherical': 2.5, 'snell': 3.0,
            'critical angle': 3.5, 'total internal reflection': 4.0,
        },
        'method': 'matplotlib',
        'description': 'Optical diagram with lenses, mirrors, or light rays'
    },
    DiagramType.WAVES: {
        'keywords': {
            'wave': 3.5, 'wavelength': 3.5, 'frequency': 3.0, 'amplitude': 3.5,
            'phase': 2.5, 'sine': 3.0, 'cosine': 3.0, 'transverse': 3.0,
            'longitudinal': 3.0, 'interference': 3.5, 'diffraction': 3.5,
            'standing wave': 4.0, 'node': 3.0, 'antinode': 3.0,
            'harmonic': 3.0, 'resonance': 3.0, 'sound wave': 3.5,
            'electromagnetic': 2.5, 'oscillate': 2.5, 'amplitude of': 3.5,
        },
        'method': 'matplotlib',
        'description': 'Wave diagram showing oscillation or propagation'
    },
    DiagramType.ATOM: {
        'keywords': {
            'atom': 3.5, 'orbital': 4.0, 'bohr': 4.0, 'electron': 3.0,
            'proton': 3.0, 'neutron': 3.0, 'nucleus': 3.5, 'energy level': 4.0,
            'quantum': 3.0, 'spectral': 3.0, 'hydrogen': 2.5,
            'atomic model': 4.0, 'electron configuration': 4.0,
            'shell': 3.0, 'subshell': 3.0, 'quantum number': 3.5,
        },
        'method': 'raw_svg',
        'description': 'Atomic or orbital diagram'
    },
    DiagramType.APPARATUS: {
        'keywords': {
            'apparatus': 4.0, 'flask': 4.0, 'beaker': 4.0, 'test tube': 4.0,
            'burette': 4.0, 'pipette': 4.0, 'distillation': 3.5,
            'filtration': 3.5, 'crystallization': 3.5, 'titration': 3.5,
            'condenser': 4.0, 'thermometer': 3.5, 'burner': 3.5,
            'funnel': 3.5, 'crucible': 4.0, 'round bottom': 3.5,
            'conical flask': 4.0, 'measuring cylinder': 4.0,
        },
        'method': 'raw_svg',
        'description': 'Chemistry laboratory apparatus'
    },
    DiagramType.MOLECULE: {
        'keywords': {
            'molecule': 3.5, 'compound': 2.5, 'bond': 2.5,
            'structural formula': 4.0, 'isomer': 3.0, 'functional group': 3.5,
            'organic': 2.0, 'hydrocarbon': 3.0, 'alkane': 3.5,
            'alkene': 3.5, 'alkyne': 3.5, 'alcohol': 3.0,
            'carboxylic acid': 3.5, 'ester': 3.0, 'smiles': 4.0,
            'benzene': 3.5, 'aromatic': 3.0, 'chiral': 3.0,
        },
        'method': 'rdkit',
        'description': 'Molecular structure diagram'
    },
    DiagramType.GEOMETRY: {
        'keywords': {
            'triangle': 3.5, 'rectangle': 3.5, 'square': 2.0,
            'circle': 2.5, 'polygon': 3.5, 'angle': 2.5,
            'area of': 3.0, 'perimeter': 3.5, 'radius': 1.5,
            'diameter': 2.5, 'chord': 3.5, 'tangent': 3.0,
            'secant': 3.5, 'arc': 3.0, 'sector': 3.5,
            'segment': 3.0, 'quadrilateral': 4.0, 'prove that': 2.0,
        },
        'method': 'matplotlib',
        'description': 'Geometric shape or figure'
    },
    DiagramType.BIOLOGY: {
        'keywords': {
            'cell': 4.0, 'tissue': 3.5, 'organ': 3.5, 'membrane': 4.0,
            'mitochondria': 4.5, 'mitochondrion': 4.5, 'nucleus': 4.0,
            'chromosome': 4.0, 'dna': 4.0, 'rna': 4.0, 'gene': 3.5,
            'protein': 3.0, 'enzyme': 3.0, 'ribosome': 4.0,
            'golgi': 4.0, 'endoplasmic': 4.0, 'lysosome': 4.0,
            'vacuole': 4.0, 'cytoplasm': 3.5, 'organelle': 4.0,
            'diagram shows': 3.5, 'labeled': 3.0, 'structure labeled': 4.0,
            'respiratory system': 4.5, 'circulatory system': 4.5,
            'digestive system': 4.5, 'nervous system': 4.5,
            'skeletal': 3.5, 'muscle': 3.5, 'heart': 3.5, 'brain': 3.5,
            'kidney': 4.0, 'liver': 3.5, 'lung': 3.5, 'blood vessel': 4.0,
            'artery': 3.5, 'vein': 3.5, 'capillary': 4.0,
            'neuron': 4.0, 'synapse': 4.5, 'synaptic': 4.5,
            'bacteria': 4.0, 'virus': 4.0, 'pathogen': 3.5,
            'antibody': 3.5, 'antigen': 3.5, 'immune': 3.5,
            'photosynthesis': 4.0, 'chloroplast': 4.5, 'leaf': 3.0,
            'root': 3.0, 'stem': 3.0, 'flower': 3.0, 'plant cell': 4.5,
            'animal cell': 4.5, 'blood cell': 4.5, 'white blood': 4.0,
            'red blood': 4.0, 'platelet': 4.0, 'plasma': 3.0,
            'hormone': 3.0, 'gland': 3.5, 'pituitary': 4.0,
            'thyroid': 4.0, 'adrenal': 4.0, 'pancreas': 3.5,
            'insulin': 3.5, 'glucose': 3.0, 'glycolysis': 4.0,
            'krebs': 4.0, 'calvin': 4.0, 'cell cycle': 4.5,
            'mitosis': 4.5, 'meiosis': 4.5, 'replication': 3.5,
            'transcription': 4.0, 'translation': 4.0,
            'inhibitor': 3.0, 'substrate': 3.0, 'active site': 4.0,
        },
        'method': 'raw_svg',
        'description': 'Biological diagram (cell, organ, system)'
    }
}

PHRASE_PATTERNS = {
    'square root': DiagramType.GRAPH,
    'square of': DiagramType.GRAPH,
    'relationship between': DiagramType.GRAPH,
    'as a function of': DiagramType.GRAPH,
    'varies with': DiagramType.GRAPH,
    'which graph': DiagramType.GRAPH,
    'correctly represents': DiagramType.GRAPH,
    'simple harmonic': DiagramType.WAVES,
    'simple harmonic motion': DiagramType.WAVES,
    'free fall': DiagramType.MECHANICS,
    'inclined plane': DiagramType.MECHANICS,
    'total internal reflection': DiagramType.OPTICS,
    'standing wave': DiagramType.WAVES,
    'sound wave': DiagramType.WAVES,
    'electric circuit': DiagramType.CIRCUIT,
    'rc circuit': DiagramType.CIRCUIT,
    'rl circuit': DiagramType.CIRCUIT,
    'energy level': DiagramType.ATOM,
    'atomic model': DiagramType.ATOM,
    'electron configuration': DiagramType.ATOM,
    'structural formula': DiagramType.MOLECULE,
    'functional group': DiagramType.MOLECULE,
    'diagram shows': DiagramType.BIOLOGY,
    'the diagram': DiagramType.BIOLOGY,
    'labeled as': DiagramType.BIOLOGY,
    'structure labeled': DiagramType.BIOLOGY,
    'structures labeled': DiagramType.BIOLOGY,
    'synaptic junction': DiagramType.BIOLOGY,
    'synapse': DiagramType.BIOLOGY,
    'cell membrane': DiagramType.BIOLOGY,
    'plant cell': DiagramType.BIOLOGY,
    'animal cell': DiagramType.BIOLOGY,
    'blood cell': DiagramType.BIOLOGY,
    'respiratory system': DiagramType.BIOLOGY,
    'circulatory system': DiagramType.BIOLOGY,
    'digestive system': DiagramType.BIOLOGY,
    'nervous system': DiagramType.BIOLOGY,
}

CONTEXT_EXCLUSIONS = {
    'radius': {
        'radius of wire': DiagramType.GRAPH,
        'radius of curve': DiagramType.MECHANICS,
        'radius of curvature': DiagramType.OPTICS,
        'atomic radius': DiagramType.ATOM,
    },
    'square': {
        'square root': DiagramType.GRAPH,
        'square of': DiagramType.GRAPH,
    },
    'frequency': {
        'frequency of': DiagramType.WAVES,
        'resonant frequency': DiagramType.WAVES,
    },
}

SUBJECT_BOOSTS = {
    'physics': {
        DiagramType.GRAPH: 1.3,
        DiagramType.CIRCUIT: 1.4,
        DiagramType.MECHANICS: 1.3,
        DiagramType.WAVES: 1.3,
        DiagramType.OPTICS: 1.2,
    },
    'chemistry': {
        DiagramType.MOLECULE: 1.4,
        DiagramType.APPARATUS: 1.3,
        DiagramType.ATOM: 1.2,
    },
    'math': {
        DiagramType.GRAPH: 1.3,
        DiagramType.GEOMETRY: 1.4,
    },
    'biology': {
        DiagramType.BIOLOGY: 1.5,
        DiagramType.MOLECULE: 1.2,
        DiagramType.APPARATUS: 1.1,
    }
}


def extract_phrases(text_lower: str) -> Tuple[Dict[str, DiagramType], str]:
    detected = {}
    modified_text = text_lower
    
    for phrase, diagram_type in sorted(PHRASE_PATTERNS.items(), key=lambda x: -len(x[0])):
        if phrase in modified_text:
            detected[phrase] = diagram_type
            modified_text = modified_text.replace(phrase, ' ' * len(phrase))
    
    return detected, modified_text


def check_context_exclusions(keyword: str, text_lower: str) -> Optional[DiagramType]:
    if keyword not in CONTEXT_EXCLUSIONS:
        return None
    
    exclusions = CONTEXT_EXCLUSIONS[keyword]
    for context_phrase, diagram_type in exclusions.items():
        if context_phrase in text_lower:
            return diagram_type
    
    return None


def extract_visual_keywords(question_text: str) -> Tuple[str, List[str]]:
    text_lower = question_text.lower()
    
    phrases, modified_text = extract_phrases(text_lower)
    
    all_keywords = set()
    for pattern_info in DIAGRAM_PATTERNS.values():
        all_keywords.update(pattern_info['keywords'].keys())
    
    found_keywords = []
    for kw in sorted(all_keywords, key=len, reverse=True):
        if kw in modified_text:
            found_keywords.append(kw)
    
    unique_keywords = []
    seen = set()
    for kw in found_keywords:
        if not any(kw in s for s in seen if kw != s):
            unique_keywords.append(kw)
            seen.add(kw)
    
    phrase_keywords = list(phrases.keys())
    all_found = phrase_keywords + unique_keywords[:5]
    
    return ' '.join(all_found), all_found


def classify_diagram(
    question_text: str,
    subject: str = None,
    options: dict = None
) -> ClassificationResult:
    text_lower = question_text.lower()
    
    if options:
        for opt in options.values() if isinstance(options, dict) else options:
            if opt:
                text_lower += ' ' + opt.lower()
    
    phrase_matches, modified_text = extract_phrases(text_lower)
    
    scores: Dict[DiagramType, Tuple[float, List[str], float]] = {}
    
    for diagram_type, pattern_info in DIAGRAM_PATTERNS.items():
        keywords_dict = pattern_info['keywords']
        total_weight = sum(keywords_dict.values())
        matched = {}
        matched_phrases = []
        
        for phrase, phrase_type in phrase_matches.items():
            if phrase_type == diagram_type:
                matched_phrases.append(phrase)
                matched[phrase] = 5.0
        
        for kw, weight in keywords_dict.items():
            if kw in modified_text:
                context_type = check_context_exclusions(kw, text_lower)
                if context_type is None or context_type == diagram_type:
                    matched[kw] = weight
        
        if matched_phrases:
            for phrase in matched_phrases:
                matched[f"phrase:{phrase}"] = 5.0
        
        if matched:
            matched_weight = sum(matched.values())
            normalized_score = matched_weight / (total_weight + len(matched_phrases) * 5.0)
            scores[diagram_type] = (normalized_score, list(matched.keys()), matched_weight)
    
    if scores:
        for diagram_type, phrase in phrase_matches.items():
            if diagram_type in scores:
                norm_score, keywords, raw_score = scores[diagram_type]
                raw_score += 10.0
                scores[diagram_type] = (norm_score, keywords, raw_score)
    
    if subject:
        subject_lower = subject.lower()
        for subject_key, boosts in SUBJECT_BOOSTS.items():
            if subject_key in subject_lower:
                for diagram_type, boost in boosts.items():
                    if diagram_type in scores:
                        norm_score, keywords, raw_score = scores[diagram_type]
                        scores[diagram_type] = (norm_score * boost, keywords, raw_score * boost)
    
    if not scores:
        return ClassificationResult(
            diagram_type=DiagramType.GENERAL,
            confidence=0.0,
            keywords_matched=[],
            suggested_method='raw_svg',
            description='General diagram - no specific type detected'
        )
    
    best_type = max(scores.keys(), key=lambda x: (scores[x][2], scores[x][0]))
    best_norm_score, matched_keywords, best_raw_score = scores[best_type]
    
    method = DIAGRAM_PATTERNS[best_type]['method']
    confidence = min(best_raw_score / 20.0, 1.0)
    
    return ClassificationResult(
        diagram_type=best_type,
        confidence=confidence,
        keywords_matched=matched_keywords[:10],
        suggested_method=method,
        description=DIAGRAM_PATTERNS[best_type]['description']
    )


def get_method_for_diagram(diagram_type: DiagramType) -> str:
    return DIAGRAM_PATTERNS.get(diagram_type, {}).get('method', 'raw_svg')


def should_use_python_fallback(diagram_type: DiagramType) -> bool:
    python_methods = {'schemdraw', 'matplotlib', 'rdkit'}
    return DIAGRAM_PATTERNS.get(diagram_type, {}).get('method') in python_methods
