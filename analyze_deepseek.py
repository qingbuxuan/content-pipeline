import re
content = open(r'C:\content-pipeline\app_merged.py', encoding='utf-8').read()

# Find all route definitions
routes = re.findall(r'@app\.route\([\'"]([^\'"]+)[\'"].*?def\s+(\w+)', content)
print('=== 所有路由 ===')
for path, fn in routes:
    print(f'  {path} -> {fn}')

print()

# Check Procfile
procfile = open(r'C:\content-pipeline\Procfile', encoding='utf-8').read()
print('=== Procfile ===')
print(procfile.strip())

print()
print('=== 每次完整运行的 DeepSeek 调用次数 ===')
# Count call_deepseek invocations (not definitions)
calls = re.findall(r'result\s*=\s*call_deepseek|summary\s*=\s*call_deepseek|cover_prompt\s*=\s*call_deepseek', content)
print(f'直接赋值调用: {len(calls)}')
# Also count with prompts
all_calls = [l for l in content.split('\n') if 'call_deepseek(' in l and 'def ' not in l]
print(f'含call_deepseek的行: {len(all_calls)}')
for l in all_calls:
    print(f'  {l.strip()[:100]}')

print()
# Check if app.py is the same as app_merged.py
app_content = open(r'C:\content-pipeline\app.py', encoding='utf-8').read()
print(f'app.py == app_merged.py: {content == app_content}')
print(f'app.py 大小: {len(app_content)}')
print(f'app_merged.py 大小: {len(content)}')

print()
print('=== 检查每天调用次数 ===')
print('正常每日流程（cron-job.org触发/trigger）：')
print('  Node1: 最多1次（素材不足时生成话题）')
print('  Node2: 1次')
print('  Node3: 1次')
print('  Node4: 1次')
print('  Node5: 2次（摘要+封面提示词）')
print('  合计: 最多 6 次 DeepSeek API 调用/天')
print()
print('  但用户报告 1058 次/天 = 175 天 × 6次...')
print('  这意味着平均每天被调用 175 次！')
print()
print('=== 可能原因 ===')
print('1. /trigger 端点被频繁手动调用')
print('2. cron-job.org 设置了多个任务')
print('3. UptimeRobot ping 也触发了 /trigger')
print('4. 其他定时任务也在调用')
