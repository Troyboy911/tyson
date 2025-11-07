#!/usr/bin/env python3
"""
Flask API wrapper for Tyson Perplexity Agent
Provides REST endpoints to interact with the agent
"""
from flask import Flask, request, jsonify
from agent import PerplexityAgent
from database import Database
import os
import sys
import uuid

app = Flask(__name__)

# Initialize database
try:
    db = Database()
    db.init_tables()
    print("✓ Database initialized")
except Exception as e:
    print(f"Warning: Database initialization failed: {e}")
    print("Will continue without persistent storage")
    db = None

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
        'version': '2.0.0',
        'status': 'running',
        'model': agent.model,
        'tools': len(agent.tools),
        'database': 'enabled' if db else 'disabled',
        'endpoints': {
            '/': 'API information (this page)',
            '/health': 'Health check',
            '/chat': 'POST - Send message to agent',
            '/sessions': 'GET - List all sessions',
            '/sessions/<session_id>/history': 'GET - Get session conversation history',
            '/history': 'GET - Get current in-memory conversation history',
            '/clear': 'POST - Clear in-memory conversation history',
            '/clear/<session_id>': 'POST - Clear specific session history'
        }
    })

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'agent': 'ready',
        'database': 'connected' if db else 'disconnected'
    })

@app.route('/chat', methods=['POST'])
def chat():
    """
    Chat endpoint with session management
    
    Request body:
    {
        "message": "Your message here",
        "session_id": "optional-session-uuid",
        "stream": false
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
        session_id = data.get('session_id', str(uuid.uuid4()))
        stream = data.get('stream', False)
        
        # Save user message to database if available
        if db:
            db.save_message(session_id, 'user', message)
        
        # Get response from agent
        response = agent.chat(message, stream=stream)
        
        # Save assistant response to database if available
        if db:
            db.save_message(session_id, 'assistant', response)
        
        return jsonify({
            'response': response,
            'session_id': session_id,
            'success': True
        })
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'success': False
        }), 500

@app.route('/sessions', methods=['GET'])
def list_sessions():
    """List all conversation sessions"""
    try:
        if not db:
            return jsonify({
                'error': 'Database not available',
                'success': False
            }), 503
        
        sessions = db.get_sessions()
        return jsonify({
            'sessions': sessions,
            'count': len(sessions),
            'success': True
        })
    except Exception as e:
        return jsonify({
            'error': str(e),
            'success': False
        }), 500

@app.route('/sessions/<session_id>/history', methods=['GET'])
def get_session_history(session_id):
    """Get conversation history for a specific session"""
    try:
        if not db:
            return jsonify({
                'error': 'Database not available',
                'success': False
            }), 503
        
        history = db.get_conversation(session_id)
        return jsonify({
            'session_id': session_id,
            'history': history,
            'count': len(history),
            'success': True
        })
    except Exception as e:
        return jsonify({
            'error': str(e),
            'success': False
        }), 500

@app.route('/history', methods=['GET'])
def get_history():
    """Get current in-memory conversation history"""
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
    """Clear in-memory conversation history"""
    try:
        agent.clear_history()
        return jsonify({
            'message': 'In-memory conversation history cleared',
            'success': True
        })
    except Exception as e:
        return jsonify({
            'error': str(e),
            'success': False
        }), 500

@app.route('/clear/<session_id>', methods=['POST'])
def clear_session(session_id):
    """Clear conversation history for a specific session"""
    try:
        if not db:
            return jsonify({
                'error': 'Database not available',
                'success': False
            }), 503
        
        db.clear_session(session_id)
        return jsonify({
            'message': f'Session {session_id} history cleared',
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
