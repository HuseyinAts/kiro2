# Visual Question Support Roadmap - Tables, Charts & Diagrams

**Current Status**: Text-only questions ❌
**Target**: Full visual support (tables, charts, diagrams, images) ✅
**Priority**: HIGH (ÖSYM questions heavily use visuals)
**Timeline**: Month 2-3 implementation

---

## Problem Analysis

### Current Limitation

**What We Have Now**:
- ✅ Text-based questions (Mathematics, Turkish)
- ✅ Enhanced templates for context
- ✅ Wave 2B quality evaluation
- ❌ **NO tables, charts, diagrams, or images**

**Why This Is a Problem**:
1. **ÖSYM Reality**: 40-60% of questions include visual elements
2. **Subject Requirements**:
   - Mathematics: Graphs, geometric figures, tables (60% of questions)
   - Physics: Diagrams, circuits, force diagrams (80% of questions)
   - Chemistry: Molecular structures, reaction diagrams (70% of questions)
   - Biology: Cell diagrams, graphs, tables (65% of questions)
   - Geography: Maps, charts, demographic tables (90% of questions)
   - Turkish: Sometimes includes text formatting, tables

**Impact**: Without visuals, we're missing 40-60% of authentic ÖSYM question types!

---

## ÖSYM Visual Types Analysis

### Type 1: Tables (Tablolar) - **MOST COMMON**

**Usage**: 35-40% of all questions

**Examples**:
- Data tables (veri tablosu)
- Comparison tables (karşılaştırma tablosu)
- Statistical tables (istatistik tablosu)
- Periodic table (periyodik tablo - Chemistry)
- Truth tables (doğruluk tablosu - Logic)

**Subjects**: All (especially Math, Science, Geography)

**Difficulty**: ⭐⭐ MEDIUM (can generate as HTML/Markdown/LaTeX)

---

### Type 2: Mathematical Graphs (Grafikler)

**Usage**: 25-30% of Math/Physics questions

**Examples**:
- Function graphs (f(x) grafiği)
- Line graphs (çizgi grafik)
- Bar charts (sütun grafik)
- Pie charts (pasta grafik)
- Coordinate systems (koordinat sistemi)

**Subjects**: Mathematics, Physics, Chemistry, Geography

**Difficulty**: ⭐⭐⭐ MEDIUM-HIGH (need graphing library)

---

### Type 3: Geometric Figures (Geometrik Şekiller)

**Usage**: 40-50% of Math/Physics questions

**Examples**:
- Triangles, circles, polygons (üçgen, daire, çokgen)
- 3D shapes (3 boyutlu şekiller)
- Angle diagrams (açı şemaları)
- Geometric constructions (geometrik çizimler)

**Subjects**: Mathematics, Physics

**Difficulty**: ⭐⭐⭐⭐ HIGH (need geometry rendering)

---

### Type 4: Scientific Diagrams (Bilimsel Şemalar)

**Usage**: 60-80% of Science questions

**Examples**:
- Circuit diagrams (devre şemaları - Physics)
- Molecular structures (molekül yapıları - Chemistry)
- Cell diagrams (hücre şemaları - Biology)
- Force diagrams (kuvvet diyagramları - Physics)
- Reaction mechanisms (tepkime mekanizmaları - Chemistry)

**Subjects**: Physics, Chemistry, Biology

**Difficulty**: ⭐⭐⭐⭐⭐ VERY HIGH (complex domain-specific rendering)

---

### Type 5: Maps & Geographic Visuals (Haritalar)

**Usage**: 80-90% of Geography questions

**Examples**:
- Political maps (siyasi harita)
- Physical maps (fiziki harita)
- Climate maps (iklim haritası)
- Population density maps (nüfus yoğunluğu haritası)

**Subjects**: Geography, History

**Difficulty**: ⭐⭐⭐⭐⭐ VERY HIGH (specialized mapping)

---

### Type 6: Images/Photos (Fotoğraflar)

**Usage**: 10-15% of questions

**Examples**:
- Historical photos (tarihî fotoğraflar)
- Biological specimens (biyolojik örnekler)
- Artwork (sanat eserleri)
- Real-world objects (gerçek nesneler)

**Subjects**: History, Biology, Art

**Difficulty**: ⭐⭐⭐⭐⭐ VERY HIGH (need image database or generation)

---

## Solution Architecture

### Phase 1: Tables Support (IMMEDIATE - Month 2) ⭐

**Goal**: Add table generation to all subjects

**Implementation Options**:

#### Option A: Markdown Tables (RECOMMENDED for MVP)
```markdown
| Header 1 | Header 2 | Header 3 |
|----------|----------|----------|
| Data 1   | Data 2   | Data 3   |
| Data 4   | Data 5   | Data 6   |
```

