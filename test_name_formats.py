#!/usr/bin/env python3
"""
Test script for name parsing in different formats
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from scrape import generate_username_variants

def test_name_format(name, expected_first_variant=None):
    print(f"\nTesting: '{name}'")
    print("-" * 60)
    variants = generate_username_variants(name)
    print(f"Generated variants: {variants}")
    if expected_first_variant:
        if variants[0] == expected_first_variant:
            print(f"✓ First variant matches expected: {expected_first_variant}")
        else:
            print(f"✗ Expected '{expected_first_variant}', got '{variants[0]}'")
    return variants

print("=" * 60)
print("NAME FORMAT PARSING TEST")
print("=" * 60)

# Traditional academic format: "Lastname, Firstname"
print("\n### TRADITIONAL FORMAT: 'Lastname, Firstname' ###")
test_name_format("Hornung, Johannes", "jhornung")
test_name_format("Gaisdörfer, Marcel", "mgaisdoerfer")
test_name_format("Müller, Anna", "amueller")

# Reversed format with comma: "Firstname, Lastname"
print("\n### REVERSED FORMAT: 'Firstname, Lastname' ###")
test_name_format("Johannes, Hornung", "jhornung")
test_name_format("Marcel, Gaisdörfer", "mgaisdoerfer")
test_name_format("Anna, Müller", "amueller")

# Natural order without comma: "Firstname Lastname"
print("\n### NATURAL FORMAT: 'Firstname Lastname' ###")
test_name_format("Johannes Hornung", "jhornung")
test_name_format("Marcel Gaisdörfer", "mgaisdoerfer")
test_name_format("Anna Müller", "amueller")

# Edge cases
print("\n### EDGE CASES ###")
test_name_format("Schmidt", "schmidt")  # Single name
test_name_format("Prof. Hornung, Johannes")  # With title
test_name_format("Quiroga-Triviño, Andrés", "aquirogatrivino")  # Hyphenated + special chars

# Ambiguous cases (could be interpreted either way)
print("\n### AMBIGUOUS CASES (both interpretations tried) ###")
test_name_format("Max, Schmidt")  # Could be "Firstname, Lastname" or "Lastname, Firstname"
test_name_format("Smith, John")  # Traditional: should prioritize jsmith

print("\n" + "=" * 60)
print("TEST COMPLETE")
print("=" * 60)
