import { useState, useEffect, useRef, useCallback } from "react";

/* ─── CSS INJECTION ─────────────────────────────────────────────────── */
const CSS = `
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Share+Tech+Mono&family=Rajdhani:wght@300;400;500;600;700&display=swap');

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

:root {
  --bg-deep: #020a0f;
  --bg-card: #0a1520;
  --bg-card-hover: #0f1e2e;
  --accent-cyan: #00e5ff;
  --accent-cyan-dim: rgba(0,229,255,0.15);
  --accent-magenta: #e040fb;
  --accent-green: #39ff14;
  --accent-green-dim: rgba(57,255,20,0.12);
  --text-primary: #e0f7fa;
  --text-secondary: #607d8b;
  --border-glow: rgba(0,229,255,0.25);
}

body {
  font-family: 'Rajdhani', sans-serif;
  background: var(--bg-deep);
  color: var(--text-primary);
  min-height: 100vh;
  overflow-x: hidden;
}

/* ─── PARTICLE CANVAS BG ─── */
#particle-canvas {
  position: fixed; inset: 0; z-index: 0; pointer-events: none;
}

/* ─── LAYOUT ─── */
.app-shell {
  position: relative; z-index: 1;
  display: grid;
  grid-template-columns: 240px 1fr;
  grid-template-rows: 64px 1fr;
  height: 100vh;
  max-width: 1440px;
  margin: 0 auto;
}

/* ─── TOP NAR ─── */
.topbar {
  grid-column: 1 / -1;
  display: flex; align-items: center; justify-content: space-between;
  padding: 0 28px;
  background: rgba(2,10,15,0.85);
  border-bottom: 1px solid var(--border-glow);
  backdrop-filter: blur(12px);
}
.topbar-logo {
  display: flex; align-items: center; gap: 10px;
}
.topbar-logo .logo-icon {
  width: 34px; height: 34px;
  border: 2px solid var(--accent-cyan);
  border-radius: 8px;
  display: flex; align-items: center; justify-content: center;
  animation: logo-pulse 2s ease-in-out infinite;
}
@keyframes logo-pulse {
  0%,100% { box-shadow: 0 0 6px var(--accent-cyan-dim); }
  50% { box-shadow: 0 0 18px rgba(0,229,255,0.4); }
}
.topbar-logo h1 {
  font-family: 'Orbitron', sans-serif;
  font-size: 18px; font-weight: 700;
  letter-spacing: 3px; text-transform: uppercase;
  background: linear-gradient(90deg, var(--accent-cyan), var(--accent-magenta));
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}
.topbar-status {
  display: flex; align-items: center; gap: 22px;
}
.status-pill {
  display: flex; align-items: center; gap: 7px;
  font-family: 'Share Tech Mono', monospace;
  font-size: 12px; color: var(--text-secondary);
}
.status-dot {
  width: 8px; height: 8px; border-radius: 50%;
  background: var(--accent-green);
  box-shadow: 0 0 8px var(--accent-green);
  animation: blink-dot 1.8s ease-in-out infinite;
}
.status-dot.offline { background: #f44336; box-shadow: 0 0 8px #f44336; }
@keyframes blink-dot {
  0%,100% { opacity:1; } 50% { opacity:0.35; }
}

/* ─── SIDEBAR ─── */
.sidebar {
  background: rgba(10,21,32,0.92);
  border-right: 1px solid var(--border-glow);
  padding: 20px 14px;
  display: flex; flex-direction: column; gap: 6px;
  overflow-y: auto;
}
.sidebar-section-label {
  font-family: 'Share Tech Mono', monospace;
  font-size: 10px; color: var(--text-secondary);
  text-transform: uppercase; letter-spacing: 2px;
  margin: 14px 0 6px 10px;
}
.sidebar-btn {
  display: flex; align-items: center; gap: 11px;
  padding: 10px 14px; border-radius: 8px;
  border: 1px solid transparent;
  background: transparent;
  color: var(--text-secondary);
  font-family: 'Rajdhani', sans-serif; font-size: 15px; font-weight: 500;
  cursor: pointer; transition: all 0.25s;
  position: relative; overflow: hidden;
}
.sidebar-btn:hover {
  background: var(--bg-card); color: var(--text-primary);
  border-color: var(--border-glow);
}
.sidebar-btn.active {
  background: var(--accent-cyan-dim);
  color: var(--accent-cyan);
  border-color: var(--accent-cyan);
}
.sidebar-btn .btn-icon { font-size: 18px; width: 22px; text-align:center; }
.sidebar-btn .active-bar {
  position: absolute; left: 0; top: 0; bottom: 0; width: 3px;
  background: var(--accent-cyan);
  box-shadow: 0 0 10px var(--accent-cyan);
  border-radius: 0 4px 4px 0;
  opacity: 0; transition: opacity 0.3s;
}
.sidebar-btn.active .active-bar { opacity: 1; }

/* ─── MAIN CONTENT ─── */
.main-content {
  display: flex; flex-direction: column;
  overflow: hidden;
}

/* ─── CHAT AREA ─── */
.chat-area {
  flex: 1; overflow-y: auto; padding: 24px 28px;
  display: flex; flex-direction: column; gap: 18px;
}
.chat-area::-webkit-scrollbar { width: 6px; }
.chat-area::-webkit-scrollbar-track { background: transparent; }
.chat-area::-webkit-scrollbar-thumb { background: var(--border-glow); border-radius: 3px; }

.msg {
  display: flex; gap: 12px; animation: msg-in 0.4s cubic-bezier(.22,1,.36,1);
}
@keyframes msg-in {
  from { opacity:0; transform: translateY(12px); }
  to { opacity:1; transform: translateY(0); }
}
.msg-avatar {
  width: 36px; height: 36px; border-radius: 10px;
  display: flex; align-items: center; justify-content: center;
  font-size: 16px; flex-shrink: 0;
  border: 1px solid var(--border-glow);
}
.msg-avatar.user { background: linear-gradient(135deg,#1a3a4a,#0f2535); }
.msg-avatar.agent { background: linear-gradient(135deg,#0a1e2d,#061520); border-color: var(--accent-cyan); }
.msg-bubble {
  background: var(--bg-card);
  border: 1px solid var(--border-glow);
  border-radius: 12px 12px 12px 4px;
  padding: 12px 16px;
  max-width: 75%;
  position: relative;
}
.msg.user .msg-bubble { border-radius: 12px 12px 4px 12px; border-color: rgba(224,64,251,0.2); }
.msg-bubble::before {
  content:''; position: absolute; inset: 0; border-radius: inherit;
  background: linear-gradient(135deg, rgba(0,229,255,0.03), transparent);
  pointer-events: none;
}
.msg-meta {
  font-family: 'Share Tech Mono', monospace;
  font-size: 10px; color: var(--text-secondary);
  margin-bottom: 4px;
}
.msg-text { font-size: 15px; line-height: 1.6; color: var(--text-primary); white-space: pre-wrap; }
.msg.user { flex-direction: row-reverse; }
.msg.user .msg-bubble { border-color: rgba(224,64,251,0.25); }

/* typing dots */
.typing-dots { display: flex; gap: 5px; padding: 6px 2px; }
.typing-dots span {
  width: 7px; height: 7px; border-radius: 50%;
  background: var(--accent-cyan);
  animation: typing-bounce 1.1s ease-in-out infinite;
}
.typing-dots span:nth-child(2) { animation-delay: 0.18s; }
.typing-dots span:nth-child(3) { animation-delay: 0.36s; }
@keyframes typing-bounce {
  0%,60%,100% { transform: translateY(0); opacity:.4; }
  30% { transform: translateY(-5px); opacity:1; }
}

/* ─── INPUT BAR ─── */
.input-bar {
  padding: 16px 28px 20px;
  background: rgba(2,10,15,0.7);
  border-top: 1px solid var(--border-glow);
  backdrop-filter: blur(8px);
}
.input-row {
  display: flex; gap: 10px; align-items: flex-end;
  background: var(--bg-card);
  border: 1px solid var(--border-glow);
  border-radius: 14px; padding: 10px 14px;
  transition: border-color 0.3s;
}
.input-row:focus-within { border-color: var(--accent-cyan); box-shadow: 0 0 16px var(--accent-cyan-dim); }
.input-row textarea {
  flex: 1; background: transparent; border: none; outline: none; resize: none;
  color: var(--text-primary); font-family: 'Rajdhani', sans-serif; font-size: 16px;
  line-height: 1.5; max-height: 120px; min-height: 30px;
}
.input-row textarea::placeholder { color: var(--text-secondary); }
.input-actions { display: flex; gap: 8px; }
.action-btn {
  width: 40px; height: 40px; border-radius: 10px;
  border: 1px solid var(--border-glow); background: transparent;
  color: var(--text-secondary); font-size: 18px;
  cursor: pointer; transition: all 0.2s;
  display: flex; align-items: center; justify-content: center;
}
.action-btn:hover { background: var(--accent-cyan-dim); color: var(--accent-cyan); border-color: var(--accent-cyan); }
.send-btn {
  width: 44px; height: 44px; border-radius: 10px;
  border: none;
  background: linear-gradient(135deg, var(--accent-cyan), #0288d1);
  color: #020a0f; font-size: 20px; cursor: pointer;
  transition: transform 0.15s, box-shadow 0.2s;
  display: flex; align-items: center; justify-content: center;
  box-shadow: 0 0 12px rgba(0,229,255,0.35);
}
.send-btn:hover { transform: scale(1.06); box-shadow: 0 0 22px rgba(0,229,255,0.5); }
.send-btn:active { transform: scale(0.95); }
.input-hints {
  margin-top: 8px; display: flex; gap: 10px; flex-wrap: wrap;
}
.hint-tag {
  font-family: 'Share Tech Mono', monospace; font-size: 11px;
  color: var(--text-secondary); background: var(--bg-card);
  border: 1px solid var(--border-glow);
  padding: 4px 10px; border-radius: 20px; cursor: pointer;
  transition: all 0.2s;
}
.hint-tag:hover { border-color: var(--accent-cyan); color: var(--accent-cyan); background: var(--accent-cyan-dim); }

/* ─── TOOLS PANEL ─── */
.tools-panel {
  flex: 1; overflow-y: auto; padding: 24px 28px;
  display: flex; flex-direction: column; gap: 16px;
}
.panel-header {
  font-family: 'Orbitron', sans-serif;
  font-size: 14px; font-weight: 700; letter-spacing: 2px;
  color: var(--accent-cyan);
  text-transform: uppercase;
  display: flex; align-items: center; gap: 10px;
  padding-bottom: 10px;
  border-bottom: 1px solid var(--border-glow);
}
.tools-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 14px;
}
.tool-card {
  background: var(--bg-card);
  border: 1px solid var(--border-glow);
  border-radius: 14px; padding: 22px 18px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(.22,1,.36,1);
  position: relative; overflow: hidden;
  animation: card-pop 0.5s cubic-bezier(.22,1,.36,1) both;
}
.tool-card:nth-child(1){animation-delay:.05s}
.tool-card:nth-child(2){animation-delay:.1s}
.tool-card:nth-child(3){animation-delay:.15s}
.tool-card:nth-child(4){animation-delay:.2s}
.tool-card:nth-child(5){animation-delay:.25s}
.tool-card:nth-child(6){animation-delay:.3s}
.tool-card:nth-child(7){animation-delay:.35s}
@keyframes card-pop {
  from { opacity:0; transform: translateY(20px) scale(0.95); }
  to { opacity:1; transform: translateY(0) scale(1); }
}
.tool-card::before {
  content:''; position:absolute; inset:0; border-radius: inherit;
  opacity:0; transition: opacity 0.4s;
  background: linear-gradient(135deg, rgba(0,229,255,0.06), rgba(224,64,251,0.04));
}
.tool-card:hover { border-color: var(--accent-cyan); transform: translateY(-3px); box-shadow: 0 8px 30px rgba(0,229,255,0.12); }
.tool-card:hover::before { opacity:1; }
.tool-card-icon {
  width: 46px; height: 46px; border-radius: 12px;
  display: flex; align-items: center; justify-content: center;
  font-size: 22px; margin-bottom: 14px;
  position: relative; z-index: 1;
}
.tool-card-title {
  font-family: 'Orbitron', sans-serif; font-size: 13px; font-weight: 700;
  color: var(--text-primary); margin-bottom: 6px;
  position: relative; z-index: 1;
}
.tool-card-desc {
  font-size: 13px; color: var(--text-secondary); line-height: 1.5;
  position: relative; z-index: 1;
}
.tool-badge {
  display: inline-block; font-family:'Share Tech Mono',monospace;
  font-size: 9px; padding: 2px 7px; border-radius: 10px;
  margin-top: 10px; position: relative; z-index:1;
  text-transform: uppercase; letter-spacing: 1px;
}
.badge-offline { background: var(--accent-green-dim); color: var(--accent-green); border: 1px solid rgba(57,255,20,0.3); }
.badge-online { background: rgba(0,229,255,0.1); color: var(--accent-cyan); border: 1px solid rgba(0,229,255,0.3); }

/* ─── STATUS PANEL ─── */
.status-panel {
  flex:1; overflow-y:auto; padding: 24px 28px;
  display: flex; flex-direction: column; gap: 18px;
}
.status-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
.status-card {
  background: var(--bg-card); border: 1px solid var(--border-glow);
  border-radius: 14px; padding: 20px;
  animation: card-pop 0.5s cubic-bezier(.22,1,.36,1) both;
}
.status-card:nth-child(1){animation-delay:.06s}
.status-card:nth-child(2){animation-delay:.12s}
.status-card:nth-child(3){animation-delay:.18s}
.status-card:nth-child(4){animation-delay:.24s}
.status-card-label {
  font-family:'Share Tech Mono',monospace; font-size:11px;
  color: var(--text-secondary); text-transform:uppercase; letter-spacing:1.5px;
  margin-bottom: 10px;
}
.status-card-value {
  font-family:'Orbitron',sans-serif; font-size: 22px; font-weight:700;
  color: var(--accent-cyan);
}
.status-card-sub { font-size:13px; color:var(--text-secondary); margin-top:4px; }

/* ring chart */
.ring-wrap { display:flex; align-items:center; gap: 18px; margin-top: 10px; }
.ring-svg { width:56px; height:56px; }
.ring-bg { fill: none; stroke: var(--bg-deep); stroke-width:7; }
.ring-fill { fill:none; stroke: var(--accent-cyan); stroke-width:7; stroke-linecap:round; transition: stroke-dashoffset 1s cubic-bezier(.22,1,.36,1); }
.ring-label { font-family:'Share Tech Mono',monospace; font-size:11px; color:var(--text-secondary); line-height:1.8; }

/* ─── SCROLLBAR ─── */
.tools-panel::-webkit-scrollbar,
.status-panel::-webkit-scrollbar { width:5px; }
.tools-panel::-webkit-scrollbar-thumb,
.status-panel::-webkit-scrollbar-thumb { background: var(--border-glow); border-radius:3px; }

/* ─── GLOW LINE SEPARATOR ─── */
.glow-line {
  height: 1px; width: 100%; margin: 4px 0;
  background: linear-gradient(90deg, transparent, var(--accent-cyan), transparent);
  opacity: 0.3;
}

/* ─── FILE UPLOAD OVERLAY ─── */
.upload-overlay {
  position:fixed; inset:0; z-index:100;
  background: rgba(2,10,15,0.88);
  display:flex; align-items:center; justify-content:center;
  backdrop-filter: blur(6px);
  animation: fade-in 0.25s ease;
}
@keyframes fade-in { from { opacity:0; } to { opacity:1; } }
.upload-box {
  background: var(--bg-card);
  border: 2px dashed var(--accent-cyan);
  border-radius: 22px;
  padding: 48px 40px; text-align:center;
  max-width: 420px; width: 90%;
  animation: pop-in 0.35s cubic-bezier(.22,1,.36,1);
}
@keyframes pop-in { from { transform:scale(0.85); opacity:0; } to { transform:scale(1); opacity:1; } }
.upload-icon { font-size: 48px; margin-bottom: 16px; }
.upload-title { font-family:'Orbitron',sans-serif; font-size:16px; font-weight:700; color:var(--accent-cyan); margin-bottom:8px; }
.upload-sub { font-size:14px; color:var(--text-secondary); margin-bottom: 20px; }
.upload-btn {
  display:inline-block; padding: 10px 28px; border-radius:10px;
  background: linear-gradient(135deg, var(--accent-cyan), #0288d1);
  color: #020a0f; font-family:'Orbitron',sans-serif; font-size:12px; font-weight:700;
  border:none; cursor:pointer; letter-spacing:1px;
  transition: transform 0.15s, box-shadow 0.2s;
  box-shadow: 0 0 14px rgba(0,229,255,0.35);
}
.upload-btn:hover { transform:scale(1.05); box-shadow: 0 0 24px rgba(0,229,255,0.5); }
.upload-close {
  position:absolute; top:24px; right:28px;
  background:none; border:none; color:var(--text-secondary);
  font-size:24px; cursor:pointer; transition:color .2s;
}
.upload-close:hover { color: var(--accent-cyan); }
.upload-supported { font-family:'Share Tech Mono',monospace; font-size:10px; color:var(--text-secondary); margin-top:12px; }

/* ─── SCANLINE OVERLAY ─── */
.scanlines {
  position:fixed; inset:0; z-index:999; pointer-events:none;
  background: repeating-linear-gradient(
    0deg,
    transparent,
    transparent 2px,
    rgba(0,229,255,0.015) 2px,
    rgba(0,229,255,0.015) 4px
  );
}

/* ─── CORNER DECORATIONS ─── */
.corner {
  position:fixed; width:40px; height:40px; z-index:50; pointer-events:none;
}
.corner::before, .corner::after {
  content:''; position:absolute; background: var(--accent-cyan);
  opacity:0.5;
}
.corner.tl { top:0; left:0; }
.corner.tl::before { top:0; left:0; width:100%; height:2px; }
.corner.tl::after { top:0; left:0; width:2px; height:100%; }
.corner.tr { top:0; right:0; }
.corner.tr::before { top:0; right:0; width:100%; height:2px; }
.corner.tr::after { top:0; right:0; width:2px; height:100%; }
.corner.bl { bottom:0; left:0; }
.corner.bl::before { bottom:0; left:0; width:100%; height:2px; }
.corner.bl::after { bottom:0; left:0; width:2px; height:100%; }
.corner.br { bottom:0; right:0; }
.corner.br::before { bottom:0; right:0; width:100%; height:2px; }
.corner.br::after { bottom:0; right:0; width:2px; height:100%; }
`;

