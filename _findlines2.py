# -*- coding: utf-8 -*-
with open(r'C:\content-pipeline\app.py', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines, 1):
    stripped = line.strip()
    if stripped.startswith('def ') or stripped.startswith('@') or stripped.startswith('ARTICLE') or stripped.startswith('OUTLINE') or stripped.startswith('PROMPT') or stripped.startswith('THREE'):
        print(f'L{i}: {stripped[:100]}')
