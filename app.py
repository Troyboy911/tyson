#!/usr/bin/env python3
"""
Tyson Web UI - Advanced AI Agent Interface
Features: Real-time chat, code execution, debugging, tool calling
"""

from flask import Flask, render_template, request, jsonify, session
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import os
import sys
import json
import uuid
from datetime import datetime
from agent import PerplexityAgent
import subprocess
import traceback

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', str(uuid.uuid4()))
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Store agent instances per session
agents = {}

class AdvancedAgent(PerplexityAgent):
    """Extended agent with advanced dev tools"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._register_dev_tools()
    
    def _register_dev_tools(self):
        """Register development tools"""
        
        # Code execution tool
        self.register_tool(
            name="execute_code",
            description="Execute Python code safely and return output",
            parameters={
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "Python code to execute"
                    },
                    "language": {
                        "type": "string",
                        "description": "Programming language (python, javascript, bash)",
                        "default": "python"
                    }
                },
                "required": ["code"]
            },
            function=self._execute_code
        )
        
        # File operations
        self.register_tool(
            name="file_operations",
            description="Read, write, or list files",
            parameters={
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": ["read", "write", "list"],
                        "description": "File operation to perform"
                    },
                    "path": {
                        "type": "string",
                        "description": "File or directory path"
                    },
                    "content": {
                        "type": "string",
                        "description": "Content to write (for write operation)"
                    }
                },
                "required": ["operation", "path"]
            },
            function=self._file_operations
        )
        
        # Web scraping tool
        self.register_tool(
            name="web_scrape",
            description="Scrape content from a web page",
            parameters={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "URL to scrape"
                    },
                    "selector": {
                        "type": "string",
                        "description": "CSS selector (optional)"
                    }
                },
                "required": ["url"]
            },
            function=self._web_scrape
        )
    
    def _execute_code(self, code: str, language: str = "python") -> str:
        """Execute code safely"""
        try:
            if language == "python":
                # Create a safe execution environment
                import io
                from contextlib import redirect_stdout
                
                output = io.StringIO()
                with redirect_stdout(output):
                    exec(code, {"__builtins__": __builtins__})
                
                result = output.getvalue()
                return f"Execution successful:\n{result}" if result else "Code executed successfully (no output)"
            
            elif language == "bash":
                result = subprocess.run(
                    code,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                return f"Output:\n{result.stdout}\n{result.stderr}"
            
            else:
                return f"Language '{language}' not supported yet"
        
        except Exception as e:
            return f"Execution error: {str(e)}\n{traceback.format_exc()}"
    
    def _file_operations(self, operation: str, path: str, content: str = None) -> str:
        """Perform file operations"""
        try:
            if operation == "read":
                with open(path, 'r') as f:
                    return f"File content:\n{f.read()}"
            
            elif operation == "write":
                with open(path, 'w') as f:
                    f.write(content or "")
                return f"Successfully wrote to {path}"
            
            elif operation == "list":
                items = os.listdir(path)
                return f"Directory contents:\n" + "\n".join(items)
            
            else:
                return f"Unknown operation: {operation}"
        
        except Exception as e:
            return f"File operation error: {str(e)}"
    
    def _web_scrape(self, url: str, selector: str = None) -> str:
        """Scrape web content"""
        try:
            import requests
            from bs4 import BeautifulSoup
            
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            if selector:
                elements = soup.select(selector)
                return f"Found {len(elements)} elements:\n" + "\n".join([e.text[:100] for e in elements[:5]])
            else:
                return f"Page title: {soup.title.string if soup.title else 'No title'}\n" \
                       f"Text content (first 500 chars): {soup.get_text()[:500]}"
        
        except Exception as e:
            return f"Scraping error: {str(e)}"

def get_agent(session_id: str) -> AdvancedAgent:
    """Get or create agent for session"""
    if session_id not in agents:
        agents[session_id] = AdvancedAgent()
    return agents[session_id]

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle chat messages"""
    try:
        data = request.json
        message = data.get('message', '')
        session_id = data.get('session_id', str(uuid.uuid4()))
        
        agent = get_agent(session_id)
        response = agent.chat(message, stream=False)
        
        return jsonify({
            'success': True,
            'response': response,
            'session_id': session_id,
            'history': agent.get_history()
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/clear', methods=['POST'])
def clear_history():
    """Clear conversation history"""
    try:
        data = request.json
        session_id = data.get('session_id')
        
        if session_id in agents:
            agents[session_id].clear_history()
        
        return jsonify({'success': True})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/history', methods=['GET'])
def get_history():
    """Get conversation history"""
    try:
        session_id = request.args.get('session_id')
        
        if session_id in agents:
            history = agents[session_id].get_history()
            return jsonify({'success': True, 'history': history})
        
        return jsonify({'success': True, 'history': []})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/tools', methods=['GET'])
def get_tools():
    """Get available tools"""
    try:
        session_id = request.args.get('session_id', 'default')
        agent = get_agent(session_id)
        
        tools = [
            {
                'name': name,
                'description': tool['definition']['function']['description']
            }
            for name, tool in agent.tools.items()
        ]
        
        return jsonify({'success': True, 'tools': tools})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    emit('connected', {'message': 'Connected to Tyson Agent'})

@socketio.on('chat_message')
def handle_chat_message(data):
    """Handle real-time chat messages"""
    try:
        message = data.get('message', '')
        session_id = data.get('session_id', str(uuid.uuid4()))
        
        agent = get_agent(session_id)
        
        # Send typing indicator
        emit('typing', {'typing': True})
        
        # Get response
        response = agent.chat(message, stream=False)
        
        # Send response
        emit('chat_response', {
            'response': response,
            'session_id': session_id,
            'timestamp': datetime.now().isoformat()
        })
        
        emit('typing', {'typing': False})
    
    except Exception as e:
        emit('error', {'error': str(e)})

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port, debug=True)
