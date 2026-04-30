# -*- coding: utf-8 -*-
import subprocess
import os
os.chdir(r'C:\content-pipeline')
# Remove temp files
temp_files = ['_push.py', 'fix4.py', 'fix_hash.py', 'fix_hash2.py', 'fix_hash3.py', 'fix_about.py', 'fix_about2.py', 'fix_about3.py', 'fix_about4.py', 'fix_about5.py', 'fix_final.py', 'fix_about.py', 'fix_about2.py', 'fix_about3.py', 'fix_about4.py', 'fix_about5.py', 'fix_final.py', 'fix_themes.py', 'add_theme_fields.py']
for f in temp_files:
    path = os.path.join(r'C:\content-pipeline', f)
    if os.path.exists(path):
        subprocess.run(['git', 'rm', '-f', path])
        print(f'Reoved: {f}')
subprocess.run(['git', 'commit', '-m', 'chore: cleanup temp scripts'])
r = subprocess.run(['git', 'push', 'origin', 'main'], capture_output=True, text=True)
print(r.stdout[-200:] if r.stdout else 'no stdout')
print(r.stderr[-200:] if r.stderr else 'no stderr')
