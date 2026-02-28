# openagent/ui/server.py
"""
Flask API server to connect the web UI to the OpenAgent backend.
Provides REST API endpoints for chat and system status.
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import asyncio
import sys
import sys
print("DEBUG: Server script starting...")
import os
from pathlib import Path

# Add parent directory of the project to path to support 'import openagent'
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root.parent))
os.chdir(project_root)

# Now import from the project
from openagent.core.agent import Agent
from openagent.core.network import check_connectivity

app = Flask(__name__, static_folder='.')
app.config['MAX_CONTENT_LENGTH'] = 36 * 1024 * 1024  # 36 MB max upload size
CORS(app)  # Enable CORS for local development

# Setup logging
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/openagent.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("server")

# Global agent instance
agent_instance = None
conversation_history = []


async def get_agent():
    """Get or create the agent instance."""
    global agent_instance
    if agent_instance is None:
        agent_instance = await Agent.create()
    return agent_instance


@app.route('/')
def index():
    """Serve the main UI page."""
    return send_from_directory('.', 'index.html')


@app.route('/api/upload', methods=['POST'])
def upload_file():
    """
    Handle file uploads.
    Saves the file to 'uploads' directory and returns the absolute path.
    """
    if 'file' not in request.files:
        return jsonify({'status': 'error', 'message': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'status': 'error', 'message': 'No selected file'}), 400
        
    if file:
        upload_dir = Path(os.getcwd()) / "uploads"
        upload_dir.mkdir(exist_ok=True)
        
        # Safe filename
        filename = file.filename
        filepath = upload_dir / filename
        file.save(filepath)
        
        return jsonify({
            'status': 'success', 
            'filepath': str(filepath.absolute()),
            'filename': filename
        })

@app.route('/api/chat', methods=['POST'])
def chat():
    """
    Handle chat messages from the UI.
    
    Request JSON:
        {
            "message": "user message text"
        }
    
    Response JSON:
        {
            "response": "agent response text",
            "status": "success" | "error"
        }
    """
    global conversation_history
    
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return jsonify({
                'status': 'error',
                'response': 'Empty message received.'
            }), 400
        
        # Run agent
        async def process_message():
            # Use global variable inside this async scope
            global conversation_history
            
            agent = await get_agent()
            print(f"DEBUG CHAT: message='{user_message}'")
            response = await agent.run(user_message, conversation_history)
            
            # Update conversation history
            conversation_history.append({"role": "user", "content": user_message})
            conversation_history.append({"role": "assistant", "content": response})
            
            # Trim history to last 40 messages
            if len(conversation_history) > 40:
                conversation_history = conversation_history[-40:]
            
            return response
        
        # Execute async function using asyncio.run for cleaner loop management in 3.7+
        # This is safer than manually creating and closing loops.
        response = asyncio.run(process_message())
        
        return jsonify({
            'status': 'success',
            'response': response
        })
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'response': f'Error processing message: {str(e)}'
        }), 500


@app.route('/api/status', methods=['GET'])
def status():
    """
    Get system status information.
    
    Response JSON:
        {
            "llm_model": "phi3:mini",
            "llm_host": "http://localhost:11434",
            "network_online": true,
            "memory_db": "./data/chroma_db",
            "status": "success"
        }
    """
    try:
        async def get_status():
            agent = await get_agent()
            online = await check_connectivity()
            
            return {
                'status': 'success',
                'llm_model': agent.cfg.llm.model,
                'llm_host': agent.cfg.llm.host,
                'network_online': online,
                'memory_db': str(agent.cfg.memory.db_path)
            }
        
        status_data = asyncio.run(get_status())
        
        return jsonify(status_data)
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error getting status: {str(e)}'
        }), 500


@app.route('/api/tools', methods=['GET'])
def tools():
    """
    Get list of available tools.
    
    Response JSON:
        {
            "tools": [...],
            "status": "success"
        }
    """
    try:
        async def get_tools():
            agent = await get_agent()
            # Get tool information from agent
            tool_list = []
            for tool_name, tool_obj in agent.tools.items():
                tool_list.append({
                    'name': tool_name,
                    'description': getattr(tool_obj, '__doc__', 'No description available')
                })
            return tool_list
        
        tools_data = asyncio.run(get_tools())
        
        return jsonify({
            'status': 'success',
            'tools': tools_data
        })
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error getting tools: {str(e)}'
        }), 500


@app.route('/api/analyze-image', methods=['POST'])
def analyze_image():
    """
    Handle image upload and analysis via vision AI.
    
    Accepts a file upload, saves it, then runs the full
    vision analysis pipeline (vision AI → web search → synthesis).
    """
    global conversation_history
    
    if 'file' not in request.files:
        return jsonify({'status': 'error', 'response': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'status': 'error', 'response': 'No file selected'}), 400
    
    try:
        # Save the uploaded file
        upload_dir = Path(os.getcwd()) / "uploads"
        upload_dir.mkdir(exist_ok=True)
        filepath = upload_dir / file.filename
        file.save(filepath)
        
        # Run the analysis through the agent
        async def do_analysis():
            global conversation_history
            agent = await get_agent()
            
            # Construct file tag for router
            user_msg = f"Analyse this file: [FILE:{filepath.absolute()}]"
            response = await agent.run(user_msg, conversation_history)
            
            # Update conversation history
            conversation_history.append({"role": "user", "content": f"[Uploaded image: {file.filename}]"})
            conversation_history.append({"role": "assistant", "content": response})
            
            if len(conversation_history) > 40:
                conversation_history = conversation_history[-40:]
            
            return response
        
        response = asyncio.run(do_analysis())
        
        return jsonify({
            'status': 'success',
            'response': response,
            'filename': file.filename
        })
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'response': f'Image analysis failed: {str(e)}'
        }), 500


@app.route('/api/settings', methods=['POST'])
def update_settings():
    """Update agent settings (project path for MCP)."""
    data = request.get_json()
    project_path = data.get('project_path', '')

    from openagent.tools.offline.file_ops import set_project_path
    set_project_path(project_path)

    return jsonify({'status': 'success', 'project_path': project_path})


@app.route('/api/export', methods=['POST'])
def export_response():
    """Export a response as PDF or DOCX with proper filenames."""
    data = request.get_json()
    text = data.get('text', '')
    fmt = data.get('format', 'txt')

    if not text:
        return jsonify({'status': 'error', 'message': 'No text to export'}), 400

    from flask import make_response
    import io

    if fmt == 'docx':
        try:
            from docx import Document
            doc = Document()
            doc.add_heading('OpenAgent Response', level=1)
            for paragraph in text.split('\n'):
                if paragraph.strip():
                    doc.add_paragraph(paragraph)
            buf = io.BytesIO()
            doc.save(buf)
            buf.seek(0)

            response = make_response(buf.read())
            response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            response.headers['Content-Disposition'] = 'attachment; filename=openagent_response.docx'
            return response
        except ImportError:
            response = make_response(text.encode('utf-8'))
            response.headers['Content-Type'] = 'text/plain; charset=utf-8'
            response.headers['Content-Disposition'] = 'attachment; filename=openagent_response.txt'
            return response

    elif fmt == 'pdf':
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.lib.units import inch

            buf = io.BytesIO()
            doc = SimpleDocTemplate(buf, pagesize=letter)
            styles = getSampleStyleSheet()
            story = []
            story.append(Paragraph('OpenAgent Response', styles['Title']))
            story.append(Spacer(1, 0.2 * inch))

            for line in text.split('\n'):
                if line.strip():
                    safe = line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                    story.append(Paragraph(safe, styles['Normal']))
                else:
                    story.append(Spacer(1, 0.1 * inch))

            doc.build(story)
            buf.seek(0)

            response = make_response(buf.read())
            response.headers['Content-Type'] = 'application/pdf'
            response.headers['Content-Disposition'] = 'attachment; filename=openagent_response.pdf'
            return response
        except ImportError:
            response = make_response(text.encode('utf-8'))
            response.headers['Content-Type'] = 'text/plain; charset=utf-8'
            response.headers['Content-Disposition'] = 'attachment; filename=openagent_response.txt'
            return response

    else:
        response = make_response(text.encode('utf-8'))
        response.headers['Content-Type'] = 'text/plain; charset=utf-8'
        response.headers['Content-Disposition'] = 'attachment; filename=openagent_response.txt'
        return response


@app.route('/api/clear', methods=['POST'])
def clear_history():
    """Clear conversation history."""
    global conversation_history
    conversation_history = []
    return jsonify({
        'status': 'success',
        'message': 'Conversation history cleared.'
    })


if __name__ == '__main__':
    print("=" * 60)
    print("  🤖 OpenAgent UI Server")
    print("=" * 60)
    print("")
    print("  Starting server on http://localhost:5000")
    print("  Open your browser and navigate to the URL above")
    print("")
    print("  Press Ctrl+C to stop the server")
    print("=" * 60)
    print("")
    
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
