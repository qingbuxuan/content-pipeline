# -*- coding: utf-8 -*-
with open(r'C:\content-pipeline\app_merged.py', 'r', encoding='utf-8') as f:
    for i, line in enumerate(f, 1):
        s = line.rstrip()
        if s.startswith('def '):
            print(f'{i}: {s[:80]}')
