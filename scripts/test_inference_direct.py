"""Test InferenceClient directly to verify it works with the model."""

import sys
import os
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment
from dotenv import load_dotenv
load_dotenv(project_root / "app" / "config" / ".env")

print("=" * 70)
print("Testing InferenceClient Directly")
print("=" * 70)
print()

try:
    from huggingface_hub import InferenceClient
    
    api_key = os.getenv("HUGGINGFACE_API_KEY")
    model = os.getenv("HUGGINGFACE_MODEL", "mistralai/Mistral-7B-Instruct-v0.3")
    
    print(f"Model: {model}")
    print(f"API Key: {'Set' if api_key else 'Not Set'}")
    print()
    
    if not api_key:
        print("❌ HUGGINGFACE_API_KEY not set!")
        sys.exit(1)
    
    print("1. Creating InferenceClient...")
    client = InferenceClient(model=model, token=api_key)
    print("   ✅ InferenceClient created")
    print()
    
    print("2. Testing chat_completion...")
    response = client.chat_completion(
        model=model,
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say 'test' in one word."}
        ],
        max_tokens=50,
        temperature=0.7,
    )
    
    print(f"   ✅ Response received")
    print(f"   Response type: {type(response)}")
    print()
    
    print("3. Extracting content...")
    # Try the format from user's example
    try:
        content = response.choices[0].message["content"]
        print(f"   ✅ Content extracted: {content}")
    except Exception as e:
        print(f"   ⚠️  Error extracting with []: {e}")
        # Try alternative methods
        if hasattr(response, 'choices'):
            print(f"   Response has choices: {len(response.choices)}")
            if len(response.choices) > 0:
                msg = response.choices[0].message
                print(f"   Message type: {type(msg)}")
                if hasattr(msg, '__dict__'):
                    print(f"   Message dict: {msg.__dict__}")
                content = str(msg)
                print(f"   Content (as string): {content}")
    
    print()
    print("=" * 70)
    print("✅ InferenceClient Test Complete!")
    print("=" * 70)
    
except ImportError as e:
    print(f"❌ Import Error: {e}")
    print("   Install with: pip install huggingface_hub")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
