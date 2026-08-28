import re

with open('C:/Users/husey/kiro2/frontend/src/App.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace <Routes> with <AnimatedRoutes>
content = content.replace('<Routes>', '<AnimatedRoutes>')
content = content.replace('</Routes>', '</AnimatedRoutes>')
content = content.replace(
    "import { BrowserRouter as Router, Navigate, Route, Routes } from 'react-router-dom';",
    "import { BrowserRouter as Router, Navigate, Route } from 'react-router-dom';\nimport { AnimatedRoutes } from './components/Animations/AnimatedRoutes';"
)

# Remove the outer <PageTransition> around <Suspense>
content = content.replace('<PageTransition variant="fadeUp">\n                  <Suspense fallback={<PageSkeleton />}>\n                    <AnimatedRoutes>', '<Suspense fallback={<PageSkeleton />}>\n                    <AnimatedRoutes>')
content = content.replace('</AnimatedRoutes>\n                  </Suspense>\n                </PageTransition>', '</AnimatedRoutes>\n                  </Suspense>')

idx = 0
while True:
    idx = content.find('element={', idx)
    if idx == -1: break
    start = idx + 9
    brace_count = 1
    end = start
    while end < len(content) and brace_count > 0:
        if content[end] == '{': brace_count += 1
        elif content[end] == '}': brace_count -= 1
        end += 1
    
    inner = content[start:end-1]
    if '<Navigate' not in inner and '<PageTransition' not in inner:
        new_inner = f'<PageTransition>{inner}</PageTransition>'
        content = content[:start] + new_inner + content[end-1:]
        idx = start + len(new_inner)
    else:
        idx = end

with open('C:/Users/husey/kiro2/frontend/src/App.tsx', 'w', encoding='utf-8') as f:
    f.write(content)
print('Done modifying App.tsx')
