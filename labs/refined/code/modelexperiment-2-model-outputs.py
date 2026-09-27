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


