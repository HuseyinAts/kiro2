f = r'C:\Users\husey\kiro2\backend\services\elasticsearch_service.py'
content = open(f, encoding='utf-8').read()

# Fix search_fields to match actual index mapping
old = '        search_fields = ["text^2", "explanation", "options.text"]'
new = '        search_fields = ["question_text^3", "option_a", "option_b", "option_c", "option_d", "option_e", "explanation"]'

if old in content:
    content = content.replace(old, new)
    open(f, 'w', encoding='utf-8').write(content)
    print('OK: search_fields fixed')
else:
    print('NOT FOUND')
    idx = content.find('search_fields')
    print(repr(content[idx:idx+100]))
