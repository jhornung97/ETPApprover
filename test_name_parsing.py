#!/usr/bin/env python3
"""
Test script to verify name parsing robustness
Tests both "Lastname, Firstname" and "Firstname Lastname" formats
"""

import re

def generate_username_variants(supervisor_name):
    """Generate possible Mattermost username variants from a supervisor name.
    
    Args:
        supervisor_name: Name in any format:
            - "Lastname, Firstname" (standard academic format)
            - "Firstname, Lastname" (reversed with comma)
            - "Firstname Lastname" (natural order)
            - "Lastname" (single name)
    
    Returns:
        List of username variants to try (in order of likelihood)
    """
    variants = []
    
    # Parse the name - handle multiple formats
    if ',' in supervisor_name:
        # Format with comma: could be "Lastname, Firstname" or "Firstname, Lastname"
        parts = supervisor_name.split(',')
        part1 = parts[0].strip()
        part2 = parts[1].strip() if len(parts) > 1 else ""
        
        # Heuristic: If part1 looks like a firstname (common first names, or shorter),
        # treat it as "Firstname, Lastname", otherwise "Lastname, Firstname"
        # Common academic titles that suggest lastname comes first
        academic_indicators = ['prof', 'dr', 'professor', 'doktor']
        has_title = any(indicator in part1.lower() for indicator in academic_indicators)
        
        # Check if part2 contains spaces (suggesting it might be a compound lastname)
        part2_has_spaces = ' ' in part2
        
        # If part1 is much longer than part2 and part2 doesn't have spaces,
        # it's likely "Lastname, Firstname" (traditional academic format)
        if (len(part1) > len(part2) * 1.5 and not part2_has_spaces) or has_title:
            # Traditional format: "Lastname, Firstname"
            lastname = part1
            firstname = part2
            firstname_alt = None
            lastname_alt = None
        else:
            # Could be reversed: "Firstname, Lastname"
            # Try both interpretations
            # The traditional format is still more common, so we'll prioritize it
            firstname = part2  # traditional
            lastname = part1   # traditional
            firstname_alt = part1  # reversed
            lastname_alt = part2   # reversed
    else:
        # Format without comma: "Firstname Lastname" or just "Lastname"
        parts = supervisor_name.strip().split()
        if len(parts) >= 2:
            # Assume last part is lastname, everything else is firstname
            firstname = ' '.join(parts[:-1])
            lastname = parts[-1]
            firstname_alt = None
            lastname_alt = None
        else:
            # Just one name, assume it's the lastname
            lastname = parts[0] if parts else supervisor_name.strip()
            firstname = ""
            firstname_alt = None
            lastname_alt = None
    
    # Remove umlauts and special characters
    def normalize(text):
        text = text.lower()
        # Replace umlauts
        replacements = {
            'ä': 'ae', 'ö': 'oe', 'ü': 'ue', 'ß': 'ss',
            'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u'
        }
        for old, new in replacements.items():
            text = text.replace(old, new)
        # Remove spaces and special characters except hyphens
        text = re.sub(r'[^\w\-]', '', text)
        return text
    
    lastname_normalized = normalize(lastname)
    firstname_normalized = normalize(firstname) if firstname else ""
    
    # Pattern 1: first letter + lastname (most common for non-professors)
    if firstname_normalized:
        variants.append(firstname_normalized[0] + lastname_normalized)
    
    # Pattern 2: lastname only (for professors)
    variants.append(lastname_normalized)
    
    # Pattern 3: full firstname + lastname (rare but possible)
    if firstname_normalized:
        variants.append(firstname_normalized + lastname_normalized)
    
    # Pattern 4: With hyphenated names, try without hyphen
    if '-' in lastname_normalized:
        lastname_no_hyphen = lastname_normalized.replace('-', '')
        if firstname_normalized:
            variants.append(firstname_normalized[0] + lastname_no_hyphen)
        variants.append(lastname_no_hyphen)
    
    # Pattern 5: If we have alternate interpretation (reversed format), try those too
    if firstname_alt and lastname_alt:
        lastname_alt_normalized = normalize(lastname_alt)
        firstname_alt_normalized = normalize(firstname_alt) if firstname_alt else ""
        
        if firstname_alt_normalized:
            variants.append(firstname_alt_normalized[0] + lastname_alt_normalized)
        variants.append(lastname_alt_normalized)
        if firstname_alt_normalized:
            variants.append(firstname_alt_normalized + lastname_alt_normalized)
        
        # With hyphenated names (alt version)
        if '-' in lastname_alt_normalized:
            lastname_alt_no_hyphen = lastname_alt_normalized.replace('-', '')
            if firstname_alt_normalized:
                variants.append(firstname_alt_normalized[0] + lastname_alt_no_hyphen)
            variants.append(lastname_alt_no_hyphen)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_variants = []
    for v in variants:
        if v not in seen:
            seen.add(v)
            unique_variants.append(v)
    
    return unique_variants

