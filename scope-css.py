import re, sys

def scope_file(filepath):
    with open(filepath) as f:
        content = f.read()
    
    # Split into style and HTML
    style_match = re.match(r'<style>(.*?)</style>(.*)', content, re.DOTALL)
    if not style_match:
        print(f"No style block found in {filepath}")
        return
    
    css = style_match.group(1)
    html = style_match.group(2).strip()
    
    # Process CSS: scope all selectors with .jp-embed
    scoped_css = scope_css(css)
    
    # Wrap HTML in .jp-embed div
    new_content = f'<style>\n{scoped_css}\n</style>\n\n<div class="jp-embed">\n{html}\n</div>'
    
    with open(filepath, 'w') as f:
        f.write(new_content)
    print(f"Scoped: {filepath}")

def scope_css(css):
    lines = []
    in_media = False
    
    # Process rule by rule using a simple approach:
    # Split on } and process each chunk
    result = []
    
    # Handle :root specially - keep it as-is (CSS custom props are global but harmless in embeds)
    # Actually, scope :root to .jp-embed too
    
    # Use a regex-based approach to find selectors and scope them
    # Strategy: find each selector block (before {) and prefix selectors
    
    parts = re.split(r'(\{[^{}]*\}|/\*[^*]*\*/|@media[^{]*\{)', css)
    
    i = 0
    output = []
    while i < len(parts):
        part = parts[i]
        
        # Comment
        if part.strip().startswith('/*'):
            output.append(part)
            i += 1
            continue
        
        # @media query
        if part.strip().startswith('@media'):
            output.append(part)
            i += 1
            continue
        
        # Closing brace for @media
        if part.strip() == '}':
            output.append(part)
            i += 1
            continue
        
        # Block content (between {})
        if part.startswith('{') and part.endswith('}'):
            output.append(part)
            i += 1
            continue
        
        # This should be selectors or whitespace
        # Scope the selectors
        output.append(scope_selectors(part))
        i += 1
    
    return ''.join(output)

def scope_selectors(text):
    """Scope CSS selectors in a text chunk that appears before a { block"""
    if not text.strip():
        return text
    
    # Don't touch comments
    if text.strip().startswith('/*'):
        return text
    
    # Don't touch @media closing braces or other @-rules
    if text.strip().startswith('@') or text.strip() == '}':
        return text
    
    # Split by comma for multiple selectors
    # But we need to preserve whitespace/newlines structure
    # Simple approach: find selector-like content and prefix it
    
    selectors = text.split(',')
    scoped = []
    for sel in selectors:
        s = sel.strip()
        if not s:
            scoped.append(sel)
            continue
        
        # Handle closing brace leftover
        leading_brace = ''
        if s.startswith('}'):
            leading_brace = '}\n'
            s = s[1:].strip()
            if not s:
                scoped.append(leading_brace)
                continue
        
        scoped_sel = scope_single_selector(s)
        
        # Preserve leading whitespace
        leading_ws = sel[:len(sel) - len(sel.lstrip())]
        scoped.append(leading_brace + leading_ws + scoped_sel)
    
    return ','.join(scoped)

def scope_single_selector(sel):
    """Prefix a single CSS selector with .jp-embed"""
    if not sel:
        return sel
    
    # :root -> .jp-embed
    if sel == ':root':
        return '.jp-embed'
    
    # html -> .jp-embed  
    if sel == 'html':
        return '.jp-embed'
    
    # body -> .jp-embed
    if sel == 'body':
        return '.jp-embed'
    
    # *, *::before, *::after -> .jp-embed *, etc.
    if sel.startswith('*'):
        return '.jp-embed ' + sel
    
    # Element selectors (img, a, h1, h2, h3, h4, etc.)
    bare_elements = ['img', 'a', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'ul', 'li', 'ol', 'form', 'input', 'textarea', 'button', 'section', 'div', 'span']
    for elem in bare_elements:
        if sel == elem or sel.startswith(elem + ' ') or sel.startswith(elem + ':') or sel.startswith(elem + '['):
            return '.jp-embed ' + sel
    
    # Class selectors already - prefix with .jp-embed
    if sel.startswith('.'):
        return '.jp-embed ' + sel
    
    # Anything else, prefix
    return '.jp-embed ' + sel

for f in sys.argv[1:]:
    scope_file(f)
