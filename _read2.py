# -*- coding: utf-8 -*-
with open(r'C:\content-pipeline\app_merged.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()
print(f"Total lines: {len(lines)}")

# 读关键行
def show(name, n):
    idx = n - 1
    print(f"\n=== {name} (L{n}) ===")
    for i in range(idx, min(idx+6, len(lines))):
        print(f"L{i+1}: {lines[i].rstrip()[:120]}")

show("THREE_HOOKS_ARTICLE_", 456)  # THREE_HOOKS_ARTICLE_PROMPT
show("node4_article", 742)
show("call_deepseek at 756", 754)
show("read_last_articles", 795)
show("ARTICLE_PROMPT_format at 756", 756)

# 搜索所有调用read_last_articles的地方
print("\n=== 所有调用 read_last_articles 的行 ===")
for i, line in enumerate(lines, 1):
    if 'read_last_articles' in line and i < 800:
        print(f"L{i}: {line.rstrip()[:120]}")