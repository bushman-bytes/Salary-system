"""
Script to build the AI agent knowledge base.

This script:
1. Connects to the database
2. Extracts data and creates documents
3. Generates embeddings
4. Stores in vector database
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.config.config import DATABASE_URL
from app.models.schema import get_engine, get_session
from app.ai_agent.knowledge_base_builder import KnowledgeBaseBuilder
from app.ai_agent.config import AI_PROVIDER, CHROMA_COLLECTION_NAME


def main():
    """Build the knowledge base."""
    print("=" * 60)
    print("AI Agent Knowledge Base Builder")
    print("=" * 60)
    print()
    print(f"AI Provider: {AI_PROVIDER}")
    print(f"Collection Name: {CHROMA_COLLECTION_NAME}")
    print()
    print("Note: Collection name is automatically set based on AI provider:")
    print("  - OpenAI: 'salary_queries' (1536 dimensions)")
    print("  - Hugging Face: 'salary_queries_hugFace' (384 dimensions)")
    print()
    
    # Validate database connection
    if not DATABASE_URL or DATABASE_URL == "postgresql://username:password@hostname/database?sslmode=require":
        print("❌ Error: DATABASE_URL is not configured properly.")
        print("Please set DATABASE_URL in your .env file.")
        return 1
    
    try:
        # Connect to database
        print("Connecting to database...")
        engine = get_engine(DATABASE_URL)
        session = get_session(engine)
        
        # Create knowledge base builder
        builder = KnowledgeBaseBuilder(session)
        
        # Add domain knowledge first
        print("\n" + "=" * 60)
        print("Adding Domain Knowledge")
        print("=" * 60)
        domain_result = builder.add_domain_knowledge()
        if domain_result["status"] == "success":
            print(f"✅ Added {domain_result['documents_added']} domain knowledge documents")
        else:
            print(f"⚠️  Domain knowledge: {domain_result.get('error', 'unknown error')}")
        
        # Build knowledge base from database
        print("\n" + "=" * 60)
        print("Building Knowledge Base from Database")
        print("=" * 60)
        result = builder.build_knowledge_base(employee_limit=None)
        
        if result["status"] == "success":
            print("\n" + "=" * 60)
            print("✅ Knowledge Base Built Successfully!")
            print("=" * 60)
            print(f"Documents loaded: {result['documents_loaded']}")
            print(f"Documents added: {result['documents_added']}")
            print("\nDocument breakdown:")
            for doc_type, count in result.get("type_counts", {}).items():
                print(f"  - {doc_type}: {count}")
            return 0
        elif result["status"] == "empty":
            print("⚠️  No documents found in database.")
            print("The knowledge base will only contain domain knowledge.")
            return 0
        else:
            print(f"❌ Error building knowledge base: {result.get('error', 'unknown error')}")
            return 1
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        if 'session' in locals():
            session.close()


if __name__ == "__main__":
    exit(main())
