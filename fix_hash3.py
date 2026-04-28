# -*- coding: utf-8 -*-
import re

with open(r'C:\content-pipeline\app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 当前是旧的错误版本
old = r'md_text = re.sub(r"#(\S)", r"HASHTAG_PLACEHOLDER\1", md_text)'
new = r'md_text = re.sub(r"(?<=\S)#(\S+)", r"HASHTAG_PLACEHOLDER\1", md_text)  # 只匹配前面有文字的#话题'

if old in content:
    content = content.replace(old, new, 1)
    print('Replaced')
else:
    print('Old pattern not found')

with open(r'C:\content-pipeline\app.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Done')
