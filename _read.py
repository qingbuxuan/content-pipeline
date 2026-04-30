# -*- coding: utf-8 -*-
with open(r'C:\content-pipeline\app_merged.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 找关键行
targets = ['read_last_articles', 'ARTICLE_PROMPT', 'node4_article', 
           'call_deepseek(ARTICLE', 'THREE_HOOKS_ARTICLE_PROMPT']
for i, line in enumerate(lines, 1):
    s = line.strip()
    for t in targets:
        if t in s:
            print(f'L{i}: {s[:120]}')
