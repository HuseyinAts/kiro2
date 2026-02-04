#!/usr/bin/env python3
"""
Script to update task requirement references in tasks.md
"""

import re

# Read the file
with open('.kiro/specs/MASTER_SPEC/tasks.md', 'r', encoding='utf-8') as f:
    content = f.read()

# Define replacement mappings
replacements = {
    # Task 53-58: Change REQ-26.X to REQ-48.X
    r'_Requirements: 26\.(\d+)-26\.(\d+)_': r'_Requirements: 48.\1-48.\2_',
    r'_Requirements: 26\.(\d+)_': r'_Requirements: 48.\1_',
    
    # Task 59-64: Change REQ-27.X to REQ-49.X
    r'_Requirements: 27\.(\d+)-27\.(\d+)_': r'_Requirements: 49.\1-49.\2_',
    r'_Requirements: 27\.(\d+)_': r'_Requirements: 49.\1_',
    
    # Task 76-82: Change REQ-30.X to REQ-50.X (Disleksi)
    r'_Requirements: 30\.(\d+)-30\.(\d+)_': r'_Requirements: 50.\1-50.\2_',
    r'_Requirements: 30\.(\d+)_': r'_Requirements: 50.\1_',
    
    # Task 83-87: Change REQ-31.X to REQ-51.X (Diskalkuli)
    r'_Requirements: 31\.(\d+)-31\.(\d+)_': r'_Requirements: 51.\1-51.\2_',
    r'_Requirements: 31\.(\d+)_': r'_Requirements: 51.\1_',
    
    # Task 88-92: Change REQ-32.X to REQ-52.X (DEHB)
    r'_Requirements: 32\.(\d+)-32\.(\d+)_': r'_Requirements: 52.\1-52.\2_',
    r'_Requirements: 32\.(\d+)_': r'_Requirements: 52.\1_',
    
    # Task 93-96: Change REQ-33.X to REQ-53.X (OSB)
    r'_Requirements: 33\.(\d+)-33\.(\d+)_': r'_Requirements: 53.\1-53.\2_',
    r'_Requirements: 33\.(\d+)_': r'_Requirements: 53.\1_',
}

# Apply replacements
for pattern, replacement in replacements.items():
    content = re.sub(pattern, replacement, content)

# Write back
with open('.kiro/specs/MASTER_SPEC/tasks.md', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Task requirement references updated successfully!")
print("Updated mappings:")
print("  - Task 53-58: REQ-26.X → REQ-48.X (LLM Soru Üretim)")
print("  - Task 59-64: REQ-27.X → REQ-49.X (Adaptif Test CAT)")
print("  - Task 76-82: REQ-30.X → REQ-50.X (Disleksi)")
print("  - Task 83-87: REQ-31.X → REQ-51.X (Diskalkuli)")
print("  - Task 88-92: REQ-32.X → REQ-52.X (DEHB)")
print("  - Task 93-96: REQ-33.X → REQ-53.X (OSB)")
