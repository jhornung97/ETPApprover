# Smart Username Lookup System - User Guide

## Overview

The ETaPprover Mattermost notification system now includes **intelligent username detection** that automatically generates and verifies Mattermost usernames from supervisor names.

## How It Works

### Automatic Username Generation

The system uses the following patterns to generate usernames:

1. **Pattern 1**: First letter + lastname (e.g., "Gaisdörfer, Marcel" → `mgais`)
2. **Pattern 2**: Lastname only (e.g., "Hornung, Johannes" → `hornung`)
3. **Pattern 3**: Full firstname + lastname (fallback)
4. **Pattern 4**: Handles hyphenated names with and without hyphens

### Smart Character Normalization

- **Umlauts**: ä→ae, ö→oe, ü→ue, ß→ss
- **Accents**: á→a, é→e, í→i, ó→o, ú→u
- **Special characters**: Removed (except hyphens)
- **Case**: All lowercase

### Automatic Verification

When connected to Mattermost, the system:
1. Generates all possible username variants
2. Tests each variant against Mattermost API
3. Selects the first valid username found
4. Falls back to first variant if none are valid

## Features

### 1. Manual Override Dictionary

For special cases or known mappings:

```python
manual_overrides = {
    'hornung': 'jhornung',
    'gaisdörfer': 'mgais',
    'gaisdorfer': 'mgais',
    'quiroga-trivino': 'aquiroga'
}
```

### 2. Interactive Username Lookup Tool

Both `scrape.py` (Mode 2) and `test.py` now include Option 4: "Test username lookup"

**Usage:**
```
Choose option (1/2/3/4/5): 4

Enter supervisor name(s) in format 'Lastname, Firstname'
(one per line, press Enter twice when done):
Gaisdörfer, Marcel
Hornung, Johannes
<press Enter>
<press Enter>
```

**Output:**
```
📊 Username Lookup Results:
--------------------------------------------------
  🔍 Processing supervisor: Gaisdörfer, Marcel
    ✓ Using manual override: @mgais
  🔍 Processing supervisor: Hornung, Johannes
    ✓ Using manual override: @jhornung

✓ Generated username mapping:
  Gaisdörfer, Marcel → @mgais
  Hornung, Johannes → @jhornung
--------------------------------------------------
```

### 3. Automatic Integration in scrape.py

When running Mode 1 (automated scraping), the system:
- Automatically detects Bachelor theses
- Extracts supervisor names from submission metadata
- Generates and verifies usernames
- Sends group DMs to all recipients

## Example Use Cases

### Example 1: New Supervisor "Müller, Stefan"

**Generated variants:**
1. `smueller` (first letter + lastname)
2. `mueller` (lastname only)
3. `stefanmueller` (full name)

**System tries each until finding valid username**

### Example 2: Hyphenated Name "García-López, María"

**Generated variants:**
1. `mgarcia-lopez` (with hyphen)
2. `garcia-lopez` (lastname only)
3. `mgarcialoez` (without hyphen)
4. `garcialopez` (without hyphen)
5. `mariagarcia-lopez` (full name)

### Example 3: Professor "Schmidt"

**Generated variants:**
1. `schmidt` (lastname only - preferred for professors)

## Functions Reference

### `generate_username_variants(supervisor_name)`
- Input: "Lastname, Firstname"
- Output: List of username variants in priority order

### `try_username_with_mattermost(api_url, token, username)`
- Tests if username exists in Mattermost
- Returns: True/False

### `extract_supervisor_usernames(supervisors, mattermost_config=None)`
- Input: List of supervisor names
- Optional: Mattermost config for verification
- Output: List of valid usernames

## Testing the System

### Method 1: Using test.py
```bash
cd /home/johannes/Documents/Scripts/webmaster/automatic_messaging
python3 test.py
```
Choose Option 4: "Test username lookup"

### Method 2: Using scrape.py Mode 2
```bash
python3 scrape.py 2
```
Choose Option 4: "Test username lookup"

### Method 3: Test in Python
```python
from scrape import extract_supervisor_usernames, generate_username_variants

# Generate variants
names = ["Müller, Stefan", "Schmidt, Anna"]
variants = [generate_username_variants(name) for name in names]
print(variants)

# With Mattermost verification
mattermost_config = {
    'api_url': 'https://mattermost.etp.kit.edu/api',
    'token': 'your-token'
}
usernames = extract_supervisor_usernames(names, mattermost_config)
print(usernames)
```

## Adding New Manual Overrides

Edit the `manual_overrides` dictionary in both files:
- `scrape.py` (line ~529)
- `test.py` (line ~282)

```python
manual_overrides = {
    'hornung': 'jhornung',
    'gaisdörfer': 'mgais',
    'newname': 'username',  # Add here
}
```

## Benefits

✅ **Automatic**: No manual username mapping needed
✅ **Smart**: Tries multiple patterns intelligently
✅ **Verified**: Tests usernames against Mattermost
✅ **Flexible**: Manual overrides for special cases
✅ **Interactive**: Built-in testing tool
✅ **Robust**: Handles umlauts, accents, hyphens
✅ **Fallback**: Always provides a username even if verification fails

## Troubleshooting

### Issue: Username not found
**Solution**: Add manual override or check Mattermost spelling

### Issue: Incorrect pattern detected
**Solution**: Add manual override for that supervisor

### Issue: SSL certificate warnings
**Note**: System suppresses SSL warnings for self-signed certificates (normal for internal servers)

## Version History

- **v2.0** (2025-11-21): Smart username lookup with automatic verification
- **v1.0** (2025-11-20): Manual username mapping dictionary
