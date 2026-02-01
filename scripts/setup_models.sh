#!/usr/bin/env bash
# ================================================================
# scripts/setup_models.sh
# One-command setup for the local LLM runtime.
# Run this ONCE before starting the agent.
# ================================================================

set -e

echo "=============================================="
echo "  OpenAgent — Model Setup Script"
echo "=============================================="
echo ""

# ─── 1. Check if Ollama is installed ──────────────────────────
if command -v ollama &> /dev/null; then
    echo "✅ Ollama is already installed."
    OLLAMA_VERSION=$(ollama version 2>/dev/null || echo "unknown")
    echo "   Version: $OLLAMA_VERSION"
else
    echo "📥 Ollama not found. Installing..."
    echo ""

    # Detect OS
    OS=$(uname -s)
    case "$OS" in
        Linux)
            echo "   Detected: Linux"
            curl -fsSL https://ollama.ai/install.sh | sh
            ;;
        Darwin)
            echo "   Detected: macOS"
            echo "   Please download Ollama from: https://ollama.ai/download/mac"
            echo "   Then run this script again."
            exit 1
            ;;
        *)
            echo "   Detected: $OS"
            echo "   Please install Ollama manually: https://ollama.ai"
            exit 1
            ;;
    esac

    echo ""
    echo "✅ Ollama installed successfully."
fi

echo ""

# ─── 2. Start Ollama service ──────────────────────────────────
echo "🔄 Starting Ollama service..."
ollama serve &
OLLAMA_PID=$!
sleep 2  # Give it a moment to start

# ─── 3. Pull the primary model ────────────────────────────────
PRIMARY_MODEL="phi3:mini"
echo ""
echo "📥 Pulling primary model: $PRIMARY_MODEL"
echo "   Size: ~2.5 GB | License: MIT"
echo "   This may take a few minutes on first run..."
echo ""

if ollama pull "$PRIMARY_MODEL"; then
    echo "✅ Model '$PRIMARY_MODEL' downloaded successfully."
else
    echo "⚠️  Failed to pull '$PRIMARY_MODEL'. Trying fallback model..."
    FALLBACK_MODEL="qwen2.5:0.5b"
    echo "   Pulling fallback: $FALLBACK_MODEL (Size: ~0.6 GB)"
    if ollama pull "$FALLBACK_MODEL"; then
        echo "✅ Fallback model '$FALLBACK_MODEL' downloaded."
        echo ""
        echo "⚠️  Update config/settings.yaml:"
        echo "    llm:"
        echo "      model: \"$FALLBACK_MODEL\""
    else
        echo "❌ Both models failed to download. Check your internet connection."
        exit 1
    fi
fi

echo ""

# ─── 4. Verify ────────────────────────────────────────────────
echo "🔍 Verifying setup..."
echo ""
echo "Available models:"
ollama list
echo ""
echo "=============================================="
echo "  ✅ Setup complete!"
echo ""
echo "  Start the agent with:"
echo "    python -m openagent"
echo "=============================================="

# Kill the background ollama serve (systemd will manage it on Linux)
kill $OLLAMA_PID 2>/dev/null || true
