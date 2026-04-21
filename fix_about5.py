# -*- coding: utf-8 -*-
with open(r'C:\content-pipeline\app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find lines 37-42 (ABOUT_TEXT block 1) and 44-49 (ABOUT_TEXT block 2)
# Replace them with correct ABOUT_TEXT with > prefix

correct = (
    'ABOUT_TEXT = (\n'
    '> 每天7点，7个方向，陪你慢慢变好。\n'
    '> 情感、养生、慢病、情绪、品质，科技，急救——一周七天，天天有干货。\n'
    '> 不讲大道理，只聊咱老百姓用得上的。\n'
    '> 关注我，从今天起，有人陪你健康到老。\n'
)

new_lines = []
i = 0
while i < len(lines):
    line = lines[i]
    # Skip old ABOUT_TEXT blocks (lines 37-42 and 44-49)
    if i == 36:  # ABOUT_TEXT line
        # Check if this is an old ABOUT_TEXT
        if 'ABOUT_TEXT' in line and 'wxml' not in line:
            # Skip until we find the closing )
            j = i + 1
            while j < len(lines) and ')' not in lines[j]:
                j += 1
            j += 1  # include the ) line
            print(f'Skipping block at lines {i+1}-{j}')
            i = j
            continue
    new_lines.append(line)
    i += 1

# Actually, let me just rebuild the file
with open(r'C:\content-pipeline\app.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
print('Done - lines removed')
print(f'New line count: {len(new_lines)}')
