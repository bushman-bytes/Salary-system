"""
Script to check and verify the vector store contents.

This script allows you to:
- View collection information
- Count documents
- Search for documents
- View document metadata
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.ai_agent.vector_store import get_vector_store
from app.ai_agent.config import CHROMA_COLLECTION_NAME, CHROMA_CLOUD_MODE
from app.ai_agent.rag_engine import get_rag_engine


def check_collection_info():
    """Check basic collection information."""
    print("=" * 70)
    print("Vector Store Information")
    print("=" * 70)
    print()
    
    print(f"Collection Name: {CHROMA_COLLECTION_NAME}")
    print(f"Mode: {CHROMA_CLOUD_MODE}")
    print()
    
    try:
        vector_store = get_vector_store()
        print("✅ Vector store connection successful!")
        print()
        
        # Try to get collection info
        try:
            # Search for any document to verify collection exists
            results = vector_store.similarity_search("test", k=1)
            print(f"✅ Collection '{CHROMA_COLLECTION_NAME}' exists and is accessible")
        except Exception as e:
            print(f"⚠️  Could not query collection: {e}")
            print("   Collection may be empty or not yet created")
        
    except Exception as e:
        print(f"❌ Error connecting to vector store: {e}")
        return False
    
    return True


def count_documents():
    """Count documents in the collection."""
    print("\n" + "=" * 70)
    print("Document Count")
    print("=" * 70)
    print()
    
    try:
        vector_store = get_vector_store()
        rag_engine = get_rag_engine()
        
        # Try different queries to get documents
        test_queries = [
            "employee",
            "financial",
            "advance",
            "summary",
            "report"
        ]
        
        all_doc_ids = set()
        for query in test_queries:
            try:
                docs = rag_engine.retrieve_context(query, k=100)  # Get many
                for doc in docs:
                    # Use content hash as unique identifier
                    doc_id = hash(doc.page_content)
                    all_doc_ids.add(doc_id)
            except:
                pass
        
        if all_doc_ids:
            print(f"✅ Found approximately {len(all_doc_ids)} unique documents")
        else:
            print("⚠️  No documents found in collection")
            print("   Collection may be empty")
        
        # Try a direct search
        try:
            results = vector_store.similarity_search("", k=100)
            print(f"   Direct search found: {len(results)} documents")
        except Exception as e:
            print(f"   Direct search error: {e}")
        
    except Exception as e:
        print(f"❌ Error counting documents: {e}")


def search_documents(query: str = "employee", k: int = 5):
    """Search for documents and display results."""
    print("\n" + "=" * 70)
    print(f"Search Results for: '{query}'")
    print("=" * 70)
    print()
    
    try:
        rag_engine = get_rag_engine()
        docs = rag_engine.retrieve_context(query, k=k)
        
        if not docs:
            print("⚠️  No documents found")
            return
        
        print(f"Found {len(docs)} document(s):\n")
        
        for i, doc in enumerate(docs, 1):
            print(f"--- Document {i} ---")
            metadata = doc.metadata
            content_preview = doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content
            
            print(f"Type: {metadata.get('type', 'unknown')}")
            if 'employee_name' in metadata:
                print(f"Employee: {metadata['employee_name']}")
            if 'month' in metadata:
                print(f"Period: {metadata['month']}")
            if 'category' in metadata:
                print(f"Category: {metadata['category']}")
            print(f"Content Preview: {content_preview}")
            print()
        
    except Exception as e:
        print(f"❌ Error searching: {e}")


def list_document_types():
    """List all document types in the collection."""
    print("\n" + "=" * 70)
    print("Document Types Breakdown")
    print("=" * 70)
    print()
    
    try:
        rag_engine = get_rag_engine()
        
        # Search with broad queries to get all types
        all_docs = []
        queries = ["employee", "financial", "advance", "domain", "knowledge"]
        
        seen = set()
        for query in queries:
            docs = rag_engine.retrieve_context(query, k=20)
            for doc in docs:
                doc_id = hash(doc.page_content)
                if doc_id not in seen:
                    seen.add(doc_id)
                    all_docs.append(doc)
        
        if not all_docs:
            print("⚠️  No documents found")
            return
        
        # Count by type
        type_counts = {}
        for doc in all_docs:
            doc_type = doc.metadata.get("type", "unknown")
            type_counts[doc_type] = type_counts.get(doc_type, 0) + 1
        
        print("Document types found:")
        for doc_type, count in sorted(type_counts.items()):
            print(f"  - {doc_type}: {count}")
        
        print(f"\nTotal unique documents: {len(all_docs)}")
        
    except Exception as e:
        print(f"❌ Error listing document types: {e}")


def interactive_search():
    """Interactive search interface."""
    print("\n" + "=" * 70)
    print("Interactive Search")
    print("=" * 70)
    print()
    print("Enter search queries (type 'exit' to quit, 'list' to see types)")
    print()
    
    while True:
        try:
            query = input("Search query: ").strip()
            
            if query.lower() == 'exit':
                break
            elif query.lower() == 'list':
                list_document_types()
                continue
            elif not query:
                continue
            
            search_documents(query, k=3)
            print()
            
        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"Error: {e}")


def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Check Vector Store Contents")
    parser.add_argument(
        "--search",
        type=str,
        help="Search for documents with this query"
    )
    parser.add_argument(
        "--count",
        action="store_true",
        help="Count documents in collection"
    )
    parser.add_argument(
        "--types",
        action="store_true",
        help="List document types breakdown"
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Start interactive search mode"
    )
    
    args = parser.parse_args()
    
    # Always show basic info
    if not check_collection_info():
        return 1
    
    # Run requested operations
    if args.count:
        count_documents()
    
    if args.types:
        list_document_types()
    
    if args.search:
        search_documents(args.search)
    
    if args.interactive:
        interactive_search()
    
    # If no specific action, show summary
    if not any([args.count, args.types, args.search, args.interactive]):
        print("\n" + "=" * 70)
        print("Quick Check")
        print("=" * 70)
        count_documents()
        list_document_types()
        print("\n💡 Tip: Use --search 'query' to search, --interactive for interactive mode")
        print("   Example: python scripts/check_vector_store.py --search 'employee summary'")
    
    return 0


if __name__ == "__main__":
    exit(main())