**Pros**:
- ✅ Easy to generate with LLM
- ✅ Human-readable
- ✅ Converts to HTML easily
- ✅ Works in frontend (React renders markdown)

**Cons**:
- ⚠️ Limited formatting options

#### Option B: HTML Tables
```html
<table>
  <thead>
    <tr><th>Header 1</th><th>Header 2</th></tr>
  </thead>
  <tbody>
    <tr><td>Data 1</td><td>Data 2</td></tr>
  </tbody>
</table>
```

**Pros**:
- ✅ Full control over styling
- ✅ Native web support

**Cons**:
- ⚠️ More verbose
- ⚠️ Requires HTML sanitization

#### Option C: JSON Table Data
```json
{
  "type": "table",
  "headers": ["Column 1", "Column 2"],
  "rows": [
    ["Data 1", "Data 2"],
    ["Data 3", "Data 4"]
  ]
}
```

**Pros**:
- ✅ Structured data
- ✅ Frontend can render however it wants
- ✅ Easy to validate

**Cons**:
- ⚠️ Requires frontend table component

**RECOMMENDATION**: **Option A (Markdown) for MVP**, migrate to Option C for production

**Implementation Steps**:
1. Update `osym_inspired_generator.py` to request tables when appropriate
2. Add table detection in prompts:
   ```python
   "If question requires data comparison, include a markdown table"
   ```
3. Update database schema to support markdown content
4. Add frontend markdown renderer (already available in React)

**Estimated Time**: 4-6 hours
**Difficulty**: ⭐⭐ MEDIUM

---

### Phase 2: Mathematical Graphs (Month 2-3) ⭐⭐

**Goal**: Generate function graphs, charts, coordinate systems

**Implementation Options**:

#### Option A: Matplotlib (Python) - Server-Side Generation
```python
import matplotlib.pyplot as plt
import numpy as np

def generate_function_graph(equation, x_range):
    x = np.linspace(x_range[0], x_range[1], 100)
    y = eval(equation)  # e.g., "x**2 + 2*x + 1"

    plt.plot(x, y)
    plt.grid(True)
    plt.xlabel('x')
    plt.ylabel('f(x)')

    # Save to base64 or file
    plt.savefig('graph.png')
    return 'graph.png'
```

**Pros**:
- ✅ Full control over graphs
- ✅ Python ecosystem
- ✅ Generate PNG/SVG
- ✅ ÖSYM-style styling possible

**Cons**:
- ⚠️ Server-side only
- ⚠️ File storage needed

#### Option B: Plotly (Interactive) - JavaScript
```javascript
const data = [{
  x: [1, 2, 3, 4],
  y: [10, 15, 13, 17],
  type: 'scatter'
}];

Plotly.newPlot('graph', data);
```

**Pros**:
- ✅ Interactive graphs
- ✅ Client-side rendering
- ✅ Beautiful visualizations

**Cons**:
- ⚠️ Not matching ÖSYM style (static)
- ⚠️ Requires frontend integration

#### Option C: LaTeX/TikZ (Academic Quality)
```latex
\begin{tikzpicture}
  \begin{axis}
    \addplot[blue] {x^2};
  \end{axis}
\end{tikzpicture}
```

**Pros**:
- ✅ Academic quality
- ✅ ÖSYM uses similar
- ✅ Vector graphics (SVG)

**Cons**:
- ⚠️ Requires LaTeX installation
- ⚠️ Complex setup

**RECOMMENDATION**: **Matplotlib for MVP** (proven, ÖSYM-compatible)

**Implementation Steps**:
1. Create `services/graph_generator.py`
2. Define graph types: function, scatter, bar, pie
3. Generate as PNG/SVG
4. Store in CDN or S3
5. Reference in question JSON

**Estimated Time**: 8-12 hours
**Difficulty**: ⭐⭐⭐ MEDIUM-HIGH

---

### Phase 3: Geometric Figures (Month 3) ⭐⭐⭐

**Goal**: Generate triangles, circles, angles, 3D shapes

**Implementation Options**:

#### Option A: Matplotlib Patches
```python
import matplotlib.patches as patches

fig, ax = plt.subplots()
triangle = patches.Polygon([[0,0], [1,0], [0.5,0.866]], closed=True)
ax.add_patch(triangle)
```

**Pros**:
- ✅ Same as graphs (consistency)
- ✅ Label support

**Cons**:
- ⚠️ Limited 3D support

#### Option B: Asymptote (Geometry Specialized)
```asymptote
draw(circle((0,0), 1));
draw((0,0)--(1,0)--(0.5,0.866)--cycle);
```

**Pros**:
- ✅ Geometry-focused
- ✅ Vector output
- ✅ 3D support

**Cons**:
- ⚠️ Additional dependency
- ⚠️ Less common

#### Option C: SVG Direct Generation
```python
svg = f'''
<svg width="200" height="200">
  <polygon points="100,10 190,190 10,190"
           fill="none" stroke="black" />
</svg>
'''
```

