"""
Simple HTTP server to serve the OpenAgent UI.
Run this instead of server.py if you just want to see the UI without the backend.
"""

import http.server
import socketserver
import webbrowser
from pathlib import Path

PORT = 8080

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # Add CORS headers
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

if __name__ == '__main__':
    # Change to ui directory
    ui_dir = Path(__file__).parent
    import os
    os.chdir(ui_dir)
    
    Handler = MyHTTPRequestHandler
    
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print("=" * 70)
        print("  🤖 OpenAgent UI — Demo Mode")
        print("=" * 70)
        print("")
        print(f"  Server running at: http://localhost:{PORT}")
        print("")
        print("  📌 DEMO MODE: UI will use simulated responses")
        print("  📌 To use real AI: Install Ollama and run server.py instead")
        print("")
        print("  Opening browser automatically...")
        print("  If it doesn't open, navigate to: http://localhost:8000")
        print("")
        print("  Press Ctrl+C to stop the server")
        print("=" * 70)
        print("")
        
        # Try to open browser
        try:
            webbrowser.open(f'http://localhost:{PORT}')
        except:
            pass
        
        httpd.serve_forever()
