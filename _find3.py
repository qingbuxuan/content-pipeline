# -*- coding: utf-8 -*-
with open(r'C:\content-pipeline\app.py', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines, 1):
    s = line.strip()
    if ('read_last_articles' in s) or ('node3' in s) or ('node4' in s) or ('outline' in s.lower() and 'prompt' in s.lower()) or ('article' in s.lower() and 'prompt' in s.lower()):
        print(f'L{i}: {s[:120]}')