/* ─── PARTICLE SYSTEM ─────────────────────────────────────── */
function ParticleCanvas() {
  const canvasRef = useRef(null);
  useEffect(() => {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");
    let w, h, particles, animId;
    const resize = () => {
      w = canvas.width = window.innerWidth;
      h = canvas.height = window.innerHeight;
    };
    resize();
    window.addEventListener("resize", resize);

    class P {
      constructor() { this.reset(); }
      reset() {
        this.x = Math.random() * w;
        this.y = Math.random() * h;
        this.vx = (Math.random() - 0.5) * 0.4;
        this.vy = (Math.random() - 0.5) * 0.4;
        this.r = Math.random() * 1.8 + 0.4;
        this.alpha = Math.random() * 0.5 + 0.15;
        this.hue = Math.random() > 0.7 ? 280 : 190;
      }
      update() {
        this.x += this.vx; this.y += this.vy;
        if (this.x < 0 || this.x > w || this.y < 0 || this.y > h) this.reset();
      }
      draw() {
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.r, 0, Math.PI * 2);
        ctx.fillStyle = `hsla(${this.hue},100%,60%,${this.alpha})`;
        ctx.fill();
      }
    }

    particles = Array.from({ length: 120 }, () => new P());

    const drawLines = () => {
      for (let i = 0; i < particles.length; i++) {
        for (let j = i + 1; j < particles.length; j++) {
          const dx = particles[i].x - particles[j].x;
          const dy = particles[i].y - particles[j].y;
          const dist = Math.sqrt(dx * dx + dy * dy);
          if (dist < 100) {
            ctx.beginPath();
            ctx.moveTo(particles[i].x, particles[i].y);
            ctx.lineTo(particles[j].x, particles[j].y);
            ctx.strokeStyle = `rgba(0,229,255,${0.08 * (1 - dist / 100)})`;
            ctx.lineWidth = 0.8;
            ctx.stroke();
          }
        }
      }
    };

    const loop = () => {
      ctx.clearRect(0, 0, w, h);
      particles.forEach(p => { p.update(); p.draw(); });
      drawLines();
      animId = requestAnimationFrame(loop);
    };
    loop();
    return () => { cancelAnimationFrame(animId); window.removeEventListener("resize", resize); };
  }, []);
  return <canvas id="particle-canvas" ref={canvasRef} />;
}

