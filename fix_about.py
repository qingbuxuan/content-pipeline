# -*- coding: utf-8 -*-
with open(r'C:\content-pipeline\app.py', 'rb') as f:
    content = f.read()

# Find the actual ABOUT_TEXT block
idx = content.find(b'\xe6\xaf\x8f\xe5\xa4\xa97')
print(f'Found at {idx}')
# Show 200 bytes
print(content[idx:idx+300])
