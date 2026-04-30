# -*- coding: utf-8 -*-
with open(r'C:\content-pipeline\app.py', encoding='utf-8') as f:
    content = f.read()

import re
# 找所有 def 函数
for m in re.finditer(r'^def (\w+)', content, re.MULTILINE):
    print(m.start(), m.group(1))
