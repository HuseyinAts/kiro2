# BÖLÜM 13: Claude Agent SDK

## 13.1 SDK Nedir?

### Tanım

Claude Agent SDK, Claude Code'un yeteneklerini programmatik olarak kullanmak için Anthropic tarafından sağlanan resmi kütüphanedir. Python ve TypeScript versiyonları mevcuttur.

### Temel Kullanım Alanları

| Alan | Açıklama |
|------|----------|
| Custom workflows | Özelleştirilmiş otomasyon akışları |
| CI/CD entegrasyonu | Build pipeline'larında Claude kullanımı |
| Batch processing | Toplu görev işleme |
| API integration | Harici servislerle entegrasyon |
| Testing | Otomatik test ve doğrulama |

### Messages API vs Agent SDK

| Özellik | Messages API | Agent SDK |
|---------|--------------|-----------|
| Amaç | Tek seferlik yanıt | Agentic workflow |
| State | Stateless | Stateful |
| Tools | Manual tanımlama | Built-in tools |
| Loop | Manual implement | Automatic |
| Complexity | Düşük | Orta-Yüksek |

---

## 13.2 Kurulum

### Python

```bash
# pip ile kurulum
pip install anthropic-beta

# veya poetry ile
poetry add anthropic-beta
```

### TypeScript/Node.js

```bash
# npm ile
npm install @anthropic-ai/sdk

# veya yarn ile
yarn add @anthropic-ai/sdk
```

### Doğrulama

```python
# Python
import anthropic
print(anthropic.__version__)

# Agent features check
from anthropic.types.beta import BetaToolUseBlock
print("Agent SDK available")
```

```typescript
// TypeScript
import Anthropic from '@anthropic-ai/sdk';
console.log('Anthropic SDK loaded');
```

---

## 13.3 Temel Kullanım

### Python - Basit Agent Loop

```python
import anthropic
from anthropic.types.beta import (
    BetaMessage,
    BetaToolUseBlock,
    BetaToolResultBlockParam
)

client = anthropic.Anthropic()

def run_agent(prompt: str, tools: list, max_iterations: int = 10) -> str:
    """Basit agent loop implementasyonu."""
    
    messages = [{"role": "user", "content": prompt}]
    
    for iteration in range(max_iterations):
        # Claude'a sor
        response = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=4096,
            tools=tools,
            messages=messages
        )
        
        # Tool use var mı kontrol et
        tool_use_blocks = [
            block for block in response.content 
            if isinstance(block, BetaToolUseBlock)
        ]
        
        if not tool_use_blocks:
            # Tool yok, final response
            return response.content[0].text
        
        # Tool'ları çalıştır
        tool_results = []
        for tool_use in tool_use_blocks:
            result = execute_tool(tool_use.name, tool_use.input)
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": tool_use.id,
                "content": str(result)
            })
        
        # Mesajları güncelle
        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user", "content": tool_results})
    
    return "Max iterations reached"


def execute_tool(name: str, input_data: dict) -> any:
    """Tool'u çalıştır."""
    if name == "read_file":
        with open(input_data["path"], "r") as f:
            return f.read()
    elif name == "write_file":
        with open(input_data["path"], "w") as f:
            f.write(input_data["content"])
        return "File written successfully"
    elif name == "run_command":
        import subprocess
        result = subprocess.run(
            input_data["command"],
            shell=True,
            capture_output=True,
            text=True
        )
        return result.stdout or result.stderr
    else:
        return f"Unknown tool: {name}"
```

### Tool Tanımlama

```python
tools = [
    {
        "name": "read_file",
        "description": "Read contents of a file",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to the file to read"
                }
            },
            "required": ["path"]
        }
    },
    {
        "name": "write_file",
        "description": "Write content to a file",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to write to"
                },
                "content": {
                    "type": "string",
                    "description": "Content to write"
                }
            },
            "required": ["path", "content"]
        }
    },
    {
        "name": "run_command",
        "description": "Run a shell command",
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "Command to execute"
                }
            },
            "required": ["command"]
        }
    }
]
```

---

## 13.4 TypeScript Implementation

### Temel Agent