/* ─── MAIN APP ────────────────────────────────────────────── */
const TOOLS_DATA = [
  { id: "parse", icon: "📄", title: "File Parser", desc: "Extract text from TXT, PDF, DOCX files instantly.", badge: "offline", color: "#39ff14" },
  { id: "ocr", icon: "🖼️", title: "OCR Vision", desc: "Run Tesseract OCR on images. Extract text from screenshots.", badge: "offline", color: "#39ff14" },
  { id: "summarize", icon: "📝", title: "Summarizer", desc: "AI-powered text summarization via local LLM.", badge: "offline", color: "#39ff14" },
  { id: "command", icon: "⚡", title: "Sandbox Exec", desc: "Run whitelisted shell commands in a safe sandbox.", badge: "offline", color: "#39ff14" },
  { id: "search", icon: "🌐", title: "Web Search", desc: "DuckDuckGo search. No API key. Privacy-first.", badge: "online", color: "#00e5ff" },
  { id: "fetch", icon: "🔗", title: "Web Fetch", desc: "Download and parse any webpage into clean text.", badge: "online", color: "#00e5ff" },
  { id: "memory", icon: "🧠", title: "RAG Memory", desc: "ChromaDB vector memory. Stores and recalls context.", badge: "offline", color: "#39ff14" },
];

