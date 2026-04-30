# -*- coding: utf-8 -*-
import re

with open(r'C:\content-pipeline\app.py', encoding='utf-8') as f:
    content = f.read()

for m in re.finditer(r'^def (\w+)', content, re.MULTILINE):
    print(m.group(1))
