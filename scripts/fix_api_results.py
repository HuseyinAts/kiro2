f = r'C:\Users\husey\kiro2\backend\api\elasticsearch.py'
content = open(f, encoding='utf-8').read()

# Result nesneleri dict olarak geliyor, attribute yerine .get() kullan
replacements = [
    # Pattern: 4-satir blok (question search ve content search)
    (
        '                    "id": result.id,\n'
        '                    "score": result.score,\n'
        '                    "source": result.source,\n'
        '                    "highlight": result.highlight,',
        '                    "id": result.get("id", result.get("_id", "")),\n'
        '                    "score": result.get("_score"),\n'
        '                    "source": result,\n'
        '                    "highlight": result.get("highlight", {}),',
    ),
    # Pattern: satir ici (similar questions)
    (
        '{"id": result.id, "score": result.score, "source": result.source}',
        '{"id": result.get("id", result.get("_id", "")), "score": result.get("_score"), "source": result}',
    ),
]

count = 0
for old, new in replacements:
    occurrences = content.count(old)
    if occurrences > 0:
        content = content.replace(old, new)
        count += occurrences
        print(f'Fixed {occurrences}x: {old[:50].strip()}...')
    else:
        print(f'NOT FOUND: {old[:50].strip()}...')

open(f, 'w', encoding='utf-8').write(content)
print(f'Total replacements: {count}')
