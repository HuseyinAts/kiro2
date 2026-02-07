# Edit Prompt Technique

## Problem: Traditional Iteration Wastes Tokens

**Traditional approach (inefficient)**:
1. Claude shows full file (1000+ lines)
2. You review and request changes
3. Claude shows full file again with edits
4. Repeat 10 times = **~25,000 tokens wasted**

## Solution: Edit Prompts (67% Savings)

**Edit prompt approach**:
```
Edit /path/to/file.ts:
- Line 45: Change `const x = 5` to `const x = 10`
- After line 67: Add `console.log('Debug')`
- Lines 100-105: Remove (delete these lines)
- Line 200: Replace entire function with: [new code]
```

**Result**: Only changes are shown, not full file
**Savings**: 10 iterations = ~3,000 tokens (83% less!)

## When to Use

- ✅ Modifying existing files
- ✅ Making multiple small changes
- ✅ Working near token limits
- ❌ Creating new files (use create_file)
- ❌ Need to review full context

## Template

```
Edit [filepath]:
- [Line number/range]: [Action] [Description]
- [After/Before line X]: [Add/Remove] [Content]
```

## Examples

### Python
```
Edit backend/app/main.py:
- Line 15: Change timeout from 30 to 60
- After line 45: Add new endpoint: [code]
- Lines 100-110: Remove deprecated function
```

### TypeScript
```
Edit frontend/src/App.tsx:
- Line 23: Replace useState with useReducer
- After line 67: Add error boundary: [code]
```

## Verification

After edit:
1. Run tests
2. Check build
3. Review git diff

Save **50,000+ tokens per project** with this technique!
