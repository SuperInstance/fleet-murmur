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


