"""Test ChromaDB Cloud connection directly."""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.ai_agent.config import (
    CHROMA_CLOUD_API_KEY,
    CHROMA_CLOUD_TENANT,
    CHROMA_CLOUD_DATABASE,
    CHROMA_COLLECTION_NAME,
)

print("=" * 70)
print("Testing ChromaDB Cloud Connection")
print("=" * 70)
print()

print(f"API Key: {CHROMA_CLOUD_API_KEY[:20]}...")
print(f"Tenant: {CHROMA_CLOUD_TENANT}")
print(f"Database: {CHROMA_CLOUD_DATABASE}")
print(f"Collection: {CHROMA_COLLECTION_NAME}")
print()

try:
    import chromadb
    
    print("1. Creating CloudClient...")
    client = chromadb.CloudClient(
        api_key=CHROMA_CLOUD_API_KEY,
        tenant=CHROMA_CLOUD_TENANT,
        database=CHROMA_CLOUD_DATABASE,
    )
    print("   ✅ CloudClient created successfully!")
    print()
    
    print("2. Testing connection by listing collections...")
    collections = client.list_collections()
    print(f"   ✅ Connection successful! Found {len(collections)} collection(s)")
    print()
    
    print("3. Checking for target collection...")
    collection_names = [c.name for c in collections]
    if CHROMA_COLLECTION_NAME in collection_names:
        print(f"   ✅ Collection '{CHROMA_COLLECTION_NAME}' exists!")
        collection = client.get_collection(CHROMA_COLLECTION_NAME)
        count = collection.count()
        print(f"   📊 Collection has {count} documents")
    else:
        print(f"   ⚠️  Collection '{CHROMA_COLLECTION_NAME}' not found")
        print(f"   Available collections: {collection_names}")
        print(f"   💡 Collection will be created automatically on first use")
    print()
    
    print("=" * 70)
    print("✅ ChromaDB Cloud connection test PASSED!")
    print("=" * 70)
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
