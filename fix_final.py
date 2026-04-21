# -*- coding: utf-8 -*-
with open(r'C:\content-pipeline\app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# New correct ABOUT_TEXT
new_about = (
    'ABOUT_TEXT = (\n'
    '    "> 每天7点，7个方向，陪你慢慢变好。"\n'
    '    "> 情感、养生、慢病、情绪、品质，科技，急救——一周七天，天天有干货。"\n'
    '    "> 不讲大道理，只聊咱老百姓用得上的。"\n'
    '    "> 关注我，从今天起，有人陪你健康到老。"\n'
)

result = []
i = 0
in_old_about = False
about_count = 0

while i < len(lines):
    line = lines[i]
    
    # Detect start of ABOUT_TEXT block
    if 'ABOUT_TEXT = (' in line:
        about_count += 1
        if about_count <= 1:
            # Keep first ABOUT_TEXT as-is? No - replace it
            # Skip old block (find closing )
            j = i + 1
            while j < len(lines) and ')' not in lines[j]:
                j += 1
            # Skip old block
            print(f'Skipping old ABOUT_TEXT block lines {i+1}-{j+1}')
            i = j + 1
            # Insert new ABOUT_TEXT
            result.append(new_about)
            if not result[-1].endswith('\n'):
                result[-1] += '\n'
            continue
        else:
            # Second ABOUT_TEXT - skip entirely
            j = i + 1
            while j < len(lines) and ')' not in lines[j]:
                j += 1
            print(f'Skipping duplicate ABOUT_TEXT block lines {i+1}-{j+1}')
            i = j + 1
            continue
    
    result.append(line)
    i += 1

# Fix 文末预告: {WEEKDAY_NAMES[next_wk]} · {WEEKDAY_NAMES[next_wk]}
# Should be: {WEEKDAY_NAMES[next_wk]} · {next_banner.get('column', '')}
fixed_result = []
for line in result:
    if "WEEKDAY_NAMES[next_wk]} · {WEEKDAY_NAMES[next_wk]}" in line:
        fixed_line = line.replace(
            "WEEKDAY_NAMES[next_wk]} · {WEEKDAY_NAMES[next_wk]}",
            "WEEKDAY_NAMES[next_wk]} · {next_banner.get('column', '')}"
        )
        print(f'Fixed 文末预告: {repr(line[:60])} -> {repr(fixed_line[:60])}')
        fixed_result.append(fixed_line)
    else:
        fixed_result.append(line)

with open(r'C:\content-pipeline\app.py', 'w', encoding='utf-8') as f:
    f.writelines(fixed_result)

print(f'Done. Lines: {len(lines)} -> {len(fixed_result)}')
# Verify ABOUT_TEXT
for i, line in enumerate(fixed_result):
    if 'ABOUT_TEXT' in line:
        print(f'Line {i+1}: {repr(line[:60])}')
