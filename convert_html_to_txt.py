"""Convert all HTML files in Desktop/FACEBOOK to plain .txt files."""
import os
import re
import html as html_mod

FACEBOOK = r"C:\Users\clint\Desktop\FACEBOOK"

converted = 0
for filename in sorted(os.listdir(FACEBOOK)):
    if not filename.lower().endswith('.html'):
        continue
    
    html_path = os.path.join(FACEBOOK, filename)
    txt_path = os.path.join(FACEBOOK, filename.replace('.html', '.txt'))
    
    with open(html_path, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()
    
    # Remove style blocks
    content = re.sub(r'<style[^>]*>.*?</style>', '', content, flags=re.DOTALL | re.IGNORECASE)
    
    # Remove script blocks
    content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL | re.IGNORECASE)
    
    # Remove head section
    content = re.sub(r'<head[^>]*>.*?</head>', '', content, flags=re.DOTALL | re.IGNORECASE)
    
    # Convert <br> tags to newlines
    content = re.sub(r'<br\s*/?>', '\n', content, flags=re.IGNORECASE)
    
    # Convert </p> and </div> and </tr> to double newlines
    content = re.sub(r'</p>', '\n\n', content, flags=re.IGNORECASE)
    content = re.sub(r'</div>', '\n', content, flags=re.IGNORECASE)
    content = re.sub(r'</tr>', '\n', content, flags=re.IGNORECASE)
    content = re.sub(r'</h[1-6]>', '\n\n', content, flags=re.IGNORECASE)
    content = re.sub(r'</li>', '\n', content, flags=re.IGNORECASE)
    content = re.sub(r'</td>', ' | ', content, flags=re.IGNORECASE)
    content = re.sub(r'<td[^>]*>', '', content, flags=re.IGNORECASE)
    
    # Strip all remaining HTML tags
    content = re.sub(r'<[^>]+>', '', content)
    
    # Decode HTML entities
    content = html_mod.unescape(content)
    
    # Collapse multiple blank lines
    content = re.sub(r'\n{4,}', '\n\n\n', content)
    content = re.sub(r'\n{3,}', '\n\n', content)
    
    # Strip leading/trailing whitespace per line
    lines = [line.strip() for line in content.splitlines()]
    # Remove completely empty leading/trailing lines
    while lines and not lines[0]:
        lines.pop(0)
    while lines and not lines[-1]:
        lines.pop()
    
    content = '\n'.join(lines)
    
    # Add header
    header = f"{'='*60}\n{filename}\nConverted: August 1, 2026 — BCC Investigation\n{'='*60}\n\n"
    
    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write(header + content)
    
    converted += 1
    print(f"  OK {filename} -> {os.path.basename(txt_path)}")

import sys
sys.stdout.reconfigure(encoding='utf-8')
print(f"\nConverted {converted} HTML files to .txt in {FACEBOOK}")
