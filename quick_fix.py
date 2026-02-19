#!/usr/bin/env python3
"""
Quick fix to add timestamp parsing and better priority detection.
This applies fixes directly without regex complexity.
"""

import json

# Read the file
with open('core/xkg_core.py', 'r') as f:
    lines = f.readlines()

# Find line numbers to modify
class_line = None
export_d3_line = None
priority_keywords_start = None
priority_keywords_end = None

for i, line in enumerate(lines):
    if line.startswith('class Tweet:'):
        class_line = i
    if 'def export_for_d3(self)' in line:
        export_d3_line = i
    if "'urgent':" in line and priority_keywords_start is None:
        priority_keywords_start = i
    if priority_keywords_start and line.strip() == '})':
        priority_keywords_end = i
        break

print(f"Found key lines:")
print(f"  Tweet class: {class_line + 1}")
print(f"  export_for_d3: {export_d3_line + 1}")
print(f"  Priority keywords: {priority_keywords_start + 1} - {priority_keywords_end + 1}")

# Create new timestamp function
timestamp_func = '''

def parse_timestamp(ts: str) -> str:
    """Parse various timestamp formats to ISO 8601"""
    if not ts:
        return ""
    
    # Already ISO format
    if ts.startswith('20'):  # Starts with year like 2024-
        return ts.split('.')[0] + 'Z' if 'Z' not in ts else ts.split('.')[0] + 'Z'
    
    return ts

'''

# Insert timestamp function before class Tweet
lines.insert(class_line, timestamp_func)

# Now update priority keywords (recalculate indices after insert)
priority_keywords_start = None
priority_keywords_end = None
for i, line in enumerate(lines):
    if "'urgent':" in line and priority_keywords_start is None:
        priority_keywords_start = i
    if priority_keywords_start and line.strip() == '})':
        priority_keywords_end = i
        break

# New priority keywords (less noisy)
new_priority = """        # Improved priority detection - less noisy
        self.priority_keywords = {
            'urgent': [
                'asap', 'urgent', 'critical', 'emergency', 'blocking',
                'priority 1', 'p1', 'right now', 'immediately'
            ],
            'high': [
                'todo:', 'need to', 'must', 'required', 'deadline',
                'by friday', 'by monday', 'this week', 'important'
            ],
            'medium': [
                'remember to', 'going to', 'should', 'fix', 'update',
                'review', 'check', 'look at', 'consider'
            ],
            'low': [
                'would be nice', 'sometime', 'low priority', 'maybe',
                'eventually', 'when possible'
            ]
        }
"""

# Replace the old priority keywords
new_lines = lines[:priority_keywords_start] + [new_priority] + lines[priority_keywords_end+1:]
lines = new_lines

# Write the fixed file
with open('core/xkg_core.py', 'w') as f:
    f.writelines(lines)

print("\n✅ Applied fixes:")
print("   • Added parse_timestamp() function")
print("   • Replaced priority keywords with cleaner version")

