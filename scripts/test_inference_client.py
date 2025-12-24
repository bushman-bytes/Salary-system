"""Test InferenceClient directly to verify response format."""

import sys
import os
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment
from dotenv import load_dotenv
load_dotenv(project_root / "app" / "config" / ".env")

try:
    from huggingface_hub import InferenceClient
    
    api_key = os.getenv("HUGGINGFACE_API_KEY")
    model = os.getenv("HUGGINGFACE_MODEL", "mistralai/Mistral-7B-Instruct-v0.3")
    
    print("Testing Hugging Face InferenceClient")
    print("=" * 70)
    print(f"Model: {model}")
    print()
    
    client = InferenceClient(model=model, token=api_key)
    
    print("1. Testing chat_completion...")
    response = client.chat_completion(
        model=model,
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say 'test' in one word."}
        ],
        max_tokens=50,
        temperature=0.7,
    )
    
    print(f"Response type: {type(response)}")
    print(f"Response: {response}")
    print()
    
    # Try different ways to extract content
    print("2. Extracting content...")
    if hasattr(response, 'choices'):
        print("  - Has 'choices' attribute")
        if len(response.choices) > 0:
            print(f"  - First choice: {response.choices[0]}")
            message = response.choices[0].message
            print(f"  - Message: {message}")
            if hasattr(message, '__getitem__'):
                content = message["content"]
                print(f"  - Content (via []): {content}")
            elif hasattr(message, 'get'):
                content = message.get("content", "")
                print(f"  - Content (via .get()): {content}")
    elif isinstance(response, dict):
        print("  - Is a dictionary")
        content = response.get("choices", [{}])[0].get("message", {}).get("content", "")
        print(f"  - Content: {content}")
    else:
        print(f"  - Unknown format: {response}")
    
    print()
    print("=" * 70)
    print("✅ Test Complete!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
