# BÖLÜM 12: MCP Entegrasyonları

## 12.1 MCP Nedir?

### Tanım

**MCP (Model Context Protocol)**, Anthropic tarafından geliştirilen açık standart protokoldür. AI uygulamalarının harici veri kaynakları ve araçlarla standart bir şekilde iletişim kurmasını sağlar.

### Analoji

> "MCP, AI için USB-C gibidir. Tıpkı USB-C'nin farklı cihazları tek bir standart ile bağladığı gibi, MCP de AI uygulamalarını farklı veri kaynaklarına bağlar."

### Temel Faydalar

| Fayda | Açıklama |
|-------|----------|
| Standardizasyon | Tek protokol, çoklu entegrasyon |
| Modülerlik | Plug-and-play server'lar |
| Güvenlik | İzole sandbox'lar |
| Genişletilebilirlik | Custom server geliştirme |
| Community | Açık kaynak ekosistem |

---

## 12.2 Mimari Bileşenler

### MCP Mimarisi

```
┌─────────────────────────────────────────────────────────────────┐
│                          HOST                                    │
│                (Claude Desktop, Claude Code, IDE)                │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│   ┌───────────────┐  ┌───────────────┐  ┌───────────────┐       │
│   │  MCP Client   │  │  MCP Client   │  │  MCP Client   │       │
│   │   (Built-in)  │  │   (Built-in)  │  │   (Built-in)  │       │
│   └───────┬───────┘  └───────┬───────┘  └───────┬───────┘       │
│           │                  │                  │                │
└───────────┼──────────────────┼──────────────────┼────────────────┘
            │                  │                  │
            │ STDIO/HTTP       │ STDIO/HTTP       │ STDIO/HTTP
            │                  │                  │
            ▼                  ▼                  ▼
    ┌───────────────┐  ┌───────────────┐  ┌───────────────┐
    │  MCP Server   │  │  MCP Server   │  │  MCP Server   │
    │  (Filesystem) │  │   (Memory)    │  │  (PostgreSQL) │
    └───────┬───────┘  └───────┬───────┘  └───────┬───────┘
            │                  │                  │
            ▼                  ▼                  ▼
    ┌───────────────┐  ┌───────────────┐  ┌───────────────┐
    │  Local Files  │  │ Knowledge     │  │   Database    │
    │               │  │ Graph         │  │               │
    └───────────────┘  └───────────────┘  └───────────────┘
```

### Bileşen Açıklamaları

**Host:** MCP'yi çalıştıran uygulama
- Claude Desktop
- Claude Code
- IDE extensions
- Custom applications

**MCP Client:** Host içindeki bağlayıcı
- Server'larla iletişim
- Request/response yönetimi
- Birden fazla client destekli

**MCP Server:** Harici kaynaklara erişim sağlayan sunucu
- Resources (veri okuma)
- Tools (fonksiyon çağırma)
- Prompts (şablon sağlama)

---

## 12.3 Transport Katmanları

### STDIO (Standard Input/Output)

**Kullanım:** Lokal entegrasyonlar

**Avantajlar:**
- Minimum gecikme
- Process isolation
- Basit setup

**Dezavantajlar:**
- Sadece lokal
- Her connection için yeni process

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/dir"]
    }
  }
}
```

### Streamable HTTP (Yeni Standart)

**Kullanım:** Remote server'lar

**Avantajlar:**
- Network üzerinden erişim
- Bidirectional streaming
- Modern standart

**Dezavantajlar:**
- Latency
- Network dependency

```json
{
  "mcpServers": {
    "remote-api": {
      "url": "https://api.example.com/mcp",
      "headers": {
        "Authorization": "Bearer ${API_TOKEN}"
      }
    }
  }
}
```

### SSE (Server-Sent Events) - Legacy

**Kullanım:** Geriye uyumluluk

**Not:** Yeni implementasyonlar için önerilmiyor.

---

## 12.4 Server Yetenekleri

### Resources (Veri Kaynakları)

Read-only veri erişimi sağlar.

**Özellikler:**
- URI tabanlı adreslenme
- MIME type desteği
- Lazy loading

**Örnek:**
```typescript
// Server tarafı
server.resource({
  uri: "file:///documents/report.pdf",
  name: "Q4 Report",
  mimeType: "application/pdf"
});