**Pros**:
- ✅ Full control
- ✅ Lightweight
- ✅ Web-native

**Cons**:
- ⚠️ Manual coordinate calculation
- ⚠️ Complex for 3D

**RECOMMENDATION**: **Matplotlib for 2D**, **Asymptote for 3D** (if needed)

**Estimated Time**: 12-16 hours
**Difficulty**: ⭐⭐⭐⭐ HIGH

---

### Phase 4: Scientific Diagrams (Month 4-5) ⭐⭐⭐⭐

**Goal**: Circuit diagrams, molecular structures, cell diagrams

**Implementation**: **Domain-specific libraries**

#### Physics - Circuit Diagrams
**Library**: `SchemDraw` (Python)
```python
import schemdraw
import schemdraw.elements as elm

with schemdraw.Drawing() as d:
    d += elm.Resistor().label('R1')
    d += elm.Capacitor().label('C1')
```

**Estimated Time**: 16-20 hours per subject
**Difficulty**: ⭐⭐⭐⭐⭐ VERY HIGH

#### Chemistry - Molecular Structures
**Library**: `RDKit` (Python)
```python
from rdkit import Chem
from rdkit.Chem import Draw

mol = Chem.MolFromSmiles('CCO')  # Ethanol
Draw.MolToImage(mol)
```

**Estimated Time**: 16-20 hours
**Difficulty**: ⭐⭐⭐⭐⭐ VERY HIGH

#### Biology - Cell Diagrams
**Option**: Custom SVG templates or Biorender API

**Estimated Time**: 20-30 hours
**Difficulty**: ⭐⭐⭐⭐⭐ VERY HIGH

**RECOMMENDATION**: **Phase 4 is OPTIONAL** - focus on Phases 1-3 first

---

### Phase 5: Maps & Images (Month 5-6) - OPTIONAL ⭐⭐⭐⭐⭐

**Goal**: Geographic maps, historical images

**Implementation**: **External APIs or image databases**

**Options**:
- Google Maps API (for geography)
- Image databases (for historical photos)
- AI image generation (DALL-E, Stable Diffusion)

**RECOMMENDATION**: **LOW PRIORITY** - most value in Phases 1-3

---

## Recommended Implementation Roadmap

### Month 2: Tables Support (MUST HAVE) ⭐

**Week 1**:
- [ ] Update question schema to support markdown/HTML
- [ ] Add table generation to enhanced templates
- [ ] Test with 10 Math questions (data tables)
- [ ] Test with 10 Chemistry questions (periodic table data)

**Week 2**:
- [ ] Frontend: Add markdown renderer
- [ ] Backend: Validate table generation
- [ ] Create 25 questions with tables
- [ ] Document table formatting standards

**Success Criteria**:
- Tables render correctly in frontend
- 80%+ of table-based questions approved by Wave 2B
- Clean, ÖSYM-style formatting

**Estimated Effort**: 12-16 hours
**Risk**: LOW ✅

---

### Month 3: Mathematical Graphs (HIGH VALUE) ⭐⭐

**Week 1**:
- [ ] Set up Matplotlib graph generator
- [ ] Define graph types (function, scatter, bar, pie)
- [ ] Create storage solution (S3/CDN)
- [ ] Test with 10 Math function questions

**Week 2**:
- [ ] Integrate graph generation into question pipeline
- [ ] Add graph type detection to prompts
- [ ] Generate 25 questions with graphs
- [ ] Validate quality with Wave 2B

**Success Criteria**:
- Graphs match ÖSYM style
- Clear, readable, properly labeled
- 75%+ approval rate

**Estimated Effort**: 16-20 hours
**Risk**: MEDIUM ⚠️

---

### Month 4: Geometric Figures (NICE TO HAVE) ⭐⭐⭐

**Week 1-2**:
- [ ] Geometry rendering setup
- [ ] Common shapes library (triangles, circles, polygons)
- [ ] Angle and measurement labeling
- [ ] Test with 25 Geometry questions

**Success Criteria**:
- Accurate geometric representations
- Proper labeling and measurements
- 70%+ approval rate

**Estimated Effort**: 20-24 hours
**Risk**: MEDIUM-HIGH ⚠️

---

### Month 5+: Advanced Visuals (OPTIONAL) ⭐⭐⭐⭐

**Only if needed**:
- [ ] Scientific diagrams (circuits, molecules, cells)
- [ ] Maps and geographic visuals
- [ ] Image integration

**Estimated Effort**: 40-60 hours per domain
**Risk**: HIGH ⚠️⚠️

---

## Technical Architecture

### Database Schema Update

