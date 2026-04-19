# -*- coding: utf-8 -*-
import re

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Add icon, column, slogan to each theme
# Pattern: find each theme block and add fields after "theme" line

themes_to_add = {
    2: ('\u5468\u4e09 \xb7 \u6162\u75c5\u7ba1\u7406', '\ud83d\udcca', '\u7a0d\u4f4f\u6162\u6162\u6765', '\u6162\u6027\u75c5\u4e0d\u53ef\u6015\uff0c\u6015\u7684\u662f\u4e0d\u7ba1\u5b83'),
    3: ('\u5468\u56db \xb7 \u60c5\u7eea\u517b\u751f', '\ud83c\udf3f', '\u5fc3\u8981\u5bbd', '\u5fc3\u60c5\u987a\u4e86\uff0c\u8eab\u4f53\u5c31\u987a\u4e86'),
    4: ('\u5468\u4e94 \xb7 \u751f\u6d3b\u54c1\u8d28', '\ud83c\udfe0', '\u4f1a\u8fc7\u65e5\u5b50', '\u628a\u94b1\u82b1\u5728\u5200\u5c16\u4e0a\uff0c\u628a\u65e5\u5b50\u8fc7\u51fa\u6cbb\u5473'),
    5: ('\u5468\u516d \xb7 \u79d1\u6280\u5065\u5eb7', '\ud83d\udcf1', '\u8ddf\u4e0a\u65f6\u4ee3', '\u65b0\u4e1c\u897f\u4e0d\u96be\u5b66\uff0c\u5b66\u4e86\u5c31\u65b9\u4fbf'),
    6: ('\u5468\u65e5 \xb7 \u79d1\u666e\u6025\u6551', '\ud83d\ude91', '\u5173\u952e\u65f6\u523b', '\u5e73\u65f6\u770b\u4e00\u773c\uff0c\u6025\u65f6\u4e0d\u6293\u9xie'),
}

# For each theme, add icon, column, slogan after the "theme" line
for theme_idx, (name_part, icon, column, slogan) in themes_to_add():
    # Find the theme block
    pattern = rf'    {theme_idx}: {{  # {name_part}\n        "name": "[^"]+",\n        "theme": "[^"]+",\n        (".*?")\n        "keywords":'
    
    # Simpler approach: just insert after theme line
    for theme_idx, (name_part, icon, column, slogan) in themes_to_add.items():
        # Find the line containing "theme": and insert after it
        theme_line_pattern = rf'("theme": "[^"]+",)\n        ("keywords":)'
        if name_part in content:
            # Find the theme block for this day
            # Insert icon, column, slogan after theme line
            lines = content.split('\n')
            new_lines = []
            i = 0
            while i < len(lines):
                new_lines.append(lines[i])
                # After theme line of matching theme, insert new fields
                if f'{name_part}' in lines[i] and '"theme":' in lines[i]:
                    # Next non-empty line should be "keywords"
                    new_lines.append(f'        "icon": "{icon}",')
                    new_lines.append(f'        "column": "{column}",')
                    new_lines.append(f'        "slogan": "{slogan}",')
                i += 1
            content = '\n'.join(new_lines)
            print(f'Updated theme {theme_idx}')
        else:
            print(f'NOT FOUND: theme {theme_idx} - {name_part}')

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Done')
