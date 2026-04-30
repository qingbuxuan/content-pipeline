# -*- coding: utf-8 -*-
with open(r'C:\content-pipeline\app_merged.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()
for i, line in enumerate(lines, 1):
    s = line.strip()
    if any(k in s for k in ['read_articles', 'hist = read_articles', 'pbase = THREE', 'result = call_Deepseek(pbase', 'if hist:']):
        print(f'L{i}: {s[:120]}')
print(f"\nTotal lines: {len(lines)}")