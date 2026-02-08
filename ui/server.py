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