```sql
-- Add visual_content field to questions table
ALTER TABLE sorular ADD COLUMN visual_content JSONB;

-- Example structure:
{
  "type": "table",
  "format": "markdown",
  "content": "| Header | Data |\n|--------|------|\n| A | 1 |"
}

-- Or for images:
{
  "type": "graph",
  "format": "png",
  "url": "https://cdn.example.com/graphs/question-123.png",
  "alt_text": "Function f(x) = x^2 graph"
}
```

### Question JSON Format

```json
{
  "id": "q-001",
  "subject": "Matematik",
  "topic": "Fonksiyonlar",
  "stem": "Aşağıdaki grafikte verilen f(x) fonksiyonuna göre...",
  "visual": {
    "type": "graph",
    "url": "https://cdn.example.com/graphs/q-001.png",
    "alt_text": "f(x) = 2x + 3 doğrusal fonksiyon grafiği",
    "width": 400,
    "height": 300
  },
  "options": ["A) 3", "B) 5", "C) 7", "D) 9"],
  "correct_answer": "A"
}
```

### Frontend Component (React)

```typescript
interface VisualContent {
  type: 'table' | 'graph' | 'diagram' | 'image';
  format: 'markdown' | 'html' | 'png' | 'svg';
  content?: string;
  url?: string;
  altText?: string;
}

const QuestionVisual: React.FC<{ visual: VisualContent }> = ({ visual }) => {
  switch (visual.type) {
    case 'table':
      return <MarkdownRenderer content={visual.content} />;
    case 'graph':
    case 'diagram':
    case 'image':
      return <img src={visual.url} alt={visual.altText} />;
    default:
      return null;
  }
};
```

---

## Cost-Benefit Analysis

### Development Costs

| Phase | Time | Cost (@$30/hr) |
|-------|------|----------------|
| Phase 1: Tables | 16 hrs | $480 |
| Phase 2: Graphs | 20 hrs | $600 |
| Phase 3: Geometry | 24 hrs | $720 |
| **Total (MVP)** | **60 hrs** | **$1,800** |

### Benefits

**Question Authenticity**:
- Current: Text-only (60% of ÖSYM types)
- With visuals: 95%+ ÖSYM authenticity ✅

**Subject Coverage**:
- Current: Math (text), Turkish
- With visuals: Math (full), Physics, Chemistry, Biology, Geography

**Student Value**:
- More realistic exam preparation
- Visual learning support
- Better test readiness

**Market Differentiation**:
- Competitors often lack visual questions
- Unique selling point
- Higher perceived value

---

## Risk Assessment

### Technical Risks

1. **Graph Generation Quality** (MEDIUM)
   - Risk: Generated graphs don't match ÖSYM style
   - Mitigation: Style templates, manual QA

2. **Storage Costs** (LOW)
   - Risk: Image storage becomes expensive
   - Mitigation: CDN, compression, lazy loading

3. **Performance** (MEDIUM)
   - Risk: Image generation slows question creation
   - Mitigation: Async generation, caching

### Implementation Risks

1. **Complexity Creep** (HIGH)
   - Risk: Scope expands to all visual types
   - Mitigation: **Stick to Phase 1-2 for MVP**

2. **Frontend Integration** (LOW)
   - Risk: Visual rendering breaks frontend
   - Mitigation: Thorough testing, fallbacks

---

## Success Metrics

### Phase 1 (Tables) - Target: Month 2

- [ ] 100 questions with tables generated
- [ ] 80%+ approval rate maintained
- [ ] Tables render correctly 100% of time
- [ ] Zero frontend errors

### Phase 2 (Graphs) - Target: Month 3

- [ ] 50 questions with graphs generated
- [ ] 75%+ approval rate
- [ ] Graphs match ÖSYM style (manual review)
- [ ] Load time < 2 seconds

### Overall - Target: Month 4

- [ ] 40%+ questions include visuals
- [ ] Visual questions same quality as text (≥0.80)
- [ ] No degradation in approval rates
- [ ] Positive user feedback

---

## Conclusion

**Visual question support is CRITICAL** for authentic ÖSYM preparation.

**Recommended Approach**:
1. ✅ **Phase 1 (Month 2)**: Tables - HIGH VALUE, LOW EFFORT
2. ✅ **Phase 2 (Month 3)**: Graphs - HIGH VALUE, MEDIUM EFFORT
3. ⚠️ **Phase 3 (Month 4)**: Geometry - MEDIUM VALUE, HIGH EFFORT
4. ❌ **Phase 4-5**: Advanced visuals - OPTIONAL, VERY HIGH EFFORT

**Start with tables (Phase 1)** immediately - they cover 35-40% of visual questions with minimal effort!

---

**Roadmap Created**: 2025-11-07
**Priority**: HIGH (next after Turkish improvements)
**Timeline**: Month 2 start
**Expected Impact**: +40% question type coverage
**Status**: ✅ **READY FOR IMPLEMENTATION**
