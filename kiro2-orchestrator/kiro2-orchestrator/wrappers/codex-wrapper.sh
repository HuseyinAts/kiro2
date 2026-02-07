#!/bin/bash
# ============================================================================
# KIRO2 CODEX CLI WRAPPER
# ============================================================================
# Codex CLI'ı KIRO2 projesi için önceden yapılandırılmış şekilde çalıştırır
# ============================================================================

set -e

# Konfigürasyon
KIRO2_ROOT="/mnt/c/Users/husey/kiro2"
LOG_DIR="$HOME/.kiro2-orchestrator/logs"
CODEX_LOG="$LOG_DIR/codex.log"

# Log dizinini oluştur
mkdir -p "$LOG_DIR"

# Varsayılan parametreler
SANDBOX_MODE="${SANDBOX_MODE:-workspace-write}"
REASONING_EFFORT="${REASONING_EFFORT:-medium}"
AUTO_APPROVE="${AUTO_APPROVE:-true}"
MODEL="${MODEL:-gpt-5.1-codex-max}"

# Kullanım bilgisi
usage() {
    echo "KIRO2 Codex Wrapper"
    echo ""
    echo "Kullanım: $0 [OPTIONS] <prompt>"
    echo ""
    echo "Options:"
    echo "  -s, --sandbox MODE     Sandbox modu (workspace-write|workspace-read|off)"
    echo "  -r, --reasoning LEVEL  Reasoning effort (low|medium|high)"
    echo "  -a, --auto-approve     Otomatik onay (true|false)"
    echo "  -m, --model MODEL      Model seçimi"
    echo "  -h, --help             Bu mesajı göster"
    echo ""
    echo "Örnek:"
    echo "  $0 'FastAPI endpoint oluştur: GET /api/v1/topics'"
    echo "  $0 -r high 'Karmaşık query optimizasyonu yap'"
}

# Argüman parsing
while [[ $# -gt 0 ]]; do
    case $1 in
        -s|--sandbox)
            SANDBOX_MODE="$2"
            shift 2
            ;;
        -r|--reasoning)
            REASONING_EFFORT="$2"
            shift 2
            ;;
        -a|--auto-approve)
            AUTO_APPROVE="$2"
            shift 2
            ;;
        -m|--model)
            MODEL="$2"
            shift 2
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            PROMPT="$1"
            shift
            ;;
    esac
done

# Prompt kontrolü
if [ -z "$PROMPT" ]; then
    echo "Hata: Prompt gerekli"
    usage
    exit 1
fi

# KIRO2 context'i ekle
KIRO2_CONTEXT="
PROJE: KIRO2 EdTech Platform
KONUM: $KIRO2_ROOT
TECH STACK: FastAPI, React, PostgreSQL, Redis
HEDEF: YKS/TYT/AYT sınav hazırlık platformu

GÖREV:
$PROMPT
"

# Timestamp
TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")

# Log başlangıcı
echo "[$TIMESTAMP] CODEX EXECUTION STARTED" >> "$CODEX_LOG"
echo "  Prompt: $PROMPT" >> "$CODEX_LOG"
echo "  Model: $MODEL" >> "$CODEX_LOG"
echo "  Sandbox: $SANDBOX_MODE" >> "$CODEX_LOG"
echo "  Reasoning: $REASONING_EFFORT" >> "$CODEX_LOG"

# Codex CLI çalıştır
cd "$KIRO2_ROOT"

CODEX_CMD="codex exec"
CODEX_CMD="$CODEX_CMD --sandbox $SANDBOX_MODE"
CODEX_CMD="$CODEX_CMD --reasoning-effort $REASONING_EFFORT"

if [ "$AUTO_APPROVE" = "true" ]; then
    CODEX_CMD="$CODEX_CMD --auto-approve"
fi

# Çalıştır
echo "Codex çalıştırılıyor..."
$CODEX_CMD "$KIRO2_CONTEXT" 2>&1 | tee -a "$CODEX_LOG"

EXIT_CODE=${PIPESTATUS[0]}

# Log sonucu
TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")
echo "[$TIMESTAMP] CODEX EXECUTION COMPLETED (exit: $EXIT_CODE)" >> "$CODEX_LOG"
echo "---" >> "$CODEX_LOG"

exit $EXIT_CODE
