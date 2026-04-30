# -*- coding: utf-8 -*-
with open(r'C:\content-pipeline\app.py', encoding='utf-8') as f:
    lines = f.readlines()

# 找关键行
targets = ['read_last_articles', 'ARTICLE_PROMPT', 'node3_outline', 'node4_article', 
           'node2_title', 'outline_data', 'article_data', 
           'prompt +=', 'THREE_HOOKS']
for i, line in enumerate(lines, 1):
    s = line.strip()
    for t in targets:
        if t in s:
            print(f'L{i}: {s[:100]}')
            break
