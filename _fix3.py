# -*- coding: utf-8 -*-
with open(r'C:\content-pipeline\app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find theme blocks and add icon/column/slogan
#周三
target3 = '\u4e09\u9ad8\uff0c\u5fc3\u8840\u7ba1\u7b49\u6162\u6027\u75c5\uff0c\u6b63\u5728\u6210\u4e3a\u6700\u521d\u9700\u7684\u79d1\u666e'
insert_after3 = '\u4e09\u9ad8\uff0c\u5fc3\u8840\u7ba1\u7b49\u6162\u6027\u75c5\uff0c\u6b63\u5728\u6210\u4e3a\u6700\u521d\u9700\u7684\u79d1\u666e'
insert_text = '        "icon": "\ud83d\udcca",\n        "column": "\u7a0d\u4f4f\u6162\u6162\u6765",\n        "slogan": "\u6162\u6027\u75c5\u4e0d\u53ef\u6015\uff0c\u6015\u7684\u662f\u4e0d\u7ba1\u5b83",\n'

new_lines = []
i = 0
while i < len(lines):
    new_lines.append(lines[i])
    # 周三
    if target3 in lines[i] and 'theme' in lines[i]:
        new_lines.append(insert_text)
        print('周三: inserted icon/column/slogan')
    i += 1

with open(r'C:\content-pipeline\app.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
print('Done')
