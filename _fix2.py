# -*- coding: utf-8 -*-
with open(r'C:\content-pipeline\app.py', 'r', encoding='utf-8') as f:
    content = f.read()

changes = [
    ('三高，心血管等慢性病，正在成为最刚需的科普",\n        "keywords": ["高血压"',
     '三高，心血管等慢性病，正在成为最刚需的科普",\n        "icon": "📊",\n        "column": "稳住慢慢来",\n        "slogan": "慢性病不可怕，怕的是不管它",\n        "keywords": ["高血压"'),
    ('坏情绪比高血压更伤身，老年人的心理问题不容忽视",\n        "keywords": ["抑郁"',
     '坏情绪比高血压更伤身，老年人的心理问题不容忽视",\n        "icon": "🌿",\n        "column": "心要宽",\n        "slogan": "心情顺了，身体就顺了",\n        "keywords": ["抑郁"'),
    ('银发族的消费升级，如何把钱花在刀刃上",\n        "keywords": ["消费"',
     '银发族的消费升级，如何把钱花在刀刃上",\n        "icon": "🏠",\n        "column": "会过日子",\n        "slogan": "把钱花在刀刃上，把日子过出滋味",\n        "keywords": ["消费"'),
    ('AI与智能设备，正在改变老年人的健康管理方式",\n        "keywords": ["手机"',
     'AI与智能设备，正在改变老年人的健康管理方式",\n        "icon": "📱",\n        "column": "跟上时代",\n        "slogan": "新东西不难学，学了就方便",\n        "keywords": ["手机"'),
    ('关键时刻能救命的硬知识，是最能打动人心的内容",\n        "keywords": ["急救"',
     '关键时刻能救命的硬知识，是最能打动人心的内容",\n        "icon": "🚑",\n        "column": "关键时刻",\n        "slogan": "平时看一眼，急时不抓瞎",\n        "keywords": ["急救"'),
]

for old, new in changes:
    if old in content:
        content = content.replace(old, new)
        print(f'OK: {old[:30]}')
    else:
        print(f'MISS: {old[:30]}')

with open(r'C:\content-pipeline\app.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Done')