// Client tarafı
const content = await client.readResource("file:///documents/report.pdf");
```

### Tools (Araçlar)

Fonksiyon çağırma imkanı sağlar.

**Özellikler:**
- JSON Schema parametreler
- Type-safe
- Async execution

**Örnek:**
```typescript
// Server tarafı
server.tool({
  name: "search_questions",
  description: "Search question bank",
  inputSchema: {
    type: "object",
    properties: {
      topic: { type: "string" },
      difficulty: { type: "integer", minimum: 1, maximum: 5 }
    },
    required: ["topic"]
  },
  handler: async ({ topic, difficulty }) => {
    return await questionBank.search(topic, difficulty);
  }
});
```

### Prompts (Şablonlar)

Önceden tanımlı prompt şablonları.

**Örnek:**
```typescript
server.prompt({
  name: "generate_question",
  description: "Generate a YKS question",
  arguments: [
    { name: "topic", description: "Question topic", required: true },
    { name: "difficulty", description: "1-5", required: false }
  ],
  handler: async ({ topic, difficulty }) => {
    return `Generate a ${difficulty || 3} difficulty question about ${topic}...`;
  }
});
```

---

## 12.5 MCP Konfigürasyonu

### Dosya Konumu

**Proje seviyesi:** `.mcp.json` (proje kökünde)

**Global:** `~/.claude/mcp.json`

### Konfigürasyon Formatı

```json
{
  "mcpServers": {
    "server-name": {
      "command": "executable",
      "args": ["arg1", "arg2"],
      "env": {
        "ENV_VAR": "value"
      },
      "cwd": "/working/directory"
    }
  }
}
```

### KIRO2 İçin Tam Konfigürasyon

```json
{
  "mcpServers": {
    "context7": {
      "command": "npx",
      "args": ["-y", "@context7/mcp-server"],
      "env": {}
    },
    "memory": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-memory"],
      "env": {
        "MEMORY_FILE": "./.claude/memory/knowledge-graph.json"
      }
    },
    "filesystem": {
      "command": "npx",
      "args": [
        "-y", 
        "@modelcontextprotocol/server-filesystem",
        "./src",
        "./tests",
        "./docs"
      ],
      "env": {}
    },
    "postgres": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-postgres"],
      "env": {
        "POSTGRES_URL": "postgresql://user:pass@localhost:5434/kiro2"
      }
    },
    "sequential-thinking": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-sequential-thinking"],
      "env": {}
    },
    "brave-search": {
      "command": "npx",
      "args": ["-y", "@anthropic/mcp-server-brave"],
      "env": {
        "BRAVE_API_KEY": "${BRAVE_API_KEY}"
      }
    }
  }
}
```

---

## 12.6 Önerilen MCP Server'lar

### 1. Context7 (Zorunlu)

**Amaç:** Güncel kütüphane dokümantasyonu

**Neden önemli:**
- Claude'un training data'sı outdated olabilir
- API değişiklikleri yakalanır
- Hallucination önlenir

**Kullanım:**
```
"Use context7 to check the latest LangGraph API"
```

**Desteklenen kütüphaneler:**
- Python (FastAPI, Django, Flask, LangChain, etc.)
- JavaScript (React, Next.js, Express, etc.)
- Anthropic SDK
- ve daha fazlası...

### 2. Memory (Zorunlu)

**Amaç:** Kalıcı knowledge graph hafıza

**Özellikler:**
- Entity-relationship storage
- Session arası persistence
- Semantic search

**Kullanım senaryoları:**
- Kullanıcı tercihleri
- Proje bilgisi
- Öğrenilen kurallar

**Örnek entity'ler:**
```json
{
  "entities": [
    {
      "name": "KIRO2",
      "type": "project",
      "observations": [
        "YKS preparation platform",
        "Uses PostgreSQL on port 5434",
        "Python 3.11+ required"
      ]
    },
    {
      "name": "question_generator",
      "type": "module",
      "relations": [
        {"type": "belongs_to", "target": "KIRO2"}
      ]
    }
  ]
}
```

### 3. Filesystem (Dikkatli)

**Amaç:** Güvenli dosya sistemi erişimi

**Güvenlik:**
- Sadece belirtilen dizinlere erişim
- Read-only mod önerilir
- Sensitive dosyaları hariç tut

**Konfigürasyon:**
```json
{
  "filesystem": {
    "command": "npx",
    "args": [
      "-y",
      "@modelcontextprotocol/server-filesystem",
      "--read-only",
      "./src",
      "./docs"
    ]
  }
}
```

### 4. PostgreSQL (KIRO2 Özel)

**Amaç:** Veritabanı entegrasyonu

**Özellikler:**
- SQL query execution
- Schema introspection
- Read-only mode destekli

**Güvenlik uyarısı:**
```json
{
  "postgres": {
    "env": {
      "POSTGRES_URL": "postgresql://readonly_user:pass@localhost:5434/kiro2",
      "POSTGRES_READ_ONLY": "true"
    }
  }
}
```

### 5. Sequential Thinking (Önerilen)

**Amaç:** Karmaşık problem çözme

**Özellikler:**
- Step-by-step reasoning
- Thought persistence
- Backtracking support

**Kullanım:**
```
"Use sequential thinking to solve this complex optimization problem"
```

### 6. Brave Search (Opsiyonel)

**Amaç:** Web araması

**Kullanım senaryoları:**
- Güncel bilgi
- Fact checking
- Research

---

## 12.7 Custom MCP Server Geliştirme

### KIRO2 MCP Server Tasarımı

**Amaç:** KIRO2 özel operasyonları için MCP server

**Sağlanacak Tools:**

| Tool | Açıklama |
|------|----------|
| `search_questions` | Soru bankası araması |
| `get_curriculum` | Müfredat ağacı |
| `validate_question` | Soru doğrulama |
| `get_student_stats` | Öğrenci istatistikleri |
| `generate_report` | Rapor oluşturma |

### TypeScript Implementation

```typescript
// kiro2-mcp-server/src/index.ts

