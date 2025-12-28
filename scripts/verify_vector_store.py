"""Simple script to verify vector store contents."""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

print("=" * 70)
print("Vector Store Verification")
print("=" * 70)
print()

try:
    from app.ai_agent.vector_store import get_vector_store
    from app.ai_agent.rag_engine import get_rag_engine
    from app.ai_agent.config import CHROMA_COLLECTION_NAME, CHROMA_CLOUD_MODE
    
    print(f"Collection: {CHROMA_COLLECTION_NAME}")
    print(f"Mode: {CHROMA_CLOUD_MODE}")
    print()
    
    # Test connection
    print("Testing connection...")
    vector_store = get_vector_store()
    print("✅ Vector store connected!")
    print()
    
    # Test search
    print("Searching for documents...")
    rag = get_rag_engine()
    
    # Try multiple queries to find documents
    queries = ["employee", "financial", "advance", "summary"]
    all_docs = []
    seen = set()
    
    for query in queries:
        try:
            docs = rag.retrieve_context(query, k=10)
            for doc in docs:
                doc_id = hash(doc.page_content)
                if doc_id not in seen:
                    seen.add(doc_id)
                    all_docs.append(doc)
        except Exception as e:
            print(f"   Query '{query}' error: {e}")
    
    print(f"✅ Found {len(all_docs)} unique documents")
    print()
    
    if all_docs:
        # Count by type
        type_counts = {}
        for doc in all_docs:
            doc_type = doc.metadata.get("type", "unknown")
            type_counts[doc_type] = type_counts.get(doc_type, 0) + 1
        
        print("Document Breakdown:")
        for doc_type, count in sorted(type_counts.items()):
            print(f"  - {doc_type}: {count}")
        print()
        
        # Show sample documents
        print("Sample Documents:")
        for i, doc in enumerate(all_docs[:3], 1):
            print(f"\n  Document {i}:")
            print(f"    Type: {doc.metadata.get('type', 'unknown')}")
            if 'employee_name' in doc.metadata:
                print(f"    Employee: {doc.metadata['employee_name']}")
            print(f"    Preview: {doc.page_content[:100]}...")
    else:
        print("⚠️  No documents found in collection")
        print("   Run: python scripts/build_knowledge_base.py")
    
    print()
    print("=" * 70)
    print("✅ Verification Complete!")
    print("=" * 70)
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
