# -*- coding: utf-8 -*-
with open(r'C:\content-pipeline\app.py', encoding='utf-8') as f:
    lines = f.readlines()

keywords = ['node3_outline', 'node4_article', 'ARTICLE_PROMPT', 'Outline_PROMPT', 'read_last_articles']
for i, line in enumerate(lines, 1):
    for kw in keywords:
        if kw in line:
            print(f'L{i}: {line.strip()[:80]}')
