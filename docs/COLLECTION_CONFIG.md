# ChromaDB Collection Configuration

## Current Configuration

Your ChromaDB Cloud collection is set to: **`salary_queries`**

This collection will be used for:
- Storing all knowledge base documents
- RAG retrieval operations
- Vector similarity searches

## Configuration Location

The collection name is set in `app/config/.env`:
```env
CHROMA_COLLECTION_NAME=salary_queries
```

## How It Works

### When Building Knowledge Base
```bash
python scripts/build_knowledge_base.py
```

All documents will be stored in the `salary_queries` collection in your ChromaDB Cloud.

### When Using RAG
The RAG engine automatically uses the `salary_queries` collection for:
- Context retrieval
- Similarity searches
- Query expansion

## Changing Collection Name

To use a different collection:

1. Update `.env`:
   ```env
   CHROMA_COLLECTION_NAME=your_new_collection_name
   ```

2. Rebuild knowledge base:
   ```bash
   python scripts/build_knowledge_base.py
   ```

## Multiple Collections

You can use different collections for different purposes:

```env
# For queries and summaries
CHROMA_COLLECTION_NAME=salary_queries

# For reports (if you want separate)
# CHROMA_COLLECTION_NAME=salary_reports

# For domain knowledge only
# CHROMA_COLLECTION_NAME=domain_knowledge
```

## Verifying Collection

To check which collection is being used:

```python
from app.ai_agent.config import CHROMA_COLLECTION_NAME
print(f"Using collection: {CHROMA_COLLECTION_NAME}")
```

## Collection in ChromaDB Cloud

In your ChromaDB Cloud dashboard:
- Collection: `salary_queries`
- Database: `salary management` (from CHROMA_CLOUD_DATABASE)
- Tenant: `40f246fd-635e-4449-a7ab-3a506bd3d2b0`

All documents will be stored under this collection when you build the knowledge base.

---

**Note**: The collection will be created automatically when you first add documents to it.