# Test cases
print("=" * 70)
print("Testing Name Parsing Robustness")
print("=" * 70)

test_cases = [
    # Format: "Lastname, Firstname"
    ("Hornung, Johannes", ["jhornung", "hornung", "johanneshornung"]),
    ("Gaisdörfer, Marcel", ["mgaisdoerfer", "gaisdoerfer", "marcelgaisdoerfer"]),
    ("Quiroga-Trivino, Alejandro", ["aquirogatrivino", "quirogatrivino", "alejandroquirogatrivino", "aquiroga", "quiroga"]),
    
    # Format: "Firstname Lastname" (reversed)
    ("Johannes Hornung", ["jhornung", "hornung", "johanneshornung"]),
    ("Marcel Gaisdörfer", ["mgaisdoerfer", "gaisdoerfer", "marcelgaisdoerfer"]),
    ("Alejandro Quiroga-Trivino", ["aquirogatrivino", "quirogatrivino", "alejandroquirogatrivino", "aquiroga", "quiroga"]),
    
    # Just lastname
    ("Hornung", ["hornung"]),
    ("Gaisdörfer", ["gaisdoerfer"]),
    
    # Edge cases
    ("Smith", ["smith"]),
    ("John Smith", ["jsmith", "smith", "johnsmith"]),
    ("Smith, John", ["jsmith", "smith", "johnsmith"]),
    ("von Müller, Hans", ["hvonmueller", "vonmueller", "hansvonmueller"]),
    ("Hans von Müller", ["hvonmueller", "vonmueller", "hansvonmueller"]),
]

print("\nTest Results:")
print("-" * 70)

all_passed = True
for i, (name, expected) in enumerate(test_cases, 1):
    variants = generate_username_variants(name)
    
    # Check if all expected variants are in the generated list
    missing = [e for e in expected if e not in variants]
    passed = len(missing) == 0
    
    status = "✓ PASS" if passed else "✗ FAIL"
    print(f"\n{i}. {status} | Input: '{name}'")
    print(f"   Generated: {variants}")
    print(f"   Expected:  {expected}")
    
    if not passed:
        print(f"   Missing:   {missing}")
        all_passed = False

print("\n" + "=" * 70)
if all_passed:
    print("✓ All tests passed!")
else:
    print("✗ Some tests failed - check output above")
print("=" * 70)

# Additional demonstration
print("\n" + "=" * 70)
print("Demonstration: Same person, different input formats")
print("=" * 70)

demo_pairs = [
    ("Johannes, Hornung", "Johannes Hornung"),
    ("Gaisdörfer, Marcel", "Marcel Gaisdörfer"),
    ("Quiroga-Trivino, Alejandro", "Alejandro Quiroga-Trivino"),
]

for format1, format2 in demo_pairs:
    variants1 = generate_username_variants(format1)
    variants2 = generate_username_variants(format2)
    
    match = variants1 == variants2
    status = "✓ MATCH" if match else "✗ DIFFER"
    
    print(f"\n{status}")
    print(f"  Format 1: '{format1}'")
    print(f"    → {variants1}")
    print(f"  Format 2: '{format2}'")
    print(f"    → {variants2}")