import { Server } from "@modelcontextprotocol/sdk/server";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio";
import { Pool } from "pg";

const pool = new Pool({
  connectionString: process.env.POSTGRES_URL
});

const server = new Server({
  name: "kiro2-mcp-server",
  version: "1.0.0"
});

// Tool: Search Questions
server.tool({
  name: "search_questions",
  description: "Search the KIRO2 question bank",
  inputSchema: {
    type: "object",
    properties: {
      topic: { type: "string", description: "Question topic (e.g., 'limit', 'türev')" },
      difficulty: { type: "integer", minimum: 1, maximum: 5 },
      exam_type: { type: "string", enum: ["TYT", "AYT"] },
      limit: { type: "integer", default: 10 }
    },
    required: ["topic"]
  },
  handler: async ({ topic, difficulty, exam_type, limit = 10 }) => {
    const query = `
      SELECT question_id, question_text, difficulty_level, topic_tags
      FROM questions
      WHERE topic_tags @> $1::jsonb
      ${difficulty ? 'AND difficulty_level = $2' : ''}
      ${exam_type ? 'AND exam_type = $3' : ''}
      LIMIT $4
    `;
    
    const params = [JSON.stringify([topic])];
    if (difficulty) params.push(difficulty);
    if (exam_type) params.push(exam_type);
    params.push(limit);
    
    const result = await pool.query(query, params);
    return result.rows;
  }
});

// Tool: Get Curriculum
server.tool({
  name: "get_curriculum",
  description: "Get YKS curriculum tree for a subject",
  inputSchema: {
    type: "object",
    properties: {
      subject: { type: "string", enum: ["matematik", "fizik", "kimya", "biyoloji", "turkce"] },
      exam_type: { type: "string", enum: ["TYT", "AYT"] }
    },
    required: ["subject", "exam_type"]
  },
  handler: async ({ subject, exam_type }) => {
    const query = `
      SELECT topic, subtopics, weight
      FROM curriculum
      WHERE subject = $1 AND exam_type = $2
      ORDER BY topic_order
    `;
    
    const result = await pool.query(query, [subject, exam_type]);
    return result.rows;
  }
});

