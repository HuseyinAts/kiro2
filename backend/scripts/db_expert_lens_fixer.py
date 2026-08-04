import os
import re
import glob

def parse_balanced_parentheses(text, start_idx):
    """Returns the index of the matching closing parenthesis."""
    count = 0
    for i in range(start_idx, len(text)):
        if text[i] == '(':
            count += 1
        elif text[i] == ')':
            count -= 1
            if count == 0:
                return i
    return -1

def analyze_and_fix_models():
    models_dir = os.path.join(os.path.dirname(__file__), '../models')
    model_files = glob.glob(os.path.join(models_dir, '*.py'))
    
    total_lazy_fixes = 0
    total_deferred_fixes = 0
    total_index_fixes = 0
    
    for filepath in model_files:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        original_content = content
        
        # Fix 1: N+1 Query Traps - lazy="selectin"
        idx = 0
        while True:
            idx = content.find('relationship(', idx)
            if idx == -1:
                break
            
            end_idx = parse_balanced_parentheses(content, idx + len('relationship') - 1)
            if end_idx != -1:
                inside = content[idx + len('relationship('):end_idx]
                if 'lazy=' not in inside and 'lazy =' not in inside:
                    # Inject lazy="selectin"
                    if inside.strip() == "":
                        injection = 'lazy="selectin"'
                    else:
                        injection = ', lazy="selectin"'
                    
                    content = content[:end_idx] + injection + content[end_idx:]
                    total_lazy_fixes += 1
                    # Skip past this relationship
                    idx = end_idx + len(injection)
                else:
                    idx = end_idx
            else:
                idx += 1

        # Fix 2: Large Text/JSON columns deferred=True
        # mapped_column(Text...) or mapped_column(JSON...)
        idx = 0
        while True:
            idx = content.find('mapped_column(', idx)
            if idx == -1:
                break
            
            end_idx = parse_balanced_parentheses(content, idx + len('mapped_column') - 1)
            if end_idx != -1:
                inside = content[idx + len('mapped_column('):end_idx]
                # Check if it contains Text, JSON, JSONB (make sure it's the type)
                if re.search(r'\b(Text|JSON|JSONB)\b', inside) and 'deferred=' not in inside and 'deferred =' not in inside:
                    injection = ', deferred=True'
                    content = content[:end_idx] + injection + content[end_idx:]
                    total_deferred_fixes += 1
                    idx = end_idx + len(injection)
                else:
                    idx = end_idx
            else:
                idx += 1
                
        # Fix 3: is_active index
        # We can just do a regex replace for this one because it's a single line usually
        def replacer_index(match):
            nonlocal total_index_fixes
            inside = match.group(1)
            if 'index=' not in inside and 'index =' not in inside:
                total_index_fixes += 1
                return f'is_active: Mapped[bool] = mapped_column({inside}, index=True'
            return match.group(0)
            
        content = re.sub(r'is_active:\s*Mapped\[bool\]\s*=\s*mapped_column\(([^)]*)', replacer_index, content)

        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
                
    print(f"Total N+1 Traps fixed (added lazy='selectin'): {total_lazy_fixes}")
    print(f"Total Large Columns Deferred (added deferred=True): {total_deferred_fixes}")
    print(f"Total is_active Indexes added: {total_index_fixes}")

if __name__ == '__main__':
    analyze_and_fix_models()
