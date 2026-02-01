# OpenAgent — Complete Run Guide (Windows)

This guide will help you set up and run the OpenAgent project on Windows, including both the CLI agent and the stunning web UI.

---

## 📋 Prerequisites

- **Windows 10/11**
- **Python 3.10+** (you have Python 3.13.5 ✅)
- **Internet connection** (for initial setup only)
- **~4 GB free disk space** (for Ollama model)

---

## 🚀 Quick Start (3 Steps)

### Step 1: Install Ollama and Tesseract

#### Install Ollama
1. Download Ollama for Windows: https://ollama.ai/download/windows
2. Run the installer
3. Ollama will auto-start as a Windows service

#### Install Tesseract OCR
1. Download from: https://github.com/UB-Mannheim/tesseract/wiki
2. Run the installer (recommended path: `C:\Program Files\Tesseract-OCR`)
3. **Important**: During installation, check "Add to PATH" or manually add it:
   - Open System Properties → Environment Variables
   - Add `C:\Program Files\Tesseract-OCR` to your PATH

### Step 2: Run the Setup Script

Open PowerShell in the project directory and run:

```powershell
cd c:\Users\koush\Music\openagent
.\scripts\setup_windows.ps1
```

This script will:
- Verify Ollama installation
- Pull the `phi3:mini` model (~2.5 GB download)
- Check Tesseract installation
- List available models

**Note**: The model download may take 5-15 minutes depending on your internet speed.

### Step 3: Install Python Dependencies

```powershell
pip install -r requirements.txt
```

This installs all required Python packages including:
- ChromaDB (vector database)
- sentence-transformers (embeddings)
- PyMuPDF (PDF parsing)
- pytesseract (OCR wrapper)
- Flask (UI server)
- and more...

---

## 🎮 Running the Project

You have **two ways** to run OpenAgent:

### Option 1: CLI Agent (Terminal-Based)

Run the command-line interface:

```powershell
python -m openagent
```

**Available Commands:**
- `/help` — Show help
- `/tools` — List all tools
- `/status` — System status
- `/file <path>` — Parse a file
- `/clear` — Clear history
- `/quit` — Exit

**Example Usage:**
```
🧑 You> summarize this text: OpenAgent is an offline-first AI agent...
🤖 Agent> [AI response here]

🧑 You> /file C:\path\to\document.pdf
🤖 Agent> [Parsed content]

🧑 You> search for Python tutorials
🤖 Agent> [DuckDuckGo search results]
```

### Option 2: Web UI (Stunning Animated Interface)

#### Start the UI Server:

```powershell
cd c:\Users\koush\Music\openagent\ui
python server.py
```

You'll see:
```
============================================================
  🤖 OpenAgent UI Server
============================================================

  Starting server on http://localhost:5000
  Open your browser and navigate to the URL above

  Press Ctrl+C to stop the server
============================================================
```

#### Open in Browser:

Navigate to: **http://localhost:5000**

**UI Features:**
- 🌌 **Live particle field** with 120 particles + dynamic connecting lines
- 🔲 **CRT scanline overlay** for sci-fi terminal feel
- ✨ **Corner bracket decorations** with glow on all 4 corners
- 💫 **Logo pulse glow** animation
- ⏳ **Typing indicator** with staggered bounce dots
- 🃏 **Tool cards** that stagger-pop in with physics-based easing
- 💬 **Messages** slide in with spring animation
- 🎯 **Input bar glow** pulses cyan on focus

**3 Interactive Panels:**
1. **Chat** — Full conversational interface
2. **Tools** — Interactive cards for all 7 tools
3. **System** — Live ring-charts showing LLM load, network, memory usage

---

## 🛠️ Available Tools

| Tool | Icon | Description | Type |
|------|------|-------------|------|
| **File Parser** | 📄 | Extract text from TXT, PDF, DOCX | Offline |
| **OCR Vision** | 🖼️ | Tesseract OCR on images | Offline |
| **Summarizer** | 📝 | AI-powered text summarization | Offline |
| **Sandbox Exec** | ⚡ | Run whitelisted shell commands | Offline |
| **Web Search** | 🌐 | DuckDuckGo search (no API key) | Online |
| **Web Fetch** | 🔗 | Download and parse webpages | Online |
| **RAG Memory** | 🧠 | ChromaDB vector memory | Offline |

---

## 🧪 Testing the Installation

### 1. Verify Ollama

```powershell
ollama --version
ollama list  # Should show phi3:mini
```

### 2. Verify Tesseract

```powershell
tesseract --version
```

