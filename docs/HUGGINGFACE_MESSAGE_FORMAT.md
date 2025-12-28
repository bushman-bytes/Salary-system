# Hugging Face Chat Message Format

## Overview

The system now uses `mistralai/Mistral-7B-Instruct-v0.3` which supports chat completion format similar to OpenAI.

## Message Format

The Hugging Face Inference API (OpenAI-compatible) expects messages in this format:

```python
messages=[
    {"role": "system", "content": "You are a helpful assistant..."},
    {"role": "user", "content": "Your question here..."}
]
```

## How LangChain Handles This

LangChain's `ChatOpenAI` with Hugging Face base URL automatically converts LangChain messages to this format:

```python
from langchain_core.messages import SystemMessage, HumanMessage

# LangChain format
messages = [
    SystemMessage(content="You are a helpful assistant..."),
    HumanMessage(content="Your question here...")
]

# Automatically converted to:
# [
#     {"role": "system", "content": "..."},
#     {"role": "user", "content": "..."}
# ]
```

## Current Implementation

The system uses `ChatOpenAI` with Hugging Face's OpenAI-compatible endpoint:

```python
ChatOpenAI(
    model="mistralai/Mistral-7B-Instruct-v0.3",
    base_url="https://router.huggingface.co/v1/",  # Updated endpoint
    api_key=HUGGINGFACE_API_KEY,
    temperature=0.3,
    max_tokens=2000,
    top_p=0.9,
)
```

This automatically handles message conversion from LangChain format to Hugging Face format.

## Example Usage

### In Chains

```python
from langchain_core.messages import HumanMessage, SystemMessage

messages = [
    SystemMessage(content="You are an AI assistant for salary management."),
    HumanMessage(content="Generate a summary for employee John Doe.")
]

response = llm.invoke(messages)
# Response is automatically formatted correctly
```

### Direct API Call (Reference)

If using `InferenceClient` directly (like in your example):

```python
from huggingface_hub import InferenceClient

client = InferenceClient(
    model="mistralai/Mistral-7B-Instruct-v0.3",
    token=HUGGINGFACE_API_KEY
)

response = client.chat_completion(
    model="mistralai/Mistral-7B-Instruct-v0.3",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Your question"}
    ],
    max_tokens=200,
    temperature=0.7,
)

print(response.choices[0].message["content"])
```

## Current Configuration

- **Model**: `mistralai/Mistral-7B-Instruct-v0.3`
- **Endpoint**: `https://router.huggingface.co/v1/` (updated from deprecated api-inference endpoint)
- **Format**: OpenAI-compatible chat completion
- **Message Format**: Automatic conversion from LangChain messages

## Testing

Test the message format:

```bash
python scripts/test_hf_llm.py
```

This will verify that:
1. LLM initializes correctly
2. Messages are formatted properly
3. Responses are received

## Notes

- The system automatically converts LangChain messages to the correct format
- No manual message conversion needed
- Works seamlessly with existing LangChain chains
- Compatible with both OpenAI and Hugging Face models
