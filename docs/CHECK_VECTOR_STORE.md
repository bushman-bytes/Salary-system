# How to Check Your Vector Store

## Quick Check

### Basic Information
```bash
python scripts/check_vector_store.py
```

Shows:
- Collection name
- Connection mode (local/cloud)
- Document count
- Document types breakdown

### Search Documents
```bash
python scripts/check_vector_store.py --search "employee summary"
```

### Count Documents
```bash
python scripts/check_vector_store.py --count
```

### List Document Types
```bash
python scripts/check_vector_store.py --types
```

### Interactive Mode
```bash
python scripts/check_vector_store.py --interactive
```

Allows you to:
- Search multiple queries
- Type 'list' to see document types
- Type 'exit' to quit

## Python Code Examples

### Check Collection Exists
```python
from app.ai_agent.vector_store import get_vector_store

store = get_vector_store()
results = store.similarity_search("test", k=1)
print(f"Collection accessible: {len(results) >= 0}")
```

### Count Documents
```python
from app.ai_agent.rag_engine import get_rag_engine

rag = get_rag_engine()
docs = rag.retrieve_context("employee", k=100)
print(f"Found {len(docs)} documents")
```

### Search by Type
```python
from app.ai_agent.rag_engine import get_rag_engine

rag = get_rag_engine()

# Get employee summaries
employee_docs = rag.retrieve_by_type("employee", "employee_summary", k=10)
print(f"Employee summaries: {len(employee_docs)}")

# Get financial patterns
financial_docs = rag.retrieve_by_type("financial", "financial_pattern", k=10)
print(f"Financial patterns: {len(financial_docs)}")
```

### View Document Details
```python
from app.ai_agent.rag_engine import get_rag_engine

rag = get_rag_engine()
docs = rag.retrieve_context("employee summary", k=3)

for i, doc in enumerate(docs, 1):
    print(f"\nDocument {i}:")
    print(f"  Type: {doc.metadata.get('type')}")
    print(f"  Employee: {doc.metadata.get('employee_name', 'N/A')}")
    print(f"  Content: {doc.page_content[:200]}...")
```

### Check Specific Collection in Cloud

If using ChromaDB Cloud, you can also check via the ChromaDB dashboard:
1. Log into ChromaDB Cloud
2. Navigate to your database: `salary management`
3. Check collection: `salary_queries`
4. View documents and metadata

## Expected Results

After building the knowledge base, you should see:

```
Document types found:
  - domain_knowledge: 4
  - employee_summary: 4 (or more, depending on your database)
  - financial_pattern: 1 (or more)
  - advance_pattern: 1 (or more)

Total unique documents: 8+ (depends on your data)
```

## Troubleshooting

### "No documents found"
- Collection may be empty
- Try rebuilding: `python scripts/build_knowledge_base.py`
- Check if documents were actually added (check build output)

### "Collection not found"
- Collection is created automatically on first document add
- If empty, it may not exist yet
- Run build script to create it

### "Permission denied" (Cloud)
- Check API key is correct
- Verify collection name matches
- Try switching to local mode for testing

## Quick Verification

After building, verify with:
```bash
python scripts/check_vector_store.py --types
```

This will show you exactly what's in your vector store!
