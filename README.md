# Tyson - Perplexity AI Agent

A production-ready AI agent powered by Perplexity API with full tool calling capabilities, streaming responses, and multi-turn conversations.

## Features

- ✅ **Perplexity API Integration** - Uses Perplexity's powerful online models as default
- ✅ **Tool Calling Support** - Built-in tools with ability to register custom tools
- ✅ **Streaming Responses** - Real-time token-by-token responses
- ✅ **Conversation History** - Maintains context across multiple turns
- ✅ **Built-in Tools**:
  - Calculator (mathematical expressions)
  - Current time/date
  - Web search (via Perplexity's online capabilities)
- ✅ **Custom Tool Registration** - Easily add your own tools
- ✅ **Interactive CLI** - Command-line interface for testing
- ✅ **History Management** - Save and load conversation history

## Installation

```bash
# Clone the repository
git clone https://github.com/Troyboy911/tyson.git
cd tyson

# Install dependencies
pip install -r requirements.txt
```

## Quick Start

### 1. Set up your Perplexity API Key

```bash
export PERPLEXITY_API_KEY='your-api-key-here'
```

Get your API key from: https://www.perplexity.ai/settings/api

### 2. Run the agent

```bash
python agent.py
```

### 3. Start chatting!

```
============================================================
Tyson - Perplexity AI Agent
============================================================
Type 'exit' or 'quit' to end the conversation
Type 'clear' to clear conversation history
Type 'history' to view conversation history
Type 'stream' to toggle streaming mode
============================================================

✓ Agent initialized with model: llama-3.1-sonar-large-128k-online
✓ 3 tools registered

You: What's 25 * 847?

Agent: [Tool Call: calculate]
Arguments: {
  "expression": "25 * 847"
}
Result: Result: 21175

The result of 25 * 847 is 21,175.
```

## Usage Examples

### Basic Usage

```python
from agent import PerplexityAgent

# Initialize the agent
agent = PerplexityAgent()

# Have a conversation
response = agent.chat("What's the weather like today?")
print(response)

# Continue the conversation with context
response = agent.chat("Will it rain tomorrow?")
print(response)
```

### With Streaming

```python
agent = PerplexityAgent()
response = agent.chat("Tell me about quantum computing", stream=True)
# Response will stream token by token to console
```

### Register Custom Tools

```python
from agent import PerplexityAgent

agent = PerplexityAgent()

# Define a custom tool
def get_stock_price(symbol: str) -> str:
    # Your implementation here
    return f"Stock price for {symbol}: $150.25"

# Register the tool
agent.register_tool(
    name="get_stock_price",
    description="Get the current stock price for a given symbol",
    parameters={
        "type": "object",
        "properties": {
            "symbol": {
                "type": "string",
                "description": "Stock ticker symbol (e.g., AAPL, GOOGL)"
            }
        },
        "required": ["symbol"]
    },
    function=get_stock_price
)

# Use it
response = agent.chat("What's the price of Apple stock?")
print(response)
```

### Save and Load Conversation History

```python
agent = PerplexityAgent()

# Have some conversations
agent.chat("Hello!")
agent.chat("What's AI?")

# Save history
agent.save_history("conversation.json")

# Later, load it back
new_agent = PerplexityAgent()
new_agent.load_history("conversation.json")
# Conversation context is restored
```

## Configuration

### Available Models

You can use any Perplexity model:

```python
# Default: llama-3.1-sonar-large-128k-online (recommended for agent tasks)
agent = PerplexityAgent(model="llama-3.1-sonar-large-128k-online")

# Other options:
agent = PerplexityAgent(model="llama-3.1-sonar-small-128k-online")
agent = PerplexityAgent(model="llama-3.1-sonar-huge-128k-online")
```

### Environment Variables

- `PERPLEXITY_API_KEY` - Your Perplexity API key (required)

## Interactive CLI Commands

When running `python agent.py`, you have access to these commands:

- `exit` / `quit` - End the conversation
- `clear` - Clear conversation history
- `history` - View full conversation history
- `stream` - Toggle streaming mode on/off

## API Reference

### PerplexityAgent

#### `__init__(api_key: Optional[str] = None, model: str = "llama-3.1-sonar-large-128k-online")`

Initialize the agent.

**Parameters:**
- `api_key` (str, optional): Perplexity API key. Defaults to PERPLEXITY_API_KEY env var.
- `model` (str): Model to use for completions.

#### `chat(message: str, stream: bool = False) -> str`

Send a message and get a response.

**Parameters:**
- `message` (str): User message
- `stream` (bool): Whether to stream the response

**Returns:**
- str: Agent's response

#### `register_tool(name: str, description: str, parameters: Dict, function: Callable)`

Register a custom tool for the agent to use.

**Parameters:**
- `name` (str): Tool name
- `description` (str): What the tool does
- `parameters` (Dict): JSON schema for parameters
- `function` (Callable): Function to execute

#### `clear_history()`

Clear conversation history.

#### `get_history() -> List[Dict[str, Any]]`

Get conversation history.

#### `save_history(filename: str)`

Save conversation history to file.

#### `load_history(filename: str)`

Load conversation history from file.

## Built-in Tools

### calculate
Perform mathematical calculations.
```
You: What's sqrt(144) + 25?
Agent: [calls calculator] Result: 37.0
```

### get_current_time
Get current date and time.
```
You: What time is it?
Agent: [calls time tool] Current date and time: 2025-11-06 18:24:15
```

### search_web
Search the web (uses Perplexity's online model).
```
You: Search for recent AI news
Agent: [uses online search capabilities]
```

## Advanced Usage

### Building Autonomous Agents

The tool calling system enables autonomous agents that can:
- Make decisions
- Execute multiple tools in sequence
- Handle complex multi-step tasks
- Maintain state across interactions

### Integration with External Systems

Register tools that interact with:
- Databases
- APIs
- File systems
- Web services
- Hardware devices

## Troubleshooting

**API Key Error:**
```
Error: Perplexity API key required.
```
Solution: Set your API key with `export PERPLEXITY_API_KEY='your-key'`

**Module Not Found:**
```
ModuleNotFoundError: No module named 'requests'
```
Solution: Install dependencies with `pip install -r requirements.txt`

## Contributing

Contributions welcome! Feel free to:
- Add new built-in tools
- Improve error handling
- Add tests
- Improve documentation
- Report bugs

## License

MIT License - see LICENSE file for details

## Links

- [Perplexity API Documentation](https://docs.perplexity.ai/)
- [Get API Key](https://www.perplexity.ai/settings/api)
- [GitHub Repository](https://github.com/Troyboy911/tyson)

## Support

For issues, questions, or feature requests, please open an issue on GitHub.

---

**Made with ❤️ using Perplexity API**