```typescript
import Anthropic from '@anthropic-ai/sdk';

const client = new Anthropic();

interface Tool {
  name: string;
  description: string;
  input_schema: {
    type: 'object';
    properties: Record<string, any>;
    required: string[];
  };
}

async function runAgent(
  prompt: string,
  tools: Tool[],
  maxIterations: number = 10
): Promise<string> {
  const messages: Anthropic.MessageParam[] = [
    { role: 'user', content: prompt }
  ];

  for (let i = 0; i < maxIterations; i++) {
    const response = await client.messages.create({
      model: 'claude-sonnet-4-5-20250929',
      max_tokens: 4096,
      tools,
      messages
    });

    // Tool use kontrolü
    const toolUseBlocks = response.content.filter(
      (block): block is Anthropic.ToolUseBlock => block.type === 'tool_use'
    );

    if (toolUseBlocks.length === 0) {
      // Final response
      const textBlock = response.content.find(
        (block): block is Anthropic.TextBlock => block.type === 'text'
      );
      return textBlock?.text || '';
    }

    // Tool'ları çalıştır
    const toolResults: Anthropic.ToolResultBlockParam[] = [];
    for (const toolUse of toolUseBlocks) {
      const result = await executeTool(toolUse.name, toolUse.input as Record<string, any>);
      toolResults.push({
        type: 'tool_result',
        tool_use_id: toolUse.id,
        content: String(result)
      });
    }

    // Mesajları güncelle
    messages.push({ role: 'assistant', content: response.content });
    messages.push({ role: 'user', content: toolResults });
  }

  return 'Max iterations reached';
}

async function executeTool(name: string, input: Record<string, any>): Promise<any> {
  const fs = await import('fs/promises');
  const { exec } = await import('child_process');
  const util = await import('util');
  const execPromise = util.promisify(exec);

  switch (name) {
    case 'read_file':
      return await fs.readFile(input.path, 'utf-8');
    case 'write_file':
      await fs.writeFile(input.path, input.content);
      return 'File written successfully';
    case 'run_command':
      const { stdout, stderr } = await execPromise(input.command);
      return stdout || stderr;
    default:
      return `Unknown tool: ${name}`;
  }
}
```

---

## 13.5 Streaming

### Python Streaming

```python
import anthropic

client = anthropic.Anthropic()

def stream_response(prompt: str):
    """Streaming yanıt al."""
    
    with client.messages.stream(
        model="claude-sonnet-4-5-20250929",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}]
    ) as stream:
        for text in stream.text_stream:
            print(text, end="", flush=True)
        print()  # Newline at end

# Kullanım
stream_response("Explain quantum computing in simple terms.")
```

### TypeScript Streaming

```typescript
import Anthropic from '@anthropic-ai/sdk';

const client = new Anthropic();

async function streamResponse(prompt: string): Promise<void> {
  const stream = await client.messages.stream({
    model: 'claude-sonnet-4-5-20250929',
    max_tokens: 4096,
    messages: [{ role: 'user', content: prompt }]
  });

  for await (const event of stream) {
    if (event.type === 'content_block_delta' && 
        event.delta.type === 'text_delta') {
      process.stdout.write(event.delta.text);
    }
  }
  console.log(); // Newline
}
```

---

## 13.6 Error Handling

### Python Error Handling

```python
import anthropic
from anthropic import APIError, RateLimitError, APIConnectionError

client = anthropic.Anthropic()

def safe_api_call(prompt: str, max_retries: int = 3) -> str:
    """Hata yönetimi ile API çağrısı."""
    
    for attempt in range(max_retries):
        try:
            response = client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
            
        except RateLimitError as e:
            # Rate limit - exponential backoff
            wait_time = 2 ** attempt
            print(f"Rate limited. Waiting {wait_time}s...")
            import time
            time.sleep(wait_time)
            
        except APIConnectionError as e:
            # Network error
            print(f"Connection error: {e}")
            if attempt == max_retries - 1:
                raise
            import time
            time.sleep(1)
            
        except APIError as e:
            # Genel API hatası
            print(f"API error: {e.status_code} - {e.message}")
            raise
    
    raise Exception("Max retries exceeded")
```

### TypeScript Error Handling

