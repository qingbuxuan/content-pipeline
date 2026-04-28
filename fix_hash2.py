# -*- coding: utf-8 -*-
import re

with open(r'C:\content-pipeline\app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix: 只匹配前面有非空白字符的 #话题
old = r'md_text = re.sub(r"(?<!\\n)#(\\S)", r"HASHTAG_PLACEHOLDER\\1", md_text)  # 只保护行内#话题，不破坏##标题'
new = r'md_text = re.sub(r"(?<=\S)#(\S+)", r"HASHTAG_PLACEHOLDER\1", md_text)  # 只匹配前面有文字的#话题'

if old in content:
    content = content.replace(old, new, 1)
    print('Replaced')
else:
    print('Old pattern not found')
    # Show actual line
    for i, line in enumerate(content.split('\n'), 1):
        if 'HASHTAG_PLACEHOLDER' in line and 'md_text' in line:
            print(f'Line {i}: {line}')

with open(r'C:\content-pipeline\app.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Done')
