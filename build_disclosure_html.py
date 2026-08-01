#!/usr/bin/env python3
"""Convert DISCLOSURE_WHITEPAPER_TODO.md to a self-contained HTML file."""

import json

def main():
    with open('azazael/DISCLOSURE_WHITEPAPER_TODO.md', 'r', encoding='utf-8') as f:
        md_content = f.read()
    
    # Clean up encoding damage: runs of '?' from earlier bad encoding fixes are em dashes
    import re
    md_content = re.sub(r'\?{2,}', '\u2014', md_content)
    # Also fix standalone ? that are likely em dashes (space-?-space or newline-?-space patterns)
    md_content = re.sub(r' \? ', ' \u2014 ', md_content)
    md_content = re.sub(r'\n\? ', '\n\u2014 ', md_content)
    md_content = re.sub(r' \?\n', ' \u2014\n', md_content)
    
    # JSON-encode the markdown to safely embed in JavaScript
    md_json = json.dumps(md_content)
    
    # CDN-hosted marked.js
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AZAZAEL Disclosure Whitepaper</title>
<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{
  background: #0a0a0f;
  color: #c9d1d9;
  font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
  line-height: 1.7;
  padding: 60px 80px 200px 80px;
  max-width: 1100px;
  margin: 0 auto;
}}
h1 {{ color: #f0883e; border-bottom: 2px solid #f0883e44; padding-bottom: 10px; margin: 50px 0 20px; font-size: 2em; }}
h2 {{ color: #58a6ff; margin: 40px 0 15px; font-size: 1.5em; border-bottom: 1px solid #30363d; padding-bottom: 8px; }}
h3 {{ color: #7ee787; margin: 30px 0 10px; font-size: 1.2em; }}
h4 {{ color: #d2a8ff; margin: 20px 0 8px; }}
table {{ border-collapse: collapse; width: 100%; margin: 15px 0; font-size: 0.85em; }}
th, td {{ border: 1px solid #30363d; padding: 8px 12px; text-align: left; }}
th {{ background: #161b22; color: #f0883e; font-weight: 600; }}
tr:nth-child(even) {{ background: #0d1117; }}
code {{ background: #161b22; padding: 2px 6px; border-radius: 4px; font-family: 'Fira Code', 'Cascadia Code', monospace; font-size: 0.9em; color: #7ee787; }}
pre {{ background: #161b22; padding: 16px; border-radius: 8px; overflow-x: auto; margin: 15px 0; }}
pre code {{ background: none; padding: 0; }}
blockquote {{ border-left: 4px solid #f0883e; padding: 10px 20px; margin: 15px 0; background: #161b2244; color: #8b949e; }}
hr {{ border: none; border-top: 1px solid #30363d; margin: 40px 0; }}
a {{ color: #58a6ff; text-decoration: none; }}
a:hover {{ text-decoration: underline; }}
strong {{ color: #f0883e; }}
ul, ol {{ margin: 10px 0 10px 30px; }}
li {{ margin: 4px 0; }}
::-webkit-scrollbar {{ width: 8px; }}
::-webkit-scrollbar-track {{ background: #0d1117; }}
::-webkit-scrollbar-thumb {{ background: #30363d; border-radius: 4px; }}
</style>
</head>
<body>
<div id="content"></div>
<script>
(function wait() {{
  if (typeof marked !== 'undefined') {{
    document.getElementById('content').innerHTML = marked.parse({md_json});
    document.title = 'RENDER_READY | ' + document.title;
  }} else {{
    setTimeout(wait, 100);
  }}
}})();
</script>
</body>
</html>'''
    
    with open('disclosure_render.html', 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f'HTML size: {len(html):,} chars')
    print(f'MD size:   {len(md_content):,} chars')
    print('Written to: disclosure_render.html')

if __name__ == '__main__':
    main()
