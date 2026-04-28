# -*- coding: utf-8 -*-
import subprocess, os
os.chdir(r'C:\content-pipeline')
subprocess.run(['git', 'add', '-A'])
subprocess.run(['git', 'commit', '-m', 'fix: 话题标签正则：#后非空格非#为话题标签，其余为标题'])
r = subprocess.run(['git', 'push', 'origin', 'main'], capture_output=True, text=True)
print(r.stdout)
print(r.stderr)
print('Done')