const HINTS = ["/help", "/tools", "/status", "/file path", "summarize ...", "search for ...", "fetch https://..."];

export default function App() {
  const [style] = useState(() => {
    const s = document.createElement("style");
    s.textContent = CSS;
    document.head.appendChild(s);
    return s;
  });

  const [activeTab, setActiveTab] = useState("chat");
  const [messages, setMessages] = useState([
    { role: "agent", text: "System initialized. All offline tools ready. Type a command or pick a hint below." , time: new Date() }
  ]);
  const [input, setInput] = useState("");
  const [typing, setTyping] = useState(false);
  const [isOnline, setIsOnline] = useState(true);
  const [showUpload, setShowUpload] = useState(false);
  const chatRef = useRef(null);
  const textRef = useRef(null);

  // Simulate online check
  useEffect(() => {
    const check = () => setIsOnline(navigator.onLine);
    check();
    window.addEventListener("online", check);
    window.addEventListener("offline", check);
    return () => { window.removeEventListener("online", check); window.removeEventListener("offline", check); };
  }, []);

  // Auto scroll
  useEffect(() => {
    if (chatRef.current) chatRef.current.scrollTop = chatRef.current.scrollHeight;
  }, [messages, typing]);

  const fmt = (d) => d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

  // Simulated agent responses
  const RESPONSES = {
    "/help": "Available commands:\n• /help      → Show this help\n• /tools     → List all tools\n• /status    → System status\n• /file <p>  → Parse a file\n• /clear     → Clear history\n• /quit      → Exit\n\nOr just type naturally — the agent routes automatically.",
    "/tools": "📦 Loaded Tools:\n━━━━━━━━━━━━━━━━━━━━━\n📄 parse_file   → TXT, PDF, DOCX\n🖼️  ocr_image    → Tesseract OCR\n📝 summarize    → LLM summarization\n⚡ run_command  → Sandboxed exec\n🌐 web_search   → DuckDuckGo\n🔗 web_fetch    → Page extraction\n🧠 memory       → ChromaDB RAG",
    "/status": `System Status Report\n━━━━━━━━━━━━━━━━━━━━━\n🤖 LLM Model   : phi3:mini (3.8B)\n🏠 LLM Host    : http://localhost:11434\n🌐 Network     : ${navigator.onLine ? "🟢 Online" : "🔴 Offline"}\n🗄️  Memory DB   : ./data/chroma_db\n📦 Embedding   : all-MiniLM-L6-v2\n🛡️  Sandbox     : Enabled (10s timeout)\n✅ All systems nominal.`,
  };

  const sendMessage = useCallback(() => {
    const text = input.trim();
    if (!text) return;
    setInput("");
    setMessages(prev => [...prev, { role: "user", text, time: new Date() }]);
    setTyping(true);

    const delay = 800 + Math.random() * 1200;
    setTimeout(() => {
      setTyping(false);
      const lower = text.toLowerCase();
      let reply;
      if (RESPONSES[lower]) {
        reply = RESPONSES[lower];
      } else if (lower.includes("summarize")) {
        reply = "📝 Summarization pipeline activated.\n\nRouting → LLM (phi3:mini) → Generating summary...\n\n⚡ Result:\nThe provided text has been condensed to its key points. All filler and redundant information has been removed. Core insights preserved.\n\n[Offline tool — no internet required]";
      } else if (lower.includes("search")) {
        reply = isOnline
          ? "🌐 Web Search activated → DuckDuckGo\n\nQuery routed. Fetching top 5 results...\n\n📌 Results:\n1. Result Title — snippet preview...\n2. Another Result — more context here...\n3. Third Match — relevant snippet...\n\n[Online tool — internet required]"
          : "⚠️ Web search requires internet.\nYou are currently OFFLINE.\nOnline tools are disabled until connectivity is restored.";
      } else if (lower.includes("fetch") || lower.includes("http")) {
        reply = isOnline
          ? "🔗 Web Fetch activated.\n\nDownloading page... extracting text...\n\n✅ Page parsed successfully.\n• Stripped: scripts, styles, nav, ads\n• Extracted: 3,420 characters of clean text\n• Ready for LLM processing.\n\n[Online tool — internet required]"
          : "⚠️ Web fetch requires internet. Currently OFFLINE.";
      } else if (lower.includes("ocr") || lower.includes("image")) {
        reply = "🖼️ OCR Pipeline activated.\n\nPreprocessing → Grayscale → Binarize → Resize\nRunning Tesseract (eng, psm=3, oem=3)...\n\n✅ Text extracted successfully.\n• Characters detected: 847\n• Confidence: High\n• Language: English\n\n[Offline tool — Tesseract, no internet required]";
      } else if (lower.includes("command") || lower.includes("run") || lower.includes("exec")) {
        reply = "⚡ Sandbox Executor activated.\n\n🔍 Extracting command via LLM...\n✅ Command: echo \"hello\"\n🛡️  Whitelist check: PASSED\n⏱️  Executing (timeout: 10s)...\n\n✅ Output:\nhello\n\n[Offline tool — sandboxed, shell=False]";
      } else if (lower.includes("memory") || lower.includes("remember")) {
        reply = "🧠 Memory Store (ChromaDB)\n\n📥 Storing interaction...\n• Embedding via all-MiniLM-L6-v2\n• Vector dim: 384\n• Stored to: ./data/chroma_db\n\n📤 Retrieving relevant context...\n• Top 3 similar memories found\n• Injecting into next LLM prompt\n\n[Offline — persistent local vector DB]";
      } else {
        reply = `🤖 Processing via phi3:mini (local LLM)...\n\nInput routed → Agent Core → Tool Router → General LLM\n\n📝 Response:\nI've analyzed your query. Based on my local knowledge and any available memory context, here is my response. Note: I run entirely offline on your machine with zero cloud dependency.\n\n⚡ Latency: ~3.2s | Tokens: 87 | Model: phi3:mini`;
      }
      setMessages(prev => [...prev, { role: "agent", text: reply, time: new Date() }]);
    }, delay);
  }, [input, isOnline]);

  const handleKey = (e) => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage(); }
  };

  const sidebarItems = [
    { id: "chat", icon: "💬", label: "Chat" },
    { id: "tools", icon: "🧩", label: "Tools" },
    { id: "status", icon: "📊", label: "System" },
  ];

  return (
    <>
      <ParticleCanvas />
      <div className="scanlines" />
      <div className="corner tl"/><div className="corner tr"/><div className="corner bl"/><div className="corner br"/>

      <style>{CSS}</style>

      <div className="app-shell">
        {/* TOPBAR */}
        <div className="topbar">
          <div className="topbar-logo">
            <div className="logo-icon">
              <span style={{ fontSize: 18 }}>🤖</span>
            </div>
            <h1>OpenAgent</h1>
          </div>
          <div className="topbar-status">
            <div className="status-pill">
              <div className={`status-dot ${isOnline ? "" : "offline"}`} />
              <span>{isOnline ? "NETWORK ONLINE" : "NETWORK OFFLINE"}</span>
            </div>
            <div className="status-pill">
              <div className="status-dot" style={{ background: "#e040fb", boxShadow: "0 0 8px #e040fb" }} />
              <span>LLM ACTIVE</span>
            </div>
            <div className="status-pill">
              <div className="status-dot" />
              <span>MEMORY OK</span>
            </div>
          </div>
        </div>

        {/* SIDEBAR */}
        <div className="sidebar">
          <div className="sidebar-section-label">Navigation</div>
          {sidebarItems.map(item => (
            <button key={item.id} className={`sidebar-btn ${activeTab === item.id ? "active" : ""}`} onClick={() => setActiveTab(item.id)}>
              <div className="active-bar" />
              <span className="btn-icon">{item.icon}</span>
              <span>{item.label}</span>
            </button>
          ))}
          <div className="sidebar-section-label" style={{ marginTop: 24 }}>Quick Tools</div>
          {TOOLS_DATA.slice(0, 4).map(t => (
            <button key={t.id} className="sidebar-btn" onClick={() => { setActiveTab("chat"); setInput(t.id === "parse" ? "/file " : t.id === "ocr" ? "ocr " : t.id === "summarize" ? "summarize " : "run command: "); textRef.current?.focus(); }}>
              <span className="btn-icon">{t.icon}</span>
              <span>{t.title}</span>
            </button>
          ))}
          <div style={{ marginTop: "auto", paddingTop: 20 }}>
            <div className="glow-line" />
            <div style={{ fontFamily: "'Share Tech Mono', monospace", fontSize: 10, color: "var(--text-secondary)", padding: "8px 10px", lineHeight: 1.8 }}>
              <div>Model: phi3:mini</div>
              <div>Embedding: MiniLM-L6</div>
              <div>DB: ChromaDB</div>
              <div>v0.1.0 — MIT License</div>
            </div>
          </div>
        </div>

        {/* MAIN */}
        <div className="main-content">
          {/* ── CHAT TAB ── */}
          {activeTab === "chat" && (
            <>
              <div className="chat-area" ref={chatRef}>
                {messages.map((m, i) => (
                  <div key={i} className={`msg ${m.role}`}>
                    <div className={`msg-avatar ${m.role}`}>
                      {m.role === "user" ? "👤" : "🤖"}
                    </div>
                    <div className="msg-bubble">
                      <div className="msg-meta">{m.role === "agent" ? "OPENAGENT" : "YOU"} — {fmt(m.time)}</div>
                      <div className="msg-text">{m.text}</div>
                    </div>
                  </div>
                ))}
                {typing && (
                  <div className="msg agent">
                    <div className="msg-avatar agent">🤖</div>
                    <div className="msg-bubble">
                      <div className="msg-meta">OPENAGENT — processing...</div>
                      <div className="typing-dots"><span/><span/><span/></div>
                    </div>
                  </div>
                )}
              </div>
              <div className="input-bar">
                <div className="input-row">
                  <textarea ref={textRef} value={input} onChange={e => setInput(e.target.value)} onKeyDown={handleKey} placeholder="Type a command or ask anything..." rows={1} />
                  <div className="input-actions">
                    <button className="action-btn" onClick={() => setShowUpload(true)} title="Upload file">📎</button>
                    <button className="send-btn" onClick={sendMessage} title="Send">▶</button>
                  </div>
                </div>
                <div className="input-hints">
                  {HINTS.map(h => (
                    <div key={h} className="hint-tag" onClick={() => { setInput(h); textRef.current?.focus(); }}>{h}</div>
                  ))}
                </div>
              </div>
            </>
          )}

          {/* ── TOOLS TAB ── */}
          {activeTab === "tools" && (
            <div className="tools-panel">
              <div className="panel-header">⚙️ Available Tools</div>
              <div className="tools-grid">
                {TOOLS_DATA.map(t => (
                  <div key={t.id} className="tool-card" onClick={() => { setActiveTab("chat"); setInput(t.id === "parse" ? "/file " : t.id === "ocr" ? "ocr this image" : t.id === "summarize" ? "summarize " : t.id === "command" ? "run command: echo hello" : t.id === "search" ? "search for " : t.id === "fetch" ? "fetch https://" : "memory status"); setTimeout(() => textRef.current?.focus(), 100); }}>
                    <div className="tool-card-icon" style={{ background: t.badge === "offline" ? "rgba(57,255,20,0.1)" : "rgba(0,229,255,0.1)", border: `1px solid ${t.badge === "offline" ? "rgba(57,255,20,0.3)" : "rgba(0,229,255,0.3)"}` }}>
                      {t.icon}
                    </div>
                    <div className="tool-card-title">{t.title}</div>
                    <div className="tool-card-desc">{t.desc}</div>
                    <div className={`tool-badge ${t.badge === "offline" ? "badge-offline" : "badge-online"}`}>{t.badge}</div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* ── STATUS TAB ── */}
          {activeTab === "status" && (
            <div className="status-panel">
              <div className="panel-header">📊 System Status</div>
              <div className="status-grid">
                <div className="status-card">
                  <div className="status-card-label">LLM Model</div>
                  <div className="status-card-value" style={{ fontSize: 16 }}>phi3:mini</div>
                  <div className="status-card-sub">3.8B params · Q4_K_M · MIT</div>
                  <div className="ring-wrap">
                    <svg className="ring-svg" viewBox="0 0 56 56">
                      <circle className="ring-bg" cx="28" cy="28" r="22" />
                      <circle className="ring-fill" cx="28" cy="28" r="22" strokeDasharray="138.23" strokeDashoffset={138.23 * 0.3} transform="rotate(-90 28 28)" />
                    </svg>
                    <div className="ring-label">CPU Load<br/>Estimated 70%<br/>during inference</div>
                  </div>
                </div>
                <div className="status-card">
                  <div className="status-card-label">Network</div>
                  <div className="status-card-value" style={{ color: isOnline ? "var(--accent-green)" : "#f44336", fontSize: 18 }}>{isOnline ? "🟢 Online" : "🔴 Offline"}</div>
                  <div className="status-card-sub">{isOnline ? "DNS reachable · Online tools enabled" : "No connection · Online tools disabled"}</div>
                  <div className="ring-wrap">
                    <svg className="ring-svg" viewBox="0 0 56 56">
                      <circle className="ring-bg" cx="28" cy="28" r="22" />
                      <circle className="ring-fill" cx="28" cy="28" r="22" strokeDasharray="138.23" strokeDashoffset={isOnline ? 138.23 * 0.05 : 138.23} transform="rotate(-90 28 28)" style={{ stroke: isOnline ? "var(--accent-green)" : "#f44336" }} />
                    </svg>
                    <div className="ring-label">Connectivity<br/>{isOnline ? "95% stable" : "0% — no signal"}<br/>Latency: {isOnline ? "~42ms" : "N/A"}</div>
                  </div>
                </div>
                <div className="status-card">
                  <div className="status-card-label">Memory (ChromaDB)</div>
                  <div className="status-card-value">247</div>
                  <div className="status-card-sub">Vectors stored · 384-dim embeddings</div>
                  <div className="ring-wrap">
                    <svg className="ring-svg" viewBox="0 0 56 56">
                      <circle className="ring-bg" cx="28" cy="28" r="22" />
                      <circle className="ring-fill" cx="28" cy="28" r="22" strokeDasharray="138.23" strokeDashoffset={138.23 * 0.55} transform="rotate(-90 28 28)" style={{ stroke: "var(--accent-magenta)" }} />
                    </svg>
                    <div className="ring-label">Usage<br/>45% capacity<br/>~55K vectors max</div>
                  </div>
                </div>
                <div className="status-card">
                  <div className="status-card-label">Sandbox Security</div>
                  <div className="status-card-value" style={{ color: "var(--accent-green)", fontSize: 18 }}>🛡️ Armed</div>
                  <div className="status-card-sub">Whitelist: 9 commands · Timeout: 10s</div>
                  <div style={{ marginTop: 12 }}>
                    {["echo","date","whoami","ls","cat","wc","pwd","env","python3"].map(cmd => (
                      <span key={cmd} style={{ display:"inline-block", fontFamily:"'Share Tech Mono',monospace", fontSize:10, color:"var(--accent-green)", background:"rgba(57,255,20,0.08)", border:"1px solid rgba(57,255,20,0.2)", padding:"2px 8px", borderRadius:12, margin:"2px 3px" }}>{cmd}</span>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* UPLOAD OVERLAY */}
      {showUpload && (
        <div className="upload-overlay">
          <button className="upload-close" onClick={() => setShowUpload(false)}>✕</button>
          <div className="upload-box">
            <div className="upload-icon">📁</div>
            <div className="upload-title">Upload File</div>
            <div className="upload-sub">Drop a file here or click to browse.<br/>The agent will parse and analyze it.</div>
            <label>
              <input type="file" style={{ display: "none" }} onChange={(e) => {
                const f = e.target.files?.[0];
                if (f) {
                  setShowUpload(false);
                  setInput(`/file ${f.name}`);
                  setMessages(prev => [...prev, { role: "agent", text: `📎 File detected: ${f.name}\n\nDetecting format... Routing to parser...\n\n✅ Parser selected based on extension.\nReady to extract and analyze.\n\nType "summarize" or "analyze" to proceed.`, time: new Date() }]);
                }
              }} accept=".txt,.pdf,.docx,.png,.jpg,.jpeg,.bmp" />
              <span className="upload-btn">Browse Files</span>
            </label>
            <div className="upload-supported">Supported: TXT · PDF · DOCX · PNG · JPG · BMP</div>
          </div>
        </div>
      )}
    </>
  );
}
