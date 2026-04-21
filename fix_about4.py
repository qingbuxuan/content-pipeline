# -*- coding: utf-8 -*-
with open(r'C:\content-pipeline\app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Count ABOUT_TEXT occurrences
count = content.count('ABOUT_TEXT = (')
print(f'ABOUT_TEXT occurrences: {count}')

# Find all positions
pos = 0
while True:
    idx = content.find('ABOUT_TEXT = (', pos)
    if idx < 0:
        break
    # Find the closing parenthesis
    end_idx = content.find(')', idx)
    print(f'Block at {idx} to {end_idx}')
    print(f'  Content: {repr(content[idx:end_idx+1][:200])}')
    pos = end_idx + 1