```typescript
import Anthropic from '@anthropic-ai/sdk';

const client = new Anthropic();

async function safeApiCall(
  prompt: string,
  maxRetries: number = 3
): Promise<string> {
  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      const response = await client.messages.create({
        model: 'claude-sonnet-4-5-20250929',
        max_tokens: 1024,
        messages: [{ role: 'user', content: prompt }]
      });
      
      const textBlock = response.content.find(
        (block): block is Anthropic.TextBlock => block.type === 'text'
      );
      return textBlock?.text || '';
      
    } catch (error) {
      if (error instanceof Anthropic.RateLimitError) {
        const waitTime = Math.pow(2, attempt) * 1000;
        console.log(`Rate limited. Waiting ${waitTime}ms...`);
        await new Promise(resolve => setTimeout(resolve, waitTime));
        
      } else if (error instanceof Anthropic.APIConnectionError) {
        console.log(`Connection error: ${error.message}`);
        if (attempt === maxRetries - 1) throw error;
        await new Promise(resolve => setTimeout(resolve, 1000));
        
      } else if (error instanceof Anthropic.APIError) {
        console.log(`API error: ${error.status} - ${error.message}`);
        throw error;
        
      } else {
        throw error;
      }
    }
  }
  
  throw new Error('Max retries exceeded');
}
```

---

## 13.7 KIRO2 SDK Entegrasyonu

### Soru Üretim Servisi

```python
# orchestrator/services/question_generator.py

import anthropic
from dataclasses import dataclass
from typing import Optional
import json

@dataclass
class QuestionRequest:
    topic: str
    subtopic: Optional[str] = None
    difficulty: int = 3
    exam_type: str = "AYT"
    count: int = 1

@dataclass
class GeneratedQuestion:
    question_id: str
    question_text: str
    options: dict
    correct_answer: str
    difficulty_level: int
    explanation: str
    solution_steps: list

class QuestionGeneratorService:
    """Claude SDK kullanarak soru üretim servisi."""
    
    def __init__(self):
        self.client = anthropic.Anthropic()
        self.model = "claude-sonnet-4-5-20250929"
        self.system_prompt = self._load_system_prompt()
        self.tools = self._define_tools()
    
    def _load_system_prompt(self) -> str:
        return """You are KIRO2 Question Generator, an expert in creating 
        Turkish university entrance exam (YKS) questions.
        
        Guidelines:
        - Generate curriculum-aligned questions
        - Use LaTeX for math: $...$ or $$...$$
        - UTF-8 encoding for Turkish characters
        - Include detailed solution steps
        - Create plausible distractors based on common errors
        """
    
    def _define_tools(self) -> list:
        return [
            {
                "name": "save_question",
                "description": "Save a generated question to the database",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "question": {
                            "type": "object",
                            "properties": {
                                "question_id": {"type": "string"},
                                "question_text": {"type": "string"},
                                "options": {"type": "object"},
                                "correct_answer": {"type": "string"},
                                "difficulty_level": {"type": "integer"},
                                "topic_tags": {"type": "array", "items": {"type": "string"}},
                                "explanation": {"type": "string"},
                                "solution_steps": {"type": "array", "items": {"type": "string"}}
                            },
                            "required": ["question_id", "question_text", "options", 
                                       "correct_answer", "difficulty_level"]
                        }
                    },
                    "required": ["question"]
                }
            },
            {
                "name": "check_duplicate",
                "description": "Check if a similar question exists",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "question_text": {"type": "string"}
                    },
                    "required": ["question_text"]
                }
            }
        ]
    
    def generate(self, request: QuestionRequest) -> list[GeneratedQuestion]:
        """Soru üret."""
        
        prompt = f"""Generate {request.count} {request.exam_type} question(s) about:
        Topic: {request.topic}
        Subtopic: {request.subtopic or 'Any'}
        Difficulty: {request.difficulty}/5
        
        For each question:
        1. First check for duplicates using check_duplicate tool
        2. If no duplicate, save using save_question tool
        3. Include detailed solution steps
        """
        
        messages = [{"role": "user", "content": prompt}]
        generated = []
        
        # Agent loop
        for _ in range(20):  # Max iterations
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=self.system_prompt,
                tools=self.tools,
                messages=messages
            )
            
            # Tool use kontrolü
            tool_uses = [b for b in response.content if b.type == "tool_use"]
            
            if not tool_uses:
                break
            
            # Tool'ları çalıştır
            tool_results = []
            for tool_use in tool_uses:
                result = self._execute_tool(tool_use.name, tool_use.input)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_use.id,
                    "content": json.dumps(result)
                })
                
                # Başarılı kayıt ise listeye ekle
                if tool_use.name == "save_question" and result.get("success"):
                    generated.append(
                        GeneratedQuestion(**tool_use.input["question"])
                    )
            
            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": tool_results})
        
        return generated
    
    def _execute_tool(self, name: str, input_data: dict) -> dict:
        """Tool'u çalıştır."""
        
        if name == "save_question":
            # Veritabanına kaydet (mock)
            return {
                "success": True,
                "question_id": input_data["question"]["question_id"]
            }
        
        elif name == "check_duplicate":
            # Duplicate kontrolü (mock)
            return {
                "is_duplicate": False,
                "similarity_score": 0.0
            }
        
        return {"error": f"Unknown tool: {name}"}


# Kullanım
if __name__ == "__main__":
    service = QuestionGeneratorService()
    
    request = QuestionRequest(
        topic="limit",
        subtopic="belirsizlik giderme",
        difficulty=3,
        exam_type="AYT",
        count=2
    )
    
    questions = service.generate(request)
    
    for q in questions:
        print(f"Generated: {q.question_id}")
        print(f"Text: {q.question_text[:100]}...")
        print("---")
```

