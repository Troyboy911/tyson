#!/usr/bin/env python3
"""
Flask API wrapper for Tyson Perplexity Agent
Provides REST endpoints to interact with the agent
"""
from flask import Flask, request, jsonify
from agent import PerplexityAgent
import os
import sys

app = Flask(__name__)

# Initialize agent globally
try:
    agent = PerplexityAgent()
    print(f"✓ Agent initialized with model: {agent.model}")
    print(f"✓ {len(agent.tools)} tools registered")
except ValueError as e:
    print(f"Error initializing agent: {e}")
    print("Please set PERPLEXITY_API_KEY environment variable")
    sys.exit(1)

@app.route('/', methods=['GET'])
def home():
    """Home endpoint with API information"""
    return jsonify({
        'name': 'Tyson Perplexity Agent API',
        'version': '1.0.0',
        'status': 'running',
        'model': agent.model,
        'tools': len(agent.tools),
        'endpoints': {
            '/': 'API information (this page)',
            '/health': 'Health check',
            '/chat': 'POST - Send message to agent',
            '/history': 'GET - Get conversation history',
            '/clear': 'POST - Clear conversation history'
        }
    })

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'agent': 'ready'
    })

@app.route('/chat', methods=['POST'])
def chat():
    """
    Chat endpoint
    
    Request body:
    {
        "message": "Your message here",
        "stream": false  # optional, defaults to false
    }
    """
    try:
        data = request.json
        
        if not data or 'message' not in data:
            return jsonify({
                'error': 'Missing message in request body',
                'success': False
            }), 400
        
        message = data.get('message', '')
        stream = data.get('stream', False)
        
        # Get response from agent
        response = agent.chat(message, stream=stream)
        
        return jsonify({
            'response': response,
            'success': True
        })
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'success': False
        }), 500

@app.route('/history', methods=['GET'])
def get_history():
    """Get conversation history"""
    try:
        history = agent.get_history()
        return jsonify({
            'history': history,
            'count': len(history),
            'success': True
        })
    except Exception as e:
        return jsonify({
            'error': str(e),
            'success': False
        }), 500

@app.route('/clear', methods=['POST'])
def clear_history():
    """Clear conversation history"""
    try:
        agent.clear_history()
        return jsonify({
            'message': 'Conversation history cleared',
            'success': True
        })
    except Exception as e:
        return jsonify({
            'error': str(e),
            'success': False
        }), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8000))
    print(f"\n🚀 Starting Tyson Agent API on port {port}")
    print(f"📡 Access the API at http://0.0.0.0:{port}")
    app.run(host='0.0.0.0', port=port, debug=False)
