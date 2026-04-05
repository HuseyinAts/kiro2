import os

f = r'C:\Users\husey\kiro2\backend\services\elasticsearch_service.py'
content = open(f, encoding='utf-8').read()

# Fix 1: QuestionSearchService index name
old1 = '        self.index_name = "questions"'
new1 = ('        import os as _os\n'
        '        self.index_name = _os.environ.get("ELASTICSEARCH_INDEX", "turkiye_sinav_platform")')

# Fix 2: ContentSearchService index name
old2 = '        self.index_name = "content"'
new2 = ('        import os as _os\n'
        '        self.index_name = _os.environ.get("ELASTICSEARCH_INDEX", "turkiye_sinav_platform")')

count = 0
if old1 in content:
    content = content.replace(old1, new1, 1)
    count += 1
    print('Fixed: QuestionSearchService index_name')
else:
    print('NOT FOUND: QuestionSearchService index_name')

if old2 in content:
    content = content.replace(old2, new2, 1)
    count += 1
    print('Fixed: ContentSearchService index_name')
else:
    print('NOT FOUND: ContentSearchService index_name')

open(f, 'w', encoding='utf-8').write(content)
print(f'Total fixes: {count}')