---

## 13.8 Best Practices

### 1. Model Seçimi

```python
# Görev karmaşıklığına göre model seç
def select_model(task_complexity: str) -> str:
    models = {
        "simple": "claude-haiku-4-5-20251001",
        "medium": "claude-sonnet-4-5-20250929",
        "complex": "claude-opus-4-5-20251101"
    }
    return models.get(task_complexity, "claude-sonnet-4-5-20250929")
```

### 2. Token Yönetimi

```python
def estimate_tokens(text: str) -> int:
    """Kabaca token tahmini."""
    # Türkçe için karakter/token oranı ~2.5
    return len(text) // 2

def check_context_limit(messages: list, max_tokens: int = 180000) -> bool:
    """Context limit kontrolü."""
    total = sum(estimate_tokens(str(m)) for m in messages)
    return total < max_tokens
```

### 3. Rate Limiting

```python
import time
from functools import wraps

def rate_limit(calls_per_minute: int = 60):
    """Rate limiting decorator."""
    interval = 60.0 / calls_per_minute
    last_call = [0.0]
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            elapsed = time.time() - last_call[0]
            if elapsed < interval:
                time.sleep(interval - elapsed)
            last_call[0] = time.time()
            return func(*args, **kwargs)
        return wrapper
    return decorator

@rate_limit(calls_per_minute=50)
def api_call(prompt: str):
    # API çağrısı
    pass
```

### 4. Caching

```python
import hashlib
import json
from functools import lru_cache

def cache_key(prompt: str, model: str) -> str:
    """Cache key oluştur."""
    data = f"{model}:{prompt}"
    return hashlib.sha256(data.encode()).hexdigest()[:16]

# Simple in-memory cache
response_cache = {}

def cached_api_call(prompt: str, model: str = "claude-sonnet-4-5-20250929"):
    """Cacheli API çağrısı."""
    key = cache_key(prompt, model)
    
    if key in response_cache:
        return response_cache[key]
    
    response = client.messages.create(
        model=model,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}]
    )
    
    result = response.content[0].text
    response_cache[key] = result
    return result
```

---

## 13.9 Özet

### Checklist

- [ ] SDK kuruldu ve doğrulandı
- [ ] Agent loop implementasyonu tamamlandı
- [ ] Tool tanımları yapıldı
- [ ] Error handling eklendi
- [ ] Streaming desteği (opsiyonel)
- [ ] Rate limiting implementasyonu
- [ ] Caching stratejisi

### Quick Reference

```python
# Temel kullanım
import anthropic

client = anthropic.Anthropic()

response = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    system="System prompt here",
    tools=[...],
    messages=[{"role": "user", "content": "..."}]
)
```

### Metrikler

| Metrik | Hedef |
|--------|-------|
| API success rate | > 99% |
| Average latency | < 2s |
| Cache hit rate | > 60% |
| Token efficiency | > 80% |

---

**Önceki Bölüm:** [12 - MCP Entegrasyonları](./12-mcp-entegrasyonlari.md)  
**Sonraki Bölüm:** [14 - GitHub Actions Entegrasyonu](./14-github-actions.md)
