#!/usr/bin/env python3
"""
Tyson - Perplexity AI Agent with Full Tool Calling Capabilities
A production-ready AI agent using Perplexity API with streaming, tool calling, and multi-turn conversations.
"""

import os
import json
import requests
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime
import sys


class PerplexityAgent:
    """
    Main agent class that handles interactions with Perplexity API
    Supports tool calling, streaming responses, and conversation history
    """
    
    def __init__(self, api_key: Optional[str] = None, model: str = "llama-3.1-sonar-large-128k-online"):
        """
        Initialize the Perplexity Agent
        
        Args:
            api_key: Perplexity API key (defaults to PERPLEXITY_API_KEY env var)
            model: Model to use (default: llama-3.1-sonar-large-128k-online)
        """
        self.api_key = api_key or os.getenv("PERPLEXITY_API_KEY")
        if not self.api_key:
            raise ValueError("Perplexity API key required. Set PERPLEXITY_API_KEY env var or pass api_key parameter")
        
        self.model = model
        self.base_url = "https://api.perplexity.ai"
        self.conversation_history: List[Dict[str, Any]] = []
        self.tools: Dict[str, Callable] = {}
        self.max_iterations = 10  # Prevent infinite loops
        
        # Register default tools
        self._register_default_tools()
    
    def _register_default_tools(self):
        """Register built-in tools for the agent"""
        self.register_tool(
            name="calculate",
            description="Perform mathematical calculations. Supports +, -, *, /, **, sqrt, etc.",
            parameters={
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "The mathematical expression to evaluate"
                    }
                },
                "required": ["expression"]
            },
            function=self._calculate
        )
        
        self.register_tool(
            name="get_current_time",
            description="Get the current date and time",
            parameters={
                "type": "object",
                "properties": {},
                "required": []
            },
            function=self._get_current_time
        )
        
        self.register_tool(
            name="search_web",
            description="Search the web for information using Perplexity's online capabilities",
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query"
                    }
                },
                "required": ["query"]
            },
            function=self._search_web
        )
    
    def register_tool(self, name: str, description: str, parameters: Dict, function: Callable):
        """Register a custom tool for the agent to use"""
        self.tools[name] = {
            "function": function,
            "definition": {
                "type": "function",
                "function": {
                    "name": name,
                    "description": description,
                    "parameters": parameters
                }
            }
        }
    
    def _calculate(self, expression: str) -> str:
        """Built-in calculator tool"""
        try:
            import math
            # Safe eval with limited scope
            allowed_names = {
                k: v for k, v in math.__dict__.items() if not k.startswith("__")
            }
            result = eval(expression, {"__builtins__": {}}, allowed_names)
            return f"Result: {result}"
        except Exception as e:
            return f"Error calculating: {str(e)}"
    
    def _get_current_time(self) -> str:
        """Built-in time tool"""
        now = datetime.now()
        return f"Current date and time: {now.strftime('%Y-%m-%d %H:%M:%S')}"
    
    def _search_web(self, query: str) -> str:
        """Built-in web search (uses Perplexity's online model)"""
        return f"Searching web for: {query} (handled by Perplexity's online model)"
    
    def chat(self, message: str, stream: bool = False) -> str:
        """
        Send a message to the agent and get a response
        
        Args:
            message: User message
            stream: Whether to stream the response
            
        Returns:
            Agent's response
        """
        # Add user message to history
        self.conversation_history.append({
            "role": "user",
            "content": message
        })
        
        iteration = 0
        while iteration < self.max_iterations:
            iteration += 1
            
            # Prepare API request
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Get tool definitions
            tool_definitions = [tool["definition"] for tool in self.tools.values()]
            
            payload = {
                "model": self.model,
                "messages": self.conversation_history,
                "stream": stream
            }
            
            # Add tools if available
            if tool_definitions:
                payload["tools"] = tool_definitions
            
            # Make API call
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                stream=stream
            )
            
            if response.status_code != 200:
                error_msg = f"API Error: {response.status_code} - {response.text}"
                print(error_msg)
                return error_msg
            
            if stream:
                return self._handle_stream(response)
            else:
                return self._handle_response(response.json())
        
        return "Max iterations reached. Ending conversation turn."
    
    def _handle_stream(self, response) -> str:
        """Handle streaming response"""
        full_response = ""
        
        for line in response.iter_lines():
            if line:
                line = line.decode('utf-8')
                if line.startswith('data: '):
                    data = line[6:]
                    if data == '[DONE]':
                        break
                    
                    try:
                        chunk = json.loads(data)
                        if 'choices' in chunk and len(chunk['choices']) > 0:
                            delta = chunk['choices'][0].get('delta', {})
                            if 'content' in delta:
                                content = delta['content']
                                print(content, end='', flush=True)
                                full_response += content
                    except json.JSONDecodeError:
                        continue
        
        print()  # New line after streaming
        
        # Add assistant response to history
        if full_response:
            self.conversation_history.append({
                "role": "assistant",
                "content": full_response
            })
        
        return full_response
    
    def _handle_response(self, response_data: Dict) -> str:
        """Handle non-streaming response with tool calling support"""
        if 'choices' not in response_data or len(response_data['choices']) == 0:
            return "No response from API"
        
        choice = response_data['choices'][0]
        message = choice.get('message', {})
        
        # Check if tool calls were made
        tool_calls = message.get('tool_calls', [])
        
        if tool_calls:
            # Add assistant message with tool calls to history
            self.conversation_history.append(message)
            
            # Execute tool calls
            for tool_call in tool_calls:
                tool_name = tool_call['function']['name']
                tool_args = json.loads(tool_call['function']['arguments'])
                tool_id = tool_call['id']
                
                print(f"\n[Tool Call: {tool_name}]")
                print(f"Arguments: {json.dumps(tool_args, indent=2)}")
                
                # Execute the tool
                if tool_name in self.tools:
                    result = self.tools[tool_name]['function'](**tool_args)
                    print(f"Result: {result}")
                    
                    # Add tool result to history
                    self.conversation_history.append({
                        "role": "tool",
                        "tool_call_id": tool_id,
                        "name": tool_name,
                        "content": str(result)
                    })
                else:
                    error_msg = f"Tool '{tool_name}' not found"
                    print(f"Error: {error_msg}")
                    self.conversation_history.append({
                        "role": "tool",
                        "tool_call_id": tool_id,
                        "name": tool_name,
                        "content": error_msg
                    })
            
            # Make another API call with tool results
            return self.chat("", stream=False)
        
        # Regular text response
        content = message.get('content', '')
        
        # Add to history
        self.conversation_history.append({
            "role": "assistant",
            "content": content
        })
        
        return content
    
    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []
    
    def get_history(self) -> List[Dict[str, Any]]:
        """Get conversation history"""
        return self.conversation_history
    
    def save_history(self, filename: str):
        """Save conversation history to file"""
        with open(filename, 'w') as f:
            json.dump(self.conversation_history, f, indent=2)
    
    def load_history(self, filename: str):
        """Load conversation history from file"""
        with open(filename, 'r') as f:
            self.conversation_history = json.load(f)


