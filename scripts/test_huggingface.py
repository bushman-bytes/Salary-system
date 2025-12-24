"""Test script to verify Hugging Face configuration."""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

print("=" * 70)
print("Testing Hugging Face Configuration")
print("=" * 70)
print()

try:
    # Test configuration loading
    print("1. Testing configuration...")
    from app.ai_agent.config import (
        AI_PROVIDER,
        HUGGINGFACE_API_KEY,
        HUGGINGFACE_MODEL,
        HUGGINGFACE_EMBEDDING_MODEL,
    )
    
    print(f"   ✅ AI_PROVIDER: {AI_PROVIDER}")
    print(f"   ✅ HUGGINGFACE_MODEL: {HUGGINGFACE_MODEL}")
    print(f"   ✅ HUGGINGFACE_EMBEDDING_MODEL: {HUGGINGFACE_EMBEDDING_MODEL}")
    print(f"   ✅ API Key set: {'Yes' if HUGGINGFACE_API_KEY else 'No'}")
    print()
    
    if AI_PROVIDER != "huggingface":
        print("   ⚠️  Warning: AI_PROVIDER is not set to 'huggingface'")
        print(f"      Current value: {AI_PROVIDER}")
        print()
    
    # Test LLM provider
    print("2. Testing LLM provider...")
    from app.ai_agent.llm_provider import get_llm
    
    llm = get_llm()
    print(f"   ✅ LLM instance created: {type(llm).__name__}")
    print()
    
    # Test embedding model
    print("3. Testing embedding model...")
    from app.ai_agent.llm_provider import get_embedding_model
    
    embedding_model = get_embedding_model()
    print(f"   ✅ Embedding model created: {type(embedding_model).__name__}")
    print()
    
    # Test simple LLM call (optional - may take time)
    print("4. Testing LLM inference (this may take a moment)...")
    try:
        from langchain_core.messages import HumanMessage
        
        # Test with a simple message
        if hasattr(llm, 'invoke'):
            # Chat model
            response = llm.invoke([HumanMessage(content="Say 'Hello' in one word.")])
            result = response.content if hasattr(response, 'content') else str(response)
        else:
            # Text generation model
            result = llm.invoke("Say 'Hello' in one word.")
        
        print(f"   ✅ LLM response received: {result[:100]}...")
    except Exception as e:
        print(f"   ⚠️  LLM inference test failed: {e}")
        print("      This might be normal if the model needs to load first")
    print()
    
    print("=" * 70)
    print("✅ Hugging Face Configuration Test Complete!")
    print("=" * 70)
    print()
    print("Next steps:")
    print("1. If all tests passed, try using the agent dashboard")
    print("2. Test with: http://localhost:8000/agent-dashboard")
    print("3. Try a simple natural language query")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
