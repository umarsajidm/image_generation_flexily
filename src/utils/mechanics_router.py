"""Mechanics diagram subtype classification."""
from enum import Enum
from typing import Dict, List, Tuple
import re


class MechanicsSubtype(Enum):
    PENDULUM = "pendulum"
    INCLINED_PLANE = "inclined_plane"
    PULLEY = "pulley"
    COLLISION = "collision"
    PROJECTILE = "projectile"
    SPRING = "spring"
    TORQUE = "torque"
    GENERIC = "generic"


SUBTYPE_PATTERNS: Dict[MechanicsSubtype, List[Tuple[str, float]]] = {
    MechanicsSubtype.PENDULUM: [
        (r'\bpendulum\b', 1.0),
        (r'\bswing\b', 0.8),
        (r'\bbob\b', 0.7),
        (r'\boscillat', 0.5),
        (r'\bsimple pendulum\b', 1.0),
        (r'\btime period.*pendulum\b', 1.0),
    ],
    MechanicsSubtype.INCLINED_PLANE: [
        (r'\binclined\b', 1.0),
        (r'\bslope\b', 0.8),
        (r'\bramp\b', 0.8),
        (r'\bwedge\b', 0.9),
        (r'\bincline plane\b', 1.0),
        (r'\bangle of inclination\b', 1.0),
    ],
    MechanicsSubtype.PULLEY: [
        (r'\bpulley\b', 1.0),
        (r'\batwood\b', 1.0),
        (r'\block.*rope\b', 0.7),
        (r'\btension.*string\b', 0.6),
        (r'\brope\b', 0.5),
    ],
    MechanicsSubtype.COLLISION: [
        (r'\bcollid', 1.0),
        (r'\bcollision\b', 1.0),
        (r'\bimpact\b', 0.8),
        (r'\bstrikes\b', 0.7),
        (r'\belastic\b', 0.6),
        (r'\binelastic\b', 0.9),
        (r'\bhead.?on\b', 0.8),
    ],
    MechanicsSubtype.PROJECTILE: [
        (r'\bprojectile\b', 1.0),
        (r'\bthrown\b', 0.7),
        (r'\blaunch', 0.8),
        (r'\bparabolic\b', 0.9),
        (r'\btrajectory\b', 0.8),
        (r'\bthrown.*angle\b', 0.9),
        (r'\bmaximum height\b', 0.7),
        (r'\brange.*projectile\b', 0.9),
    ],
    MechanicsSubtype.SPRING: [
        (r'\bspring\b', 1.0),
        (r'\boscillat.*mass\b', 0.7),
        (r'\bhook', 0.6),
        (r'\bcompress', 0.5),
        (r'\bspring constant\b', 1.0),
        (r'\bextension.*spring\b', 0.9),
    ],
    MechanicsSubtype.TORQUE: [
        (r'\btorque\b', 1.0),
        (r'\bpivot\b', 0.8),
        (r'\bmoment.*force\b', 0.7),
        (r'\blever\b', 0.8),
        (r'\bfulcrum\b', 0.9),
        (r'\brotat', 0.6),
        (r'\bbeam\b', 0.5),
        (r'\brod\b', 0.4),
        (r'\bcouple\b', 0.8),
        (r'\bturning effect\b', 0.7),
    ],
}


def classify_mechanics_subtype(question: str) -> MechanicsSubtype:
    """
    Classify a mechanics question into a specific subtype.
    
    Args:
        question: The MCQ question text
        
    Returns:
        MechanicsSubtype enum value
    """
    q_lower = question.lower()
    scores: Dict[MechanicsSubtype, float] = {subtype: 0.0 for subtype in MechanicsSubtype}
    
    for subtype, patterns in SUBTYPE_PATTERNS.items():
        for pattern, weight in patterns:
            if re.search(pattern, q_lower):
                scores[subtype] += weight
    
    best_subtype = max(scores, key=scores.get)
    
    if scores[best_subtype] > 0.5:
        return best_subtype
    else:
        return MechanicsSubtype.GENERIC


def get_subtype_confidence(question: str) -> Tuple[MechanicsSubtype, float]:
    """
    Get the classified subtype along with confidence score.
    
    Args:
        question: The MCQ question text
        
    Returns:
        Tuple of (MechanicsSubtype, confidence_score)
    """
    q_lower = question.lower()
    scores: Dict[MechanicsSubtype, float] = {subtype: 0.0 for subtype in MechanicsSubtype}
    
    for subtype, patterns in SUBTYPE_PATTERNS.items():
        for pattern, weight in patterns:
            if re.search(pattern, q_lower):
                scores[subtype] += weight
    
    best_subtype = max(scores, key=scores.get)
    confidence = scores[best_subtype]
    
    if confidence <= 0.5:
        return MechanicsSubtype.GENERIC, confidence
    
    return best_subtype, confidence


if __name__ == "__main__":
    test_cases = [
        ("A simple pendulum is released from point X", "pendulum"),
        ("A block slides down an inclined plane at angle 30°", "inclined_plane"),
        ("Two objects collide on a frictionless surface", "collision"),
        ("A projectile is launched at 45 degrees", "projectile"),
        ("A spring is compressed by 0.5m", "spring"),
        ("A torque is applied to a rod at the pivot point", "torque"),
        ("What is the work done by the force?", "generic"),
        ("A block of mass 2kg is connected to a pulley system", "pulley"),
    ]
    
    print("Mechanics Router Test Results:")
    print("-" * 60)
    for question, expected in test_cases:
        result = classify_mechanics_subtype(question)
        status = '✓' if result.value == expected else '✗'
        print(f"  {status} {result.value:15s} (expected: {expected})")