### 3. Test CLI Agent

```powershell
python -m openagent
```

Try these commands:
- `/status` — Check system status
- `/tools` — List available tools
- `summarize this: Hello world` — Test LLM

### 4. Test Web UI

1. Start server: `python ui/server.py`
2. Open browser: http://localhost:5000
3. Check animations are running
4. Send a test message: "Hello!"
5. Click on Tools panel
6. Check System Status panel

### 5. Run Automated Tests

```powershell
pytest tests/ -v
```

This runs all unit tests for parsers, tools, memory, and network functionality.

---

## 🐛 Troubleshooting

### Issue: "Ollama not found"
**Solution**: 
- Download and install from https://ollama.ai/download/windows
- Restart PowerShell after installation

### Issue: "Tesseract not found"
**Solution**:
- Install from https://github.com/UB-Mannheim/tesseract/wiki
- Add to PATH: `C:\Program Files\Tesseract-OCR`
- Restart PowerShell

### Issue: "Model pull failed"
**Solution**:
- Check internet connection
- Try fallback model: `ollama pull qwen2.5:0.5b`
- Update `config/settings.yaml` to use the fallback model

### Issue: "UI not loading"
**Solution**:
- Ensure Flask server is running: `python ui/server.py`
- Check http://localhost:5000 (not https)
- Check browser console for errors (F12)

### Issue: "Import errors"
**Solution**:
- Reinstall dependencies: `pip install -r requirements.txt --force-reinstall`
- Use a virtual environment:
  ```powershell
  python -m venv venv
  .\venv\Scripts\Activate.ps1
  pip install -r requirements.txt
  ```

### Issue: "Agent responses are slow"
**Explanation**: 
- This is normal on CPU-only systems with local models.
- **Solution**: Switch to a Cloud Provider (OpenRouter/DeepSeek) for instant responses.
  1. Open `config/settings.yaml`
  2. Change `provider: "openrouter"` or `"deepseek"`
  3. Add your API key
  4. Restart the server

### Issue: "Cloud API / 500 Error / 402 Payment Required"
**Solution**:
- The agent automatically falls back to local Ollama if the cloud fails.
- Check `logs/openagent.log` for details.
- Ensure you have credits in your API account.

---

## 📁 Project Structure

```
openagent/
├── __main__.py              # Entry point
├── config/
│   ├── cli.py               # CLI REPL
│   └── settings.yaml        # Configuration
├── core/
│   ├── agent.py             # Main agent orchestrator
│   ├── llm.py               # Ollama HTTP client
│   ├── router.py            # Tool routing logic
│   └── network.py           # Internet connectivity check
├── tools/
│   ├── offline/             # Offline tools
│   └── online/              # Online tools
├── parsers/                 # File parsers (PDF, DOCX, TXT, IMG)
├── memory/                  # ChromaDB wrapper
├── tests/                   # Unit tests
├── scripts/
│   ├── setup_models.sh      # Linux/Mac setup
│   └── setup_windows.ps1    # Windows setup (NEW)
├── ui/                      # Web UI (NEW)
│   ├── index.html           # Standalone HTML UI
│   └── server.py            # Flask API server
├── requirements.txt         # Python dependencies
└── README.md                # Project documentation
```

---

## 🎨 UI Screenshots

The UI features:
- **Dark sci-fi theme** with cyan/magenta accents
- **Glassmorphism** effects
- **Smooth animations** (60fps particle system)
- **Responsive design**
- **Real-time online/offline detection**

---

## 💡 Tips

1. **Offline Mode**: Most tools work without internet. Only Web Search and Web Fetch require connectivity.

2. **Memory**: The agent remembers conversation context using ChromaDB. Data is stored in `./data/chroma_db`.

3. **File Parsing**: Drag and drop files in the UI or use `/file <path>` in CLI.

4. **Sandbox Security**: Command execution is whitelisted. Only safe commands like `echo`, `date`, `ls` are allowed.

5. **Model Switching**: Edit `config/settings.yaml` to change the LLM model.

---

## 📚 Next Steps

- Explore all 7 tools in the Tools panel
- Try parsing different file types (PDF, DOCX, images)
- Test the RAG memory with multiple conversations
- Customize the UI colors in `ui/index.html`
- Add your own tools in `tools/offline/` or `tools/online/`

---

## 🆘 Support

- **GitHub Issues**: Report bugs or request features
- **Documentation**: See `README.md` for architecture details
- **Tests**: Run `pytest tests/ -v` to verify functionality

---

**Enjoy your offline-first AI agent! 🤖✨**
