<div align="center">

<!-- Animated Banner -->
<img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&customColorList=6,11,20&height=200&section=header&text=OpenAgent&fontSize=80&fontAlignY=35&animation=twinkling&fontColor=fff" width="100%"/>



<!-- Badges with Animation Effect -->
<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white&labelColor=306998" alt="Python"/>
  <img src="https://img.shields.io/badge/AI-Powered-FF6F00?style=for-the-badge&logo=tensorflow&logoColor=white" alt="AI"/>
  <img src="https://img.shields.io/badge/Status-Active-00FF00?style=for-the-badge&logo=statuspage&logoColor=white" alt="Status"/>
  <img src="https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge&logo=opensourceinitiative&logoColor=white" alt="License"/>
</p>

<!-- Animated Divider -->
<img src="https://user-images.githubusercontent.com/74038190/212284100-561aa473-3905-4a80-b561-0d28506553ee.gif" width="900">

<!-- Developer Badge -->
<p align="center">
  <a href="https://koushikhy.netlify.app">
    <img src="https://img.shields.io/badge/👨‍💻_Developed_by-Koushik_HY-00D9FF?style=for-the-badge&labelColor=1a1a2e" alt="Developer"/>
  </a>
</p>

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

> **OpenAgent uses [Groq](https://groq.com) for high-quality AI responses. Groq is 100% FREE — no credit card required!**

**Step 3: Get Your Free Groq API Key**

1. Go to **[https://console.groq.com](https://console.groq.com)**
2. Sign up with Google or email (no payment info needed)
3. Navigate to **API Keys** → Click **Create API Key**
4. Copy the key (starts with `gsk_...`)

**Step 4: Paste Your API Key**

Open `config/settings.yaml` and paste your key:

```yaml
llm:
  provider: "groq"               # Uses Groq's free API
  api_key: "gsk_YOUR_API_KEY_HERE"  # ← Paste your key here
  base_url: "https://api.groq.com/openai/v1"
  cloud_model: "llama-3.3-70b-versatile"
  
  # Offline Fallback (uses local Ollama when no internet)
  host: "http://localhost:11434"
  model: "phi3:mini"
```

> ⚠️ **Never commit your API key to public repos!** Add `config/settings.yaml` to `.gitignore` for public projects.

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

<div align="center">

| 🔧 Tool | 🌍 Type | 📝 Description |
|:---|:---:|:---|
| **Web Search** | 🌐 Online | DuckDuckGo-powered intelligent search |
| **Web Fetch** | 🌐 Online | Extract and parse website content |
| **File Parser** | 🔒 Local | PDF, DOCX, TXT text extraction |
| **OCR Vision** | 🔒 Local | Tesseract-based image text recognition |
| **Summarizer** | 🔒 Local | Condense long documents intelligently |
| **Sandbox Exec** | 🔒 Local | Secure shell command execution |
| **RAG Memory** | 🔒 Local | ChromaDB-powered conversation memory |

</div>

---

## ⚙️ **Configuration**

Edit `config/settings.yaml` to customize your experience:

```yaml
llm:
  # Primary Provider (FREE)
  provider: "groq"                         # Groq = free, fast, high quality
  api_key: "gsk_YOUR_API_KEY_HERE"          # Get free at https://console.groq.com
  base_url: "https://api.groq.com/openai/v1"
  cloud_model: "llama-3.3-70b-versatile"   # 70B model — ChatGPT-level quality
  
  # Local Fallback (when offline)
  host: "http://localhost:11434"
  model: "phi3:mini"                       # 3.8B model — runs on CPU
  
  # Tuning
  timeout_seconds: 60
  max_tokens: 2048
  temperature: 0.7
```

> 💡 **How it works:** OpenAgent auto-detects your internet connection in 2 seconds. Online → uses Groq (fast, smart). Offline → uses Ollama (private, local).

---

## 🎨 **UI Preview**

<div align="center">

<!-- Screenshot Placeholder - Replace with your actual screenshot -->
<img src="https://github.com/user-attachments/assets/1c1c95e7-5c4e-47cb-b105-b3eed00f5d19" alt="OpenAgent UI" width="90%"/>

### ✨ **Features Showcase**

<table>
<tr>
<td align="center" width="33%">
<img src="https://user-images.githubusercontent.com/74038190/212257454-16e3712e-945a-4ca2-b238-408ad0bf87e6.gif" width="100"/>
<br><b>Particle Effects</b>
<br><sub>Dynamic Background</sub>
</td>
<td align="center" width="33%">
<img src="https://user-images.githubusercontent.com/74038190/212257472-08e52665-c503-4bd9-aa20-f5a4dae769b5.gif" width="100"/>
<br><b>Real-Time Chat</b>
<br><sub>Instant Responses</sub>
</td>
<td align="center" width="33%">
<img src="https://user-images.githubusercontent.com/74038190/212257468-1e9a91f1-b626-4baa-b15d-5c385dfa7ed2.gif" width="100"/>
<br><b>File Upload</b>
<br><sub>Drag & Drop</sub>
</td>
</tr>
</table>

</div>

---

## 🔄 **How Hybrid Mode Works**

<div align="center">

┌─────────────────────────────────────────────────────────┐
│                    USER QUERY                           │
└──────────────────┬──────────────────────────────────────┘
                   │
                   ▼
        ┌──────────────────────┐
        │  Connectivity Check  │
        │   (2 sec ping)       │
        └──────────┬───────────┘
                   │
         ┌─────────┴─────────┐
         │                   │
         ▼                   ▼
┌─────────────────┐  ┌─────────────────┐
│  ONLINE MODE    │  │  OFFLINE MODE   │
│  ☁️ Groq API    │  │  🔒 Ollama      │
│  • Llama 70B    │  │  • Phi-3 Mini   │
│  • Web Search   │  │  • Privacy      │
│  • ChatGPT-lvl  │  │  • Fast & Safe  │
│  • FREE ✅      │  │  • No Internet  │
└─────────────────┘  └─────────────────┘
```

</div>

---

## 📊 **Performance Stats**

<div align="center">

| Metric | Online Mode | Offline Mode | Hybrid Mode |
|:---|:---:|:---:|:---:|
| **Response Time** | ~2-3s | ~1-2s | ~1-3s |
| **Privacy Level** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Capability** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Uptime** | 95% | 100% | 100% |

</div>

---

## 🛣️ **Roadmap**

<div align="center">

```mermaid
gantt
    title Development Roadmap
    dateFormat  YYYY-MM-DD
    section Phase 1
    Core Agent           :done, 2024-01-01, 2024-02-01
    Web UI              :done, 2024-02-01, 2024-03-01
    section Phase 2
    Tool Integration    :done, 2024-03-01, 2024-04-01
    RAG Memory          :active, 2024-04-01, 30d
    section Phase 3
    Multi-Modal         :2024-05-01, 60d
    Voice Interface     :2024-06-15, 45d
    section Phase 4
    Mobile App          :2024-08-01, 90d
    Plugin System       :2024-09-01, 60d
```

</div>

---

## 🤝 **Contributing**

<div align="center">

We welcome contributions! Here's how you can help:

<table>
<tr>
<td align="center" width="25%">
<img src="https://user-images.githubusercontent.com/74038190/212284087-bbe7e430-757e-4901-90bf-4cd2ce3e1852.gif" width="100"/>
<br><b>Report Bugs</b>
<br><sub>Open an issue</sub>
</td>
<td align="center" width="25%">
<img src="https://user-images.githubusercontent.com/74038190/212284158-e840e285-664b-44d7-b79b-e264b5e54825.gif" width="100"/>
<br><b>Suggest Features</b>
<br><sub>Share your ideas</sub>
</td>
<td align="center" width="25%">
<img src="https://user-images.githubusercontent.com/74038190/212257465-7ce8d493-cac5-494e-982a-5a9deb852c4b.gif" width="100"/>
<br><b>Submit PRs</b>
<br><sub>Contribute code</sub>
</td>
<td align="center" width="25%">
<img src="https://user-images.githubusercontent.com/74038190/212257460-738ff738-247f-4445-a718-cdd0ca76e2db.gif" width="100"/>
<br><b>Improve Docs</b>
<br><sub>Help others</sub>
</td>
</tr>
</table>

</div>

---

## 👨‍💻 **About the Developer**

<div align="center">

<img src="https://user-images.githubusercontent.com/74038190/212749447-bfb7e725-6987-49d9-ae85-2015e3e7cc41.gif" width="400">

### **Koushik HY**

[![Portfolio](https://img.shields.io/badge/🌐_Portfolio-koushikhy.netlify.app-00D9FF?style=for-the-badge)](https://koushikhy.netlify.app)
[![Email](https://img.shields.io/badge/📧_Email-koushik4475@gmail.com-EA4335?style=for-the-badge&logo=gmail&logoColor=white)](mailto:koushik4475@gmail.com)
[![GitHub](https://img.shields.io/badge/💻_GitHub-koushik4475-181717?style=for-the-badge&logo=github)](https://github.com/koushik4475)

</div>

---

## 📜 **License**

<div align="center">

```ascii
╔═══════════════════════════════════════════════╗
║                                               ║
║   MIT License - Free to Use and Modify        ║
║   Copyright (c) 2024 Koushik HY              ║
║                                               ║
╚═══════════════════════════════════════════════╝
```

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

</div>

---

## ⭐ **Star History**

<div align="center">

[![Star History Chart](https://api.star-history.com/svg?repos=koushik4475/open-agent&type=Date)](https://star-history.com/#koushik4475/open-agent&Date)

</div>

---

## 💝 **Support the Project**

<div align="center">

If you find OpenAgent useful, please consider:

<table>
<tr>
<td align="center" width="33%">
⭐ <b>Star this repo</b>
<br><sub>Show your support</sub>
</td>
<td align="center" width="33%">
🔄 <b>Share with others</b>
<br><sub>Spread the word</sub>
</td>
<td align="center" width="33%">
🤝 <b>Contribute</b>
<br><sub>Help improve it</sub>
</td>
</tr>
</table>

<br>

**Made with ❤️ and ☕ by Koushik HY**

</div>

---

<!-- Animated Footer -->
<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&customColorList=6,11,20&height=100&section=footer" width="100%"/>

<img src="https://user-images.githubusercontent.com/74038190/212284115-f47cd8ff-2ffb-4b04-b5bf-4d1c14c0247f.gif" width="1000">

**🚀 Happy Coding! 🎉**

</div>
