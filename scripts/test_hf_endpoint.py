"""Quick test to verify Hugging Face endpoint update."""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

print("Testing Hugging Face Endpoint Update")
print("=" * 70)
print()

try:
    from app.ai_agent.llm_provider import get_llm
    from langchain_core.messages import SystemMessage, HumanMessage
    
    print("1. Initializing LLM...")
    llm = get_llm()
    print(f"   ✅ LLM Type: {type(llm).__name__}")
    
    # Check if it's using the router endpoint
    if hasattr(llm, 'client') and hasattr(llm.client, 'base_url'):
        base_url = str(llm.client.base_url)
        print(f"   ✅ Base URL: {base_url}")
        if "router.huggingface.co" in base_url:
            print("   ✅ Using updated router endpoint!")
        elif "api-inference.huggingface.co" in base_url:
            print("   ⚠️  Still using deprecated endpoint!")
    print()
    
    print("2. Testing message format...")
    messages = [
        SystemMessage(content="You are a helpful assistant."),
        HumanMessage(content="Say 'test' in one word.")
    ]
    
    print("   Sending test message...")
    response = llm.invoke(messages)
    
    if hasattr(response, 'content'):
        result = response.content.strip()
    else:
        result = str(response).strip()
    
    print(f"   ✅ Response: {result}")
    print()
    print("=" * 70)
    print("✅ Test Complete - Endpoint update successful!")
    print("=" * 70)
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
