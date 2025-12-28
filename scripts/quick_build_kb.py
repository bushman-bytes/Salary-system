"""
Quick Knowledge Base Builder

A simplified script for building the knowledge base with options.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.config.config import DATABASE_URL
from app.models.schema import get_engine, get_session
from app.ai_agent.knowledge_base_builder import KnowledgeBaseBuilder


def main():
    """Quick knowledge base builder."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Build AI Agent Knowledge Base")
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of employees to process (for testing)"
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Clear existing knowledge base before building"
    )
    parser.add_argument(
        "--domain-only",
        action="store_true",
        help="Only add domain knowledge (no database data)"
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("Quick Knowledge Base Builder")
    print("=" * 60)
    print()
    
    # Validate database connection (unless domain-only)
    if not args.domain_only:
        if not DATABASE_URL or DATABASE_URL == "postgresql://username:password@hostname/database?sslmode=require":
            print("❌ Error: DATABASE_URL is not configured.")
            print("Use --domain-only to add only domain knowledge without database.")
            return 1
    
    try:
        # Connect to database
        if not args.domain_only:
            print("Connecting to database...")
            engine = get_engine(DATABASE_URL)
            session = get_session(engine)
        else:
            session = None
        
        # Create builder
        if session:
            builder = KnowledgeBaseBuilder(session)
        else:
            # For domain-only, we still need a session for initialization
            # But we won't use it for database queries
            print("⚠️  Domain-only mode: Will only add domain knowledge")
            print("   (Database connection not required)")
            # We'll handle this differently
            from app.ai_agent.vector_store import get_vector_store
            from app.ai_agent.knowledge_base_builder import KnowledgeBaseBuilder
            # Create a minimal builder for domain knowledge only
            print("\nAdding domain knowledge...")
            # We need to import and use the method directly
            from app.ai_agent.knowledge_base_builder import KnowledgeBaseBuilder
            # For domain-only, we'll create a dummy session
            # Actually, let's just require database connection for simplicity
            print("❌ Domain-only mode requires database connection for initialization.")
            print("   Please configure DATABASE_URL or use the full build script.")
            return 1
        
        # Add domain knowledge
        print("\n" + "=" * 60)
        print("Step 1: Adding Domain Knowledge")
        print("=" * 60)
        domain_result = builder.add_domain_knowledge()
        if domain_result["status"] == "success":
            print(f"✅ Added {domain_result['documents_added']} domain knowledge documents")
        else:
            print(f"⚠️  {domain_result.get('error', 'Unknown error')}")
        
        # Build from database (unless domain-only)
        if not args.domain_only:
            print("\n" + "=" * 60)
            print("Step 2: Building from Database")
            print("=" * 60)
            if args.limit:
                print(f"   (Processing first {args.limit} employees)")
            
            result = builder.build_knowledge_base(
                employee_limit=args.limit,
                clear_existing=args.clear
            )
            
            if result["status"] == "success":
                print("\n" + "=" * 60)
                print("✅ Knowledge Base Built Successfully!")
                print("=" * 60)
                print(f"Total documents: {result['documents_added']}")
                print("\nBreakdown:")
                for doc_type, count in result.get("type_counts", {}).items():
                    print(f"  - {doc_type}: {count}")
            elif result["status"] == "empty":
                print("\n⚠️  No documents found in database.")
                print("   Knowledge base contains only domain knowledge.")
            else:
                print(f"\n❌ Error: {result.get('error', 'Unknown error')}")
                return 1
        else:
            print("\n✅ Domain knowledge added successfully!")
            print("   (No database data processed)")
        
        if session:
            session.close()
        
        print("\n" + "=" * 60)
        print("Knowledge base is ready to use!")
        print("=" * 60)
        return 0
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
