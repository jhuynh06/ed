# Anthropic Tool Use — Quick Reference for Theodore

Source: docs.anthropic.com/en/docs/agents-and-tools/tool-use/

## Tool Definition Format

```python
tools = [
    {
        "name": "speak",
        "description": "Send a voice message to the user through Theodore's speaker",
        "input_schema": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "The message to speak"},
                "tone": {
                    "type": "string",
                    "enum": ["warm", "gentle", "reassuring"],
                    "description": "Emotional tone of the voice"
                }
            },
            "required": ["text", "tone"]
        }
    }
]
```

## Client Tool Call Flow
1. Send messages + tools to Claude
2. Claude returns `stop_reason: "tool_use"` with `tool_use` content blocks
3. Your code executes the tool
4. Send back `tool_result` message
5. Claude continues reasoning

## Response Parsing

```python
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    tools=tools,
    messages=messages,
)

for block in response.content:
    if block.type == "tool_use":
        tool_name = block.name      # "speak"
        tool_input = block.input    # {"text": "...", "tone": "warm"}
        tool_id = block.id          # "toolu_xxx"

        # Execute the tool
        result = execute_tool(tool_name, tool_input)

        # Send result back
        messages.append({"role": "assistant", "content": response.content})
        messages.append({
            "role": "user",
            "content": [{
                "type": "tool_result",
                "tool_use_id": tool_id,
                "content": str(result)
            }]
        })
```

## Structured Output with Pydantic (via Anthropic SDK)

```python
from anthropic import Anthropic

client = Anthropic()

# Force a specific tool call for structured output
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    tools=[{
        "name": "evaluate_intervention",
        "description": "Score an intervention",
        "input_schema": EvalScores.model_json_schema()
    }],
    tool_choice={"type": "tool", "name": "evaluate_intervention"},
    messages=messages,
)
```

## Key Pricing Notes
- Tool definitions count as input tokens
- Each model adds ~346 system prompt tokens when tools are present
- Haiku 4.5 is cheapest for high-frequency tool use (perception loop)
- Sonnet 4.5 for quality-critical tool use (planner, evaluator)

## Models for Theodore
- `claude-sonnet-4-20250514` — planner, MAR critics, evaluator
- `claude-haiku-4-20250514` — perception IoT-LLM translation, risk assessment
