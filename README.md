# OpenAgent | Open-Source AI Agent Application and Tool-Using Assistant

OpenAgent is an AI-agent application project with a web-based interface and a Python runtime. The repository documents its agent workflow, available tools, system architecture, and deployment-oriented quick start. It is a starting point for developers exploring AI assistants, tool-using agents, and interactive agent interfaces; review the configured model and tool permissions before connecting it to external systems.

---
title: Openagent
emoji: 🤖
colorFrom: purple
colorTo: blue
sdk: docker
pinned: false
---
<div align="center">

<!-- Animated Banner -->
<img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&customColorList=6,11,20&height=200&section=header&text=OpenAgent&fontSize=80&fontAlignY=35&animation=twinkling&fontColor=fff" width="100%"/>

<!-- Badges -->
<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white&labelColor=306998" alt="Python"/>
  <img src="https://img.shields.io/badge/AI-Powered-FF6F00?style=for-the-badge&logo=tensorflow&logoColor=white" alt="AI"/>
  <img src="https://img.shields.io/badge/Status-Active-00FF00?style=for-the-badge&logo=statuspage&logoColor=white" alt="Status"/>
  <img src="https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge&logo=opensourceinitiative&logoColor=white" alt="License"/>
</p>

<img src="https://user-images.githubusercontent.com/74038190/212284100-561aa473-3905-4a80-b561-0d28506553ee.gif" width="900">

<p align="center">
  <a href="https://koushikhy.netlify.app">
    <img src="https://img.shields.io/badge/👨‍💻_Developed_by-Koushik_HY-00D9FF?style=for-the-badge&labelColor=1a1a2e" alt="Developer"/>
  </a>
</p>

## 🌐 Live Demo

[![Live Demo](https://img.shields.io/badge/🤖_Live_Demo-Try_on_HuggingFace-FFD21E?style=for-the-badge&logo=huggingface&logoColor=black)](https://huggingface.co/spaces/koushik4475/openagent)

</div>

---

## 🌟 **What is OpenAgent?**

<div align="center">

```ascii
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║   🧠 HYBRID AI AGENT - Best of Both Worlds                   ║
║                                                               ║
║   ⚡ ONLINE  → Groq Llama 3.3 70B (ChatGPT-level, FREE)     ║
║   🔒 OFFLINE → Ollama Phi-3 (Privacy + Local Processing)     ║
║   🎯 AUTO    → Intelligent Switching Based on Connectivity   ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
```

</div>

> A **next-generation AI assistant** that combines the **privacy of local processing** with the **power of cloud intelligence**. Never compromise between speed and security again!

---

## ✨ **Key Highlights**

<table>
<tr>
<td width="50%">

### 🎨 **Stunning Cyberpunk UI**
- ⚡ **Particle Animations** - Dynamic background effects
- 📺 **CRT Scanlines** - Retro-futuristic aesthetic
- 🌈 **Glassmorphism** - Modern blur effects
- 🎭 **Real-Time Status** - Visual mode indicators
- 📤 **Drag & Drop** - Seamless file uploads

</td>
<td width="50%">

### 🛠️ **Powerful Toolset**
- 🌐 **Web Search & Fetch** - Real-time internet access
- 📄 **File Parser** - PDF, DOCX, TXT extraction
- 👁️ **OCR Vision** - Image text recognition
- 🧠 **RAG Memory** - Conversation history
- ⚙️ **Sandbox Exec** - Safe command execution

</td>
</tr>
</table>

---

## 🚀 **Quick Start**

<details open>
<summary><b>📋 Prerequisites</b></summary>
<br>

```bash
✅ Python 3.10 or higher
✅ Ollama (for local AI models)
✅ Tesseract OCR (for image processing)
```

</details>

<details open>
<summary><b>🔑 API Setup (FREE — No Credit Card Needed)</b></summary>
<br>

1. Go to **[https://console.groq.com](https://console.groq.com)**
2. Sign up with Google or email
3. Navigate to **API Keys** → Click **Create API Key**
4. Copy the key (starts with `gsk_...`)

```yaml
llm:
  provider: "groq"
  api_key: "gsk_YOUR_API_KEY_HERE"
  base_url: "https://api.groq.com/openai/v1"
  cloud_model: "llama-3.3-70b-versatile"
  host: "http://localhost:11434"
  model: "phi3:mini"
```

</details>

<details open>
<summary><b>🎯 Launch the Agent</b></summary>
<br>

```bash
python ui/server.py
```

**🌐 Open your browser:** [`http://localhost:5000`](http://localhost:5000)

</details>

---

## 🏗️ **System Architecture**

<div align="center">

```mermaid
graph TB
    A[🌐 Web UI - Flask] --> B{🤖 Agent Core}
    B --> C[☁️ Cloud LLM<br/>Groq Llama 3.3 70B]
    B --> D[🔒 Local LLM<br/>Ollama Phi-3]
    B --> E[🛠️ Tool Suite]
    E --> F[🔍 Web Search]
    E --> G[📄 File Parser]
    E --> H[👁️ OCR Vision]
    E --> I[🗄️ RAG Memory]
    I --> J[(💾 ChromaDB)]
    style A fill:#00d4ff,stroke:#0099cc,stroke-width:3px,color:#000
    style B fill:#7c3aed,stroke:#5b21b6,stroke-width:3px,color:#fff
    style C fill:#10b981,stroke:#059669,stroke-width:2px,color:#fff
    style D fill:#f59e0b,stroke:#d97706,stroke-width:2px,color:#fff
    style E fill:#ec4899,stroke:#db2777,stroke-width:2px,color:#fff
    style J fill:#6366f1,stroke:#4f46e5,stroke-width:2px,color:#fff
```

</div>

---

## 🎯 **Core Features**

| 🔧 Tool | 🌍 Type | 📝 Description |
|:---|:---:|:---|
| **Web Search** | 🌐 Online | DuckDuckGo-powered intelligent search |
| **Web Fetch** | 🌐 Online | Extract and parse website content |
| **File Parser** | 🔒 Local | PDF, DOCX, TXT text extraction |
| **OCR Vision** | 🔒 Local | Tesseract-based image text recognition |
| **Summarizer** | 🔒 Local | Condense long documents intelligently |
| **Sandbox Exec** | 🔒 Local | Secure shell command execution |
| **RAG Memory** | 🔒 Local | ChromaDB-powered conversation memory |

---

## 🎨 **UI Preview**

<div align="center">
<img src="https://github.com/user-attachments/assets/1c1c95e7-5c4e-47cb-b105-b3eed00f5d19" alt="OpenAgent UI" width="90%"/>
</div>

---

## 👨‍💻 **About the Developer**

<div align="center">

### **Koushik HY**

[![Portfolio](https://img.shields.io/badge/🌐_Portfolio-koushikhy.netlify.app-00D9FF?style=for-the-badge)](https://koushikhy.netlify.app)
[![Email](https://img.shields.io/badge/📧_Email-koushik4475@gmail.com-EA4335?style=for-the-badge&logo=gmail&logoColor=white)](mailto:koushik4475@gmail.com)
[![GitHub](https://img.shields.io/badge/💻_GitHub-koushik4475-181717?style=for-the-badge&logo=github)](https://github.com/koushik4475)

</div>

---

## 📜 **License**

MIT License — Copyright (c) 2024 Koushik HY

---

<div align="center">

**Made with ❤️ and ☕ by Koushik HY**

<img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&customColorList=6,11,20&height=100&section=footer" width="100%"/>

</div>
