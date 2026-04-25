# -*- coding: utf-8 -*-
import re

with open(r'C:\content-pipeline\app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix: only protect inline hashtags, not ## headings
old_pattern = r'md_text = re\.sub\(r"#\(\\S\)", r"HASHTAG_PLACEHOLDER\\1", md_text\)'
new_pattern = r'md_text = re.sub(r"(?<!\\n)#(\\S)", r"HASHTAG_PLACEHOLDER\\1", md_text)  # 只保护行内#话题，不破坏##标题'

content = re.sub(old_pattern, new_pattern, content)

with open(r'C:\content-pipeline\app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Done')
