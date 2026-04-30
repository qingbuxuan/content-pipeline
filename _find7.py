# -*- coding: utf-8 -*-
with open(r'C:\content-pipeline\app.py', 'r', encoding='utf-8') as f:
    for i, line in enumerate(f, 1):
        if line.strip().startswith('def '):
            print(f'{i}: {line.strip()[:80]}')
