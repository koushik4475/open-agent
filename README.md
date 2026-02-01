# OpenAgent — Hybrid AI Agent

> **Developed by [Koushik HY](https://koushikhy.netlify.app)**
>
> A powerful **Hybrid (Offline + Online) AI Agent**. Combines local privacy with cloud intelligence.
> - **Offline**: Uses Ollama (Phi-3) for local tasks + Tesseract OCR + Local RAG.
> - **Online**: Uses OpenRouter (DeepSeek) for complex reasoning + Web Search.

---

## 🌟 Key Features

### 1. Hybrid Intelligence
- **Speed**: Defaults to **DeepSeek (via OpenRouter)** for instant responses.
- **Privacy**: Falls back to **Local Ollama** if offline or for sensitive tasks.
- **Resilience**: Auto-switching ensures 100% uptime.

### 2. Stunning Web UI
- **Cyberpunk Interface**: Animated particles, CRT scanlines, and glassmorphism.
- **Real-Time Status**: Visual indicators for Online/Offline/Hybrid modes.
- **Visual Tools**: Interactive cards for file parsing, OCR, and search.
- **File Upload**: Drag-and-drop or click to upload files/images for analysis.

### 3. Comprehensive Toolset
| Tool | Type | Description |
|---|---|---|
| **Web Search** | 🌐 Online | DuckDuckGo search (Identity-aware) |
| **Web Fetch** | 🌐 Online | Read and parse any website URL |
| **File Parser** | 🔒 Local | Extract text from PDF, DOCX, TXT |
| **OCR Vision** | 🔒 Local | Extract text from images (Tesseract) |
| **Summarizer** | 🔒 Local | Condense long documents |
| **Sandbox Exec** | 🔒 Local | Run safe shell commands |
| **RAG Memory** | 🔒 Local | Remembers past conversations (ChromaDB) |

---

## 🚀 Quick Start

### Prerequisites
- **Python 3.10+**
- **Ollama** (for local fallback)
- **Tesseract OCR** (for image analysis)

### Installation

1. **Clone the repo**
   ```bash
   git clone https://github.com/koushik4475/open-agent.git
   cd open-agent
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Setup Environment**
   Run the setup script to download models:
   ```powershell
   .\scripts\setup_windows.ps1
   ```

### Running the Agent

**Start the Full UI Server:**
```powershell
python ui/server.py
```
👉 Open **http://localhost:5000** in your browser.

---

## 🛠️ Configuration

Edit `config/settings.yaml` to customize your experience:

```yaml
llm:
  provider: "openrouter"  # or "ollama"
  api_key: "your-key-here"
  cloud_model: "deepseek/deepseek-r1"
  
  # Local Fallback
  host: "http://localhost:11434"
  model: "phi3:mini"
```

---

## 🏗️ Architecture

```
┌─────────────────┐      ┌──────────────────┐
│  Web UI (Flask) │◄────►│   Agent Core     │
└─────────────────┘      └────────┬─────────┘
                                  │
          ┌───────────────────────┼────────────────────────┐
          ▼                       ▼                        ▼
  ┌───────────────┐       ┌───────────────┐        ┌───────────────┐
  │ Cloud LLM     │       │ Local LLM     │        │ Tools         │
  │ (DeepSeek)    │       │ (Ollama)      │        │ (Search/OCR)  │
  └───────────────┘       └───────────────┘        └───────────────┘
                                  ▲
                                  │
                          ┌───────────────┐
                          │ Memory (RAG)  │
                          └───────────────┘
```

---
# output:<img width="1785" height="928" alt="image" src="https://github.com/user-attachments/assets/1c1c95e7-5c4e-47cb-b105-b3eed00f5d19" />

## 👨‍💻 Developer

**Koushik HY**
- Portfolio: [koushikhy.netlify.app](https://koushikhy.netlify.app)
- Email: koushik4475@gmail.com

---

## 📄 License
MIT License. Free to use and modify.
