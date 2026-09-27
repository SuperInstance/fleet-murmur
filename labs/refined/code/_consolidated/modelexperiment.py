# MODELEXPERIMENT — Consolidated from 3 tiles


## 2 Function Implementations Comparison

"""
From modelexperiment PLATO room.
"""
# **2. Function Implementations & Comparison**

Write a Python function `deadband_filter(data, lower, upper)` that classifies numeric values according to the Deadband Protocol:
- P0 (negative space): value < lower
- P1 (safe channel): lower <= value <= upper
- P2 (optimize): value > upper
Return a list of tuples [(value, classification_str)].


def deadband_filter(data, lower, upper):
    """
    Classify numeric values into P0, P1, P2 based on deadband thresholds.
    """
    result = []
    for val in data:
        if val < lower:
            classification = "P0"
        elif lower <= val <= upper:
            classification = "P1"
        else:  # val > upper
            classification = "P2"
        result.append((val, classification))
    return result


def deadband_filter(data, lower, upper):
    classifications = []
    for value in data:
        if value < lower:
            classifications.append((value, "P0"))
        elif value <= upper:
            classifications.append((value, "P1"))
        else:
            classifications.append((value, "P2"))
    return classifications


def deadband_filter(data, lower, upper):
    if lower > upper:
        raise ValueError("lower must be <= upper")
    results = []
    for v in data:
        if not isinstance(v, (int, float)):
            raise TypeError(f"Non-numeric value: {v}")
        if v < lower:
            results.append((v, "P0"))
        elif v <= upper:  # Handles lower <= v <= upper
            results.append((v, "P1"))
        else:
            results.append((v, "P2"))
    return results


Write a Python function `parse_fleet_context(markdown_text)` that parses fleet context markdown.
Extract:
1. All section headers (##) as a list.
2. Key technologies (bulleted list under "Key Technologies") as a list.
3. Rules (bulleted list under "Rules") as a list.
Return a dict: {'sections': [...], 'technologies': [...], 'rules': [...]}.
Assume the markdown follows FLEET-CONTEXT.md format.




---


## 2 Generated Code Comparison

"""
From modelexperiment PLATO room.
"""
# **2. Generated Code & Comparison**

import re

def validate_email(email: str) -> tuple[bool, str]:
    """
    Validates an email address format.
    Returns (is_valid: bool, reason: str).
    """
    if not email or not isinstance(email, str):
        return False, "Email must be a non-empty string."
    
    # Basic length check
    if len(email) > 254:
        return False, "Email exceeds maximum length (254 chars)."
    
    # RFC 5322 simplified regex (common practice)
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if re.match(pattern, email):
        return True, "Email format is valid."
    else:
        return False, "Email format is invalid."


import re

def validate_email(email):
    """
    Validate an email address.
    Returns a tuple (bool, str) where bool indicates validity and str provides a reason.
    """
    if not isinstance(email, str):
        return False, "Input must be a string"
    
    email = email.strip()
    if len(email) == 0:
        return False, "Email cannot be empty"
    
    # Regular expression for basic email validation
    regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if re.match(regex, email):
        return True, "Valid email address"
    else:
        return False, "Invalid email format"


from typing import Dict, Any

def merge_dicts_safe(*dicts: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merges multiple dictionaries, handling key conflicts by appending
    numerical suffixes (_1, _2, etc.) to duplicate keys.
    """
    result = {}
    key_count = {}
    
    for d in dicts:
        if not isinstance(d, dict):
            continue  # skip non-dict args
        for key, value in d.items():
            if key not in result:
                result[key] = value
                key_count[key] = 1
            else:
                new_key = f"{key}_{key_count[key]}"
                key_count[key] += 1
                result[new_key] = value
    return result




---


## 2 Model Outputs

"""
From modelexperiment PLATO room.
"""
# **2. Model Outputs**

from typing import List, Tuple

def validate_deadband_protocol(steps: List[str]) -> Tuple[bool, str]:
    """
    Validates if a list of steps follows the Deadband Protocol priority order.
    
    Rules:
    1. At least one step must start with "P0:".
    2. No "P2:" step may appear before a "P1:" step.
    
    Args:
        steps: List of step descriptions as strings.
    
    Returns:
        Tuple of (is_valid: bool, error_message: str).
        Error message is empty string if valid.
    """
    # Check for P0 presence
    has_p0 = any(step.strip().startswith("P0:") for step in steps)
    if not has_p0:
        return False, "P0 missing"
    
    # Check P2 before P1
    seen_p1 = False
    for step in steps:
        step_clean = step.strip()
        if step_clean.startswith("P1:"):
            seen_p1 = True
        elif step_clean.startswith("P2:") and not seen_p1:
            return False, "P2 before P1"
    
    return True, ""


import hashlib
import re
from typing import Dict, Optional

def parse_fleet_tile(content: str) -> Dict[str, str]:
    """
    Parses a fleet training tile string and extracts metadata.
    
    Expected format includes headers and markers like '**Cycle X — Role**'.
    
    Args:
        content: Raw tile content as a string.
    
    Returns:
        Dictionary with keys: title, agent_role, cycle, phase, content_hash.
        Missing values are empty strings.
    """
    result = {
        "title": "",
        "agent_role": "",
        "cycle": "",
        "phase": "",
        "content_hash": hashlib.sha256(content.encode()).hexdigest()
    }
    
    lines = content.split('\n')
    
    # Extract title from first # header
    for line in lines:
        if line.startswith('# '):
            result["title"] = line[2:].strip()
            break
    
    # Extract agent_role and cycle from pattern "**Cycle X — Role**"
    cycle_role_pattern = r'\*\*Cycle\s+(\d+)\s*—\s*([^*]+)\*\*'
    for line in lines:
        match = re.search(cycle_role_pattern, line)
        if match:
            result["cycle"] = match.group(1)
            result["agent_role"] = match.group(2).strip()
            break
    
    # Extract phase from pattern "**Phase Y:**"
    phase_pattern = r'\*\*Phase\s+(\d+)\s*:\*\*'
    for line in lines:
        match = re.search(phase_pattern, line)
        if match:
            result["phase"] = match.group(1)
            break
    
    return result




---
