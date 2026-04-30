# -*- coding: utf-8 -*-
with open(r'C:\content-pipeline\app.py', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines, 1):
    s = line.strip()
    if (s.startswith('def ') or 
       ('ARTICLE' in s and 'PROMPT' in s) or
       ('OUTLINE' in s and 'PROMPT' in s) or
       ('node3' in s) or
       ('node4' in s)):
        print(f'L{i}: {s[:100]}')