def main():
    """
    Main function to run the agent in interactive mode
    """
    print("="*60)
    print("Tyson - Perplexity AI Agent")
    print("="*60)
    print("Type 'exit' or 'quit' to end the conversation")
    print("Type 'clear' to clear conversation history")
    print("Type 'history' to view conversation history")
    print("Type 'stream' to toggle streaming mode")
    print("="*60)
    print()
    
    # Initialize agent
    try:
        agent = PerplexityAgent()
        print(f"✓ Agent initialized with model: {agent.model}")
        print(f"✓ {len(agent.tools)} tools registered")
        print()
    except ValueError as e:
        print(f"Error: {e}")
        print("\nPlease set your Perplexity API key:")
        print("  export PERPLEXITY_API_KEY='your-api-key-here'")
        sys.exit(1)
    
    stream_mode = False
    
    # Interactive loop
    while True:
        try:
            user_input = input("You: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ['exit', 'quit']:
                print("\nGoodbye!")
                break
            
            if user_input.lower() == 'clear':
                agent.clear_history()
                print("✓ Conversation history cleared")
                continue
            
            if user_input.lower() == 'history':
                print("\nConversation History:")
                print(json.dumps(agent.get_history(), indent=2))
                continue
            
            if user_input.lower() == 'stream':
                stream_mode = not stream_mode
                print(f"✓ Streaming mode: {'ON' if stream_mode else 'OFF'}")
                continue
            
            # Get response from agent
            print("\nAgent: ", end='' if stream_mode else '')
            response = agent.chat(user_input, stream=stream_mode)
            
            if not stream_mode:
                print(response)
            
            print()
            
        except KeyboardInterrupt:
            print("\n\nInterrupted. Type 'exit' to quit.")
            print()
        except Exception as e:
            print(f"\nError: {e}")
            print()


if __name__ == "__main__":
    main()
