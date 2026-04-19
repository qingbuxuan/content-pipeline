# -*- coding: utf-8 -*-
with open('C:/content-pipeline/app.py', 'r', encoding='utf-8') as f:
    content = f.read()

changes = [
    (
        '\u4e09\u9ad8\uff0c\u5fc3\u8840\u7ba1\u7b49\u6162\u6027\u75c5\uff0c\u6b63\u5728\u6210\u4e3a\u6700\u521d\u9700\u7684\u79d1\u666e",
        '\u4e09\u9ad8\uff0c\u5fc3\u8840\u7ba1\u7b49\u6162\u6027\u75c5\uff0c\u6b63\u5728\u6210\u4e3a\u6700\u521d\u9700\u7684\u79d1\u666e',
    ),
]

# Wednesday - insert after theme line
old_wed = '"theme": "\u4e09\u9ad8\uff0c\u5fc3\u8840\u7ba1\u7b49\u6162\u6027\u75c5\uff0c\u6b63\u5728\u6210\u4e3a\u6700\u521d\u9700\u7684\u79d1\u666e",\n        "keywords": ["\u9ad8\u8840\u538b"'
new_wed = '"theme": "\u4e09\u9ad8\uff0c\u5fc3\u8840\u7ba1\u7b49\u6162\u6027\u75c5\uff0c\u6b63\u5728\u6210\u4e3a\u6700\u521d\u9700\u7684\u79d1\u666e",\n        "icon": "\ud83d\udcca",\n        "column": "\u7a0d\u4f4f\u6162\u6162\u6765",\n        "slogan": "\u6162\u6027\u75c5\u4e0d\u53ef\u6015\uff0c\u6015\u7684\u662f\u4e0d\u7ba1\u5b83",\n        "keywords": ["\u9ad8\u8840\u538b"'

if old_wed in content:
    content = content.replace(old_wed, new_wed)
    print('Wed: OK')
else:
    print('Wed: NOT FOUND')

# Thu
old_thu = '"theme": "\u574f\u60c5\u7eea\u6bd4\u9ad8\u8840\u538b\u66f4\u4f24\u8eab\uff0c\u8001\u5e74\u4eba\u7684\u5fc3\u7406\u95ee\u9898\u4e0d\u5bb9\u5ffd\u89c6",\n        "keywords": ["\u6291\u90c1"'
new_thu = '"theme": "\u574f\u60c5\u7eea\u6bd4\u9ad8\u8840\u538b\u66f4\u4f24\u8eab\uff0c\u8001\u5e74\u4eba\u7684\u5fc3\u7406\u95ee\u9898\u4e0d\u5bb9\u5ffd\u89c6",\n        "icon": "\ud83c\udf3f",\n        "column": "\u5fc3\u8981\u5bbd",\n        "slogan": "\u5fc3\u60c5\u987a\u4e86\uff0c\u8eab\u4f53\u5c31\u987a\u4e86",\n        "keywords": ["\u6291\u90c1"'

if old_thu in content:
    content = content.replace(old_thu, new_thu)
    print('Thu: OK')
else:
    print('Thu: NOT FOUND')

# Fri
old_fri = '"theme": "\u94f6\u53d1\u65cf\u7684\u6d88\u8d39\u5347\u7ea7\uff0c\u5982\u4f55\u628a\u94b1\u82b1\u5728\u5200\u5c16\u4e0a",\n        "keywords": ["\u6d88\u8d39"'
new_fri = '"theme": "\u94f6\u53d1\u65cf\u7684\u6d88\u8d39\u5347\u7ea7\uff0c\u5982\u4f55\u628a\u94b1\u82b1\u5728\u5200\u5c16\u4e0a",\n        "icon": "\ud83c\udfe0",\n        "column": "\u4f1a\u8fc7\u65e5\u5b50",\n        "slogan": "\u628a\u94b1\u82b1\u5728\u5200\u5c16\u4e0a\uff0c\u628a\u65e5\u5b50\u8fc7\u51fa\u6cbb\u5473",\n        "keywords": ["\u6d88\u8d39"'

if old_fri in content:
    content = content.replace(old_fri, new_fri)
    print('Fri: OK')
else:
    print('Fri: NOT FOUND')

# Sat
old_sat = '"theme": "AI\u4e0e\u667a\u80fd\u8bbe\u5907\uff0c\u6b63\u5728\u6539\u53d8\u8001\u5e74\u4eba\u7684\u5065\u5eb7\u7ba1\u7406\u65b9\u5f0f",\n        "keywords": ["\u624b\u673a"'
new_sat = '"theme": "AI\u4e0e\u667a\u80fd\u8bbe\u5907\uff0c\u6b63\u5728\u6539\u53d8\u8001\u5e74\u4eba\u7684\u5065\u5eb7\u7ba1\u7406\u65b9\u5f0f",\n        "icon": "\ud83d\udcf1",\n        "column": "\u8ddf\u4e0a\u65f6\u4ee3",\n        "slogan": "\u65b0\u4e1c\u897f\u4e0d\u96be\u5b66\uff0c\u5b66\u4e86\u5c31\u65b9\u4fbf",\n        "keywords": ["\u624b\u673a"'

if old_sat in content:
    content = content.replace(old_sat, new_sat)
    print('Sat: OK')
else:
    print('Sat: NOT FOUND')

# Sun
old_sun = '"theme": "\u5173\u952e\u65f6\u5219\u80fd\u6551\u547d\u7684\u786c\u77e5\u8bc6\uff0c\u662f\u6700\u80fd\u6253\u52a8\u4eba\u5fc3\u7684\u5185\u5bb9",\n        "keywords": ["\u6025\u6551"'
new_sun = '"theme": "\u5173\u952e\u65f6\u5219\u80fd\u6551\u547d\u7684\u786c\u77e5\u8bc6\uff0c\u662f\u6700\u80fd\u6253\u52a8\u4eba\u5fc3\u7684\u5185\u5bb9",\n        "icon": "\ud83d\ude91",\n        "column": "\u5173\u952e\u65f6\u523b",\n        "slogan": "\u5e73\u65f6\u770b\u4e00\u773c\uff0c\u6025\u65f6\u4e0d\u6293\u9瞎",\n        "keywords": ["\u6025\u6551"'

if old_sun in content:
    content = content.replace(old_sun, new_sun)
    print('Sun: OK')
else:
    print('Sun: NOT FOUND')

with open('C:/content-pipeline/app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Done')
