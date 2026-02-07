# 🏗️ Gemini + Claude Entegre Mimari Diyagramları

## 1. Genel Sistem Mimarisi

```mermaid
graph TB
    subgraph "Kiro IDE (Frontend)"
        UI[Chat UI]
        Editor[Code Editor]
        Files[File Explorer]
        MCPPanel[MCP Servers Panel]
    end
    
    subgraph "Agent Layer"
        Claude[Claude Sonnet 4.5<br/>Orchestrator]
    end
    
    subgraph "MCP Protocol Layer"
        MCP[MCP Protocol<br/>JSON-RPC over stdio]
    end
    
    subgraph "MCP Servers"
        Gemini[Gemini Reasoning Engine<br/>4 Tools]
        Zemberek[Zemberek NLP<br/>4 Tools]
    end
    
    subgraph "AI Models"
        GeminiAPI[Google Gemini API<br/>Experimental 1206]
        ZemberekHTTP[Zemberek HTTP Service<br/>Port 8081]
    end
    
    UI --> Claude
    Editor --> Claude
    Files --> Claude
    MCPPanel -.Monitor.-> MCP
    
    Claude --> MCP
    MCP --> Gemini
    MCP --> Zemberek
    
    Gemini --> GeminiAPI
    Zemberek --> ZemberekHTTP
    
    style Claude fill:#f9f,stroke:#333,stroke-width:4px
    style Gemini fill:#9f9,stroke:#333,stroke-width:2px
    style GeminiAPI fill:#99f,stroke:#333,stroke-width:2px
```

## 2. Veri Akış Diyagramı (Kod İncelemesi)

```mermaid
sequenceDiagram
    participant User
    participant KiroUI as Kiro IDE UI
    participant Claude as Claude Sonnet 4.5
    participant MCP as MCP Protocol
    participant GeminiMCP as Gemini MCP Server
    participant GeminiAPI as Gemini API
    
    User->>KiroUI: "Bu kodu incele: [kod]"
    KiroUI->>Claude: User message
    
    Note over Claude: Analiz: Kod incelemesi gerekli<br/>Tool: gemini_code_review
    
    Claude->>MCP: Tool Call Request
    MCP->>GeminiMCP: gemini_code_review(code, language)
    
    Note over GeminiMCP: Prompt hazırla<br/>Thinking mode ekle
    
    GeminiMCP->>GeminiAPI: generate_content(prompt)
    
    Note over GeminiAPI: Kodu analiz et<br/>5-10 saniye
    
    GeminiAPI-->>GeminiMCP: Detaylı analiz
    GeminiMCP-->>MCP: MCP Response
    MCP-->>Claude: Tool Result
    
    Note over Claude: Yanıtı formatla<br/>Kullanıcıya sun
    
    Claude-->>KiroUI: Formatted Response
    KiroUI-->>User: Kod inceleme raporu
```

## 3. Karar Ağacı (Tool Selection)

```mermaid
graph TD
    Start[Kullanıcı Sorusu] --> Analyze{Claude Analiz}
    
    Analyze -->|Basit Soru| ClaudeOnly[Claude Kendi Yanıtlar]
    Analyze -->|Kod İncelemesi| GeminiCode[gemini_code_review]
    Analyze -->|Tasarım Analizi| GeminiDesign[gemini_design_analysis]
    Analyze -->|Gereksinim Analizi| GeminiReq[gemini_requirements_analysis]
    Analyze -->|Türkçe NLP| Zemberek[Zemberek Tools]
    Analyze -->|Karmaşık Analiz| GeminiReason[gemini_reasoning_engine]
    
    ClaudeOnly --> Response[Kullanıcıya Yanıt]
    GeminiCode --> GeminiAPI[Gemini API Call]
    GeminiDesign --> GeminiAPI
    GeminiReq --> GeminiAPI
    GeminiReason --> GeminiAPI
    Zemberek --> ZemberekAPI[Zemberek HTTP Call]
    
    GeminiAPI --> Response
    ZemberekAPI --> Response
    
    style Analyze fill:#f9f,stroke:#333,stroke-width:2px
    style GeminiAPI fill:#99f,stroke:#333,stroke-width:2px
    style Response fill:#9f9,stroke:#333,stroke-width:2px
```

## 4. Deployment Mimarisi

```mermaid
graph TB
    subgraph "User Machine"
        Kiro[Kiro IDE<br/>Electron App]
    end
    
    subgraph "Local MCP Servers"
        GeminiMCP[Gemini MCP<br/>Python Process]
        ZemberekMCP[Zemberek MCP<br/>Python Process]
    end
    
    subgraph "Local Services"
        ZemberekHTTP[Zemberek HTTP<br/>Java Service<br/>Port 8081]
    end
    
    subgraph "Cloud Services"
        ClaudeAPI[Anthropic Claude API<br/>api.anthropic.com]
        GeminiAPI[Google Gemini API<br/>generativelanguage.googleapis.com]
    end
    
    Kiro -->|stdio| GeminiMCP
    Kiro -->|stdio| ZemberekMCP
    Kiro -->|HTTPS| ClaudeAPI
    
    GeminiMCP -->|HTTPS| GeminiAPI
    ZemberekMCP -->|HTTP| ZemberekHTTP
    
    style Kiro fill:#f9f,stroke:#333,stroke-width:2px
    style ClaudeAPI fill:#ff9,stroke:#333,stroke-width:2px
    style GeminiAPI fill:#99f,stroke:#333,stroke-width:2px
```

## 5. Performans Optimizasyonu Mimarisi (Önerilen)

```mermaid
graph TB
    subgraph "Frontend"
        UI[Kiro IDE UI]
    end
    
    subgraph "Orchestration Layer"
        Claude[Claude Orchestrator]
        Cache[Response Cache<br/>Redis]
        Queue[Request Queue<br/>RabbitMQ]
    end
    
    subgraph "MCP Server Pool"
        MCP1[Gemini MCP 1]
        MCP2[Gemini MCP 2]
        MCP3[Gemini MCP 3]
        LB[Load Balancer]
    end
    
    subgraph "External APIs"
        GeminiAPI[Gemini API]
    end
    
    UI --> Claude
    Claude --> Cache
    Cache -->|Cache Miss| Queue
    Queue --> LB
    LB --> MCP1
    LB --> MCP2
    LB --> MCP3
    
    MCP1 --> GeminiAPI
    MCP2 --> GeminiAPI
    MCP3 --> GeminiAPI
    
    style Cache fill:#9f9,stroke:#333,stroke-width:2px
    style Queue fill:#ff9,stroke:#333,stroke-width:2px
    style LB fill:#f99,stroke:#333,stroke-width:2px
```

---

**Not:** Bu diyagramlar Mermaid formatındadır. Markdown viewer'da veya GitHub'da görüntülenebilir.
