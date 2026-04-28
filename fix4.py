# -*- coding: utf-8 -*-
with open(r'C:\content-pipeline\app.py', 'r', encoding='utf-8') as f:
    c = f.read()

lines = c.split('\n')
new_lines = []
for line in lines:
    if 'HASHTAG_PLACEHOLDER' in line and 'sub' in line and 'md_text' in line:
        # 新规则：# 后跟非空格、非# 字符 = 话题标签
        new_line = '    md_text = re.sub(r"#([^#\\s]\\S*)", r"HASHTAG_PLACEHOLDER\\1", md_text)  # #后非空格非#=话题标签'
        new_lines.append(new_line)
        print(f'Replaced: {repr(line[:60])}')
    else:
        new_lines.append(line)

c = '\n'.join(new_lines)
with open(r'C:\content-pipeline\app.py', 'w', encoding='utf-8') as f:
    f.write(c)
print('Done')
