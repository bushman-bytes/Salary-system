"""Test Hugging Face LLM initialization and basic inference."""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

print("=" * 70)
print("Testing Hugging Face LLM")
print("=" * 70)
print()

try:
    from app.ai_agent.config import AI_PROVIDER, HUGGINGFACE_MODEL, HUGGINGFACE_API_KEY
    from app.ai_agent.llm_provider import get_llm
    
    print(f"AI Provider: {AI_PROVIDER}")
    print(f"Model: {HUGGINGFACE_MODEL}")
    print(f"API Key set: {'Yes' if HUGGINGFACE_API_KEY else 'No'}")
    print()
    
    if AI_PROVIDER != "huggingface":
        print("⚠️  AI_PROVIDER is not 'huggingface'")
        print(f"   Current: {AI_PROVIDER}")
        print("   Please set AI_PROVIDER=huggingface in .env")
        sys.exit(1)
    
    print("1. Initializing LLM...")
    llm = get_llm()
    print(f"   ✅ LLM created: {type(llm).__name__}")
    print()
    
    print("2. Testing simple inference...")
    from langchain_core.messages import HumanMessage
    
    try:
        response = llm.invoke([HumanMessage(content="Say 'Hello, world!' in one sentence.")])
        
        if hasattr(response, 'content'):
            result = response.content
        else:
            result = str(response)
        
        print(f"   ✅ Response received: {result[:100]}...")
        print()
        print("=" * 70)
        print("✅ Hugging Face LLM Test PASSED!")
        print("=" * 70)
        
    except Exception as e:
        print(f"   ❌ Inference failed: {e}")
        print()
        print("Troubleshooting:")
        print("1. Check if model is available: https://huggingface.co/models")
        print(f"2. Model: {HUGGINGFACE_MODEL}")
        print("3. Try a different model in .env:")
        print("   HUGGINGFACE_MODEL=mistralai/Mistral-Small-Instruct-2409")
        print("   or")
        print("   HUGGINGFACE_MODEL=Qwen/Qwen2.5-7B-Instruct")
        print()
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
