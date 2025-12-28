"""Debug LLM initialization to see which method is being used."""

import sys
import warnings
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Capture warnings
warnings.simplefilter("always")

print("=" * 70)
print("Debugging LLM Initialization")
print("=" * 70)
print()

try:
    # Check imports
    print("1. Checking imports...")
    try:
        from huggingface_hub import InferenceClient
        print("   ✅ InferenceClient available")
        INFERENCE_CLIENT_AVAILABLE = True
    except ImportError as e:
        print(f"   ❌ InferenceClient not available: {e}")
        INFERENCE_CLIENT_AVAILABLE = False
    
    try:
        from openai import OpenAI
        print("   ✅ OpenAI client available")
        OPENAI_CLIENT_AVAILABLE = True
    except ImportError:
        print("   ❌ OpenAI client not available")
        OPENAI_CLIENT_AVAILABLE = False
    
    print()
    
    # Check config
    print("2. Checking configuration...")
    from app.ai_agent.config import (
        AI_PROVIDER,
        HUGGINGFACE_API_KEY,
        HUGGINGFACE_MODEL,
    )
    print(f"   AI_PROVIDER: {AI_PROVIDER}")
    print(f"   HUGGINGFACE_MODEL: {HUGGINGFACE_MODEL}")
    print(f"   HUGGINGFACE_API_KEY: {'Set' if HUGGINGFACE_API_KEY else 'Not Set'}")
    print()
    
    # Try to create LLM
    print("3. Creating LLM instance...")
    from app.ai_agent.llm_provider import get_llm
    
    # Capture all warnings
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        llm = get_llm()
        
        print(f"   ✅ LLM created: {type(llm).__name__}")
        print(f"   LLM module: {type(llm).__module__}")
        
        # Check which client is being used
        if hasattr(llm, '_client'):
            print(f"   Has _client: {type(llm._client).__name__}")
        if hasattr(llm, 'client'):
            print(f"   Has client: {type(llm.client).__name__}")
        
        # Show warnings
        if w:
            print()
            print("   Warnings captured:")
            for warning in w:
                print(f"   ⚠️  {warning.message}")
    
    print()
    print("=" * 70)
    print("✅ Debug Complete!")
    print("=" * 70)
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
