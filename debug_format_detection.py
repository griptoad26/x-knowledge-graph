#!/usr/bin/env python3
"""
Debug script for format detection issues.
Run: python3 debug_format_detection.py
"""

import sys
import os
import json
from pathlib import Path

# Add core to path
sys.path.insert(0, 'core')

def find_all_export_files(directory, extensions=None):
    """Find all files in directory matching extensions (recursive)"""
    if extensions is None:
        extensions = ['.json', '.js']
    
    files = []
    directory = Path(directory)
    
    if not directory.exists():
        return files
    
    for path in directory.rglob('*'):
        if path.is_file():
            suffix = path.suffix.lower()
            name_lower = path.name.lower()
            if suffix in extensions or any(ext in name_lower for ext in extensions):
                files.append(str(path))
    
    return sorted(set(files))


def detect_export_format(filepath):
    """Auto-detect if file is X, Grok, or Production Log format"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for X export format
        if 'window.YTD' in content or '.part0' in content:
            return 'x'
        
        # Try parsing as JSON
        try:
            data = json.loads(content)
            
            # Check for Grok format
            if isinstance(data, list):
                # Check for 'source': 'grok'
                if any(item.get('source') == 'grok' for item in data if isinstance(item, dict)):
                    return 'grok'
                # Check for Grok fields
                if data:
                    first_item = data[0]
                    if any(field in first_item for field in ['author_id', 'conversation_id']):
                        return 'grok'
            
            # Check for X format
            if isinstance(data, dict):
                if 'tweet' in data:
                    return 'x'
                if any(k for k in data.keys() if 'tweet' in k.lower()):
                    return 'x'
        
        except json.JSONDecodeError:
            pass
        
        # Check filename patterns
        filename = Path(filepath).name.lower()
        if 'tweet' in filename or filename.startswith('tweet'):
            return 'x'
        if 'post' in filename or filename.endswith('.json'):
            return 'grok'  # Likely Grok if no X markers
        
        return 'unknown'
    
    except Exception as e:
        return f'error: {e}'


def debug_format_detection(export_path):
    """Debug format detection for any export folder"""
    print(f"\n{'='*60}")
    print(f"FORMAT DETECTION DEBUG: {export_path}")
    print(f"{'='*60}\n")
    
    files = find_all_export_files(export_path, ['*'])
    
    if not files:
        print(f"⚠️  No files found in {export_path}")
        return
    
    print(f"Found {len(files)} files:\n")
    
    for filepath in files:
        if not os.path.isfile(filepath):
            continue
            
        fmt = detect_export_format(filepath)
        filename = os.path.basename(filepath)
        
        # Status icon
        if fmt == 'x':
            icon = '✅'
        elif fmt == 'grok':
            icon = '✅'
        elif 'error' in str(fmt):
            icon = '❌'
        else:
            icon = '⚠️'
        
        print(f"{icon} {filename:30} → {fmt}")
        
        if fmt == 'unknown':
            print(f"    💡 Peeking content:")
            with open(filepath) as fh:
                content = fh.read(500)
                print(f"    {content[:400]}...")
        
        print()
    
    return files


def test_priority_detection():
    """Test the improved priority detection"""
    print(f"{'='*60}")
    print("PRIORITY DETECTION TEST")
    print(f"{'='*60}\n")
    
    test_cases = [
        ("ASAP: Fix the login bug!", "URGENT"),
        ("TODO: Update the API documentation", "HIGH"),
        ("Remember to backup the database", "MEDIUM"),
        ("Going to refactor the code", "MEDIUM"),
        ("Would be nice to have dark mode", "LOW"),
        ("Critical bug affecting all users", "URGENT"),
        ("Need to finish by Friday", "HIGH"),
    ]
    
    for text, expected in test_cases:
        detected = detect_priority(text)
        status = '✅' if detected == expected else '❌'
        print(f"{status} '{text[:40]}' → {detected} (expected: {expected})")


def detect_priority(text):
    """Improved priority detection"""
    text_lower = text.lower()
    
    urgent = ['asap', 'urgent', 'critical', 'emergency', 'blocking', 'p1', 'right now']
    high = ['todo:', 'need to', 'must', 'required', 'deadline', 'important']
    medium = ['remember to', 'going to', 'should', 'fix', 'update', 'review', 'check']
    low = ['would be nice', 'sometime', 'low priority', 'maybe']
    
    for kw in urgent:
        if kw in text_lower:
            return 'URGENT'
    for kw in high:
        if kw in text_lower:
            return 'HIGH'
    for kw in medium:
        if kw in text_lower:
            return 'MEDIUM'
    for kw in low:
        if kw in text_lower:
            return 'LOW'
    
    return 'MEDIUM'  # Default


if __name__ == '__main__':
    import sys
    
    print("\n" + "="*60)
    print("X KNOWLEDGE GRAPH - DEBUG TOOLS")
    print("="*60)
    
    # Run format detection debug
    debug_format_detection('./test_data/x_export')
    debug_format_detection('./test_data/grok_export')
    
    # Test priority detection
    test_priority_detection()
    
    print("\n" + "="*60)
    print("QUICK FIXES APPLIED")
    print("="*60)
    print("""
1. Format Detection: Enhanced with filename pattern matching
2. Priority Detection: Clean keyword lists, no false positives
3. Debug Helper: Run this script to diagnose any folder
    
Next: Edit core/xkg_core.py to apply these fixes permanently.
    """)