// Tool: Validate Question
server.tool({
  name: "validate_question",
  description: "Validate a question against KIRO2 standards",
  inputSchema: {
    type: "object",
    properties: {
      question: {
        type: "object",
        properties: {
          question_text: { type: "string" },
          options: { type: "object" },
          correct_answer: { type: "string" },
          difficulty_level: { type: "integer" }
        },
        required: ["question_text", "options", "correct_answer"]
      }
    },
    required: ["question"]
  },
  handler: async ({ question }) => {
    const errors = [];
    
    // Schema validation
    if (!question.question_text || question.question_text.length < 10) {
      errors.push("Question text too short");
    }
    
    // Options validation
    const options = question.options || {};
    const requiredOptions = ['A', 'B', 'C', 'D', 'E'];
    for (const opt of requiredOptions) {
      if (!options[opt]) {
        errors.push(`Missing option ${opt}`);
      }
    }
    
    // Correct answer validation
    if (!requiredOptions.includes(question.correct_answer)) {
      errors.push(`Invalid correct_answer: ${question.correct_answer}`);
    }
    
    // Difficulty validation
    if (question.difficulty_level < 1 || question.difficulty_level > 5) {
      errors.push("Difficulty must be 1-5");
    }
    
    return {
      valid: errors.length === 0,
      errors,
      score: Math.max(0, 100 - errors.length * 20)
    };
  }
});

// Resource: Curriculum Document
server.resource({
  uri: "kiro2://curriculum/matematik/ayt",
  name: "AYT Matematik Müfredatı",
  mimeType: "application/json",
  handler: async () => {
    const result = await pool.query(
      "SELECT * FROM curriculum WHERE subject = 'matematik' AND exam_type = 'AYT'"
    );
    return JSON.stringify(result.rows, null, 2);
  }
});

// Start server
const transport = new StdioServerTransport();
server.connect(transport);

console.error("KIRO2 MCP Server started");
```

### Package.json

```json
{
  "name": "kiro2-mcp-server",
  "version": "1.0.0",
  "type": "module",
  "main": "dist/index.js",
  "scripts": {
    "build": "tsc",
    "start": "node dist/index.js"
  },
  "dependencies": {
    "@modelcontextprotocol/sdk": "^0.5.0",
    "pg": "^8.11.0"
  },
  "devDependencies": {
    "typescript": "^5.3.0",
    "@types/node": "^20.0.0",
    "@types/pg": "^8.10.0"
  }
}
```

---

## 12.8 MCP Debugging

### Logging

```json
{
  "mcpServers": {
    "my-server": {
      "command": "node",
      "args": ["server.js"],
      "env": {
        "DEBUG": "mcp:*",
        "LOG_LEVEL": "debug"
      }
    }
  }
}
```

### Health Check

```bash
# Server durumunu kontrol et
echo '{"jsonrpc":"2.0","method":"ping","id":1}' | npx @context7/mcp-server
```

### Common Issues

| Problem | Çözüm |
|---------|-------|
| Server başlamıyor | `command` path'i kontrol et |
| Connection timeout | Network/firewall kontrol et |
| Permission denied | Dosya izinleri kontrol et |
| Env var not found | `${VAR}` syntax doğru mu? |

---

## 12.9 Özet

### Checklist

- [ ] `.mcp.json` oluşturuldu
- [ ] Context7 kurulu ve çalışıyor
- [ ] Memory server yapılandırıldı
- [ ] Filesystem güvenli modda
- [ ] PostgreSQL read-only bağlantı
- [ ] Custom server planlandı

### Server Seçim Matrisi

| Server | KIRO2 İçin | Öncelik |
|--------|------------|---------|
| Context7 | Zorunlu | 🔴 Yüksek |
| Memory | Zorunlu | 🔴 Yüksek |
| Filesystem | Önerilen | 🟡 Orta |
| PostgreSQL | Özel | 🟡 Orta |
| Sequential Thinking | Opsiyonel | 🟢 Düşük |
| Brave Search | Opsiyonel | 🟢 Düşük |

### Metrikler

| Metrik | Hedef |
|--------|-------|
| Server uptime | > 99.9% |
| Response time | < 500ms |
| Error rate | < 1% |

---

**Önceki Bölüm:** [11 - Prompt Engineering](./11-prompt-engineering.md)  
**Sonraki Bölüm:** [13 - Claude Agent SDK](./13-claude-agent-sdk.md)
