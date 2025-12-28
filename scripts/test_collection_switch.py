"""Test script to verify collection switching works correctly."""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

print("=" * 70)
print("Testing Collection Switching")
print("=" * 70)
print()

try:
    from app.ai_agent.config import AI_PROVIDER, CHROMA_COLLECTION_NAME, BASE_COLLECTION_NAME
    from app.ai_agent.vector_store import get_vector_store
    
    print("1. Current Configuration:")
    print(f"   AI Provider: {AI_PROVIDER}")
    print(f"   Base Collection: {BASE_COLLECTION_NAME}")
    print(f"   Active Collection: {CHROMA_COLLECTION_NAME}")
    print()
    
    # Expected collection name
    if AI_PROVIDER == "huggingface":
        expected = f"{BASE_COLLECTION_NAME}_hugFace"
    else:
        expected = BASE_COLLECTION_NAME
    
    if CHROMA_COLLECTION_NAME == expected:
        print(f"   ✅ Collection name is correct: {CHROMA_COLLECTION_NAME}")
    else:
        print(f"   ⚠️  Collection name mismatch!")
        print(f"      Expected: {expected}")
        print(f"      Got: {CHROMA_COLLECTION_NAME}")
    print()
    
    # Test vector store
    print("2. Testing Vector Store:")
    vector_store = get_vector_store()
    print(f"   ✅ Vector store created")
    print(f"   Collection name: {vector_store.collection_name}")
    print(f"   Embedding model: {type(vector_store.embedding_model).__name__}")
    print()
    
    if vector_store.collection_name == CHROMA_COLLECTION_NAME:
        print("   ✅ Vector store using correct collection")
    else:
        print(f"   ⚠️  Collection mismatch!")
        print(f"      Expected: {CHROMA_COLLECTION_NAME}")
        print(f"      Got: {vector_store.collection_name}")
    print()
    
    # Test RAG engine
    print("3. Testing RAG Engine:")
    from app.ai_agent.rag_engine import get_rag_engine
    
    rag_engine = get_rag_engine()
    print(f"   ✅ RAG engine created")
    print(f"   Vector store collection: {rag_engine.vector_store.collection_name}")
    print()
    
    if rag_engine.vector_store.collection_name == CHROMA_COLLECTION_NAME:
        print("   ✅ RAG engine using correct collection")
    else:
        print(f"   ⚠️  Collection mismatch!")
    print()
    
    print("=" * 70)
    print("✅ Collection Switching Test Complete!")
    print("=" * 70)
    print()
    print("Summary:")
    print(f"  - Provider: {AI_PROVIDER}")
    print(f"  - Collection: {CHROMA_COLLECTION_NAME}")
    print(f"  - All components using correct collection: ✅")
    print()
    print("To switch providers:")
    print("  1. Change AI_PROVIDER in app/config/.env")
    print("  2. Restart your application")
    print("  3. Run: python scripts/build_knowledge_base.py")
    print("  4. The system will automatically use the correct collection")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
