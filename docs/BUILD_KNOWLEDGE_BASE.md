# How to Build the Knowledge Base

## Quick Start

### Step 1: Ensure Prerequisites
1. **Database is configured** - `DATABASE_URL` in `.env` file
2. **Database has data** - At least some employees, advances, or bills
3. **Dependencies installed** - `pip install -r requirements.txt`
4. **AI configuration** - `OPENAI_API_KEY` or `HUGGINGFACE_API_KEY` set

### Step 2: Run the Build Script
```bash
python scripts/build_knowledge_base.py
```

That's it! The script will:
1. ✅ Connect to your database
2. ✅ Extract employee data, financial patterns, and advance patterns
3. ✅ Add domain knowledge (system guidelines)
4. ✅ Generate embeddings
5. ✅ Store in vector database

## What Gets Built

### 1. Domain Knowledge (Always Added)
- System overview and guidelines
- Advance request best practices
- Bill management guidelines
- Report generation guidelines

### 2. Employee Summaries (From Database)
- Employee profiles with role and salary
- Advance request history
- Bill records
- Attendance patterns
- Statistics and insights

### 3. Financial Patterns (From Database)
- Monthly financial summaries
- Advance request trends
- Bill patterns
- Overall financial trends

### 4. Advance Patterns (From Database)
- Status patterns (pending, approved, denied)
- Common request reasons
- Average amounts by status

## Detailed Steps

### Option 1: Build Everything (Recommended)
```bash
python scripts/build_knowledge_base.py
```

This processes:
- All employees
- All financial data (last 12 months)
- All advance patterns

### Option 2: Build with Limit (For Testing)
If you want to test with a smaller dataset:

```python
from app.ai_agent.knowledge_base_builder import KnowledgeBaseBuilder
from app.models.schema import get_engine, get_session
from app.config.config import DATABASE_URL

engine = get_engine(DATABASE_URL)
session = get_session(engine)
builder = KnowledgeBaseBuilder(session)

# Build with only first 5 employees
result = builder.build_knowledge_base(employee_limit=5)
print(result)
```

## Expected Output

### Successful Build
```
============================================================
AI Agent Knowledge Base Builder
============================================================

Connecting to database...

============================================================
Adding Domain Knowledge
============================================================
✅ Added 4 domain knowledge documents

============================================================
Building Knowledge Base from Database
============================================================
Loading documents from database...
Loading employee summaries...
Loading financial patterns...
Loading advance patterns...
Loaded 25 documents

Adding documents to vector store...
Successfully added 25 documents

Document breakdown by type:
  - domain_knowledge: 4
  - employee_summary: 10
  - financial_pattern: 8
  - financial_trend: 1
  - advance_pattern: 2

============================================================
✅ Knowledge Base Built Successfully!
============================================================
Documents loaded: 25
Documents added: 25
```

## What Happens Behind the Scenes

### 1. Document Extraction
- Queries your database for employees, advances, bills
- Creates structured documents with metadata
- Formats data for embedding

### 2. Embedding Generation
- Converts text documents to numerical vectors
- Uses your configured embedding model (OpenAI or Hugging Face)
- Each document becomes a 384-1536 dimensional vector

### 3. Vector Storage
- Stores embeddings in ChromaDB (local or cloud)
- Indexes for fast similarity search
- Preserves metadata for filtering

### 4. Knowledge Base Ready
- Documents are now searchable
- RAG engine can retrieve relevant context
- AI agent can use this for better responses

## Troubleshooting

### "DATABASE_URL is not configured"
**Solution**: Add to `.env`:
```env
DATABASE_URL=postgresql://user:password@host/database?sslmode=require
```

### "No documents found in database"
**Solution**: 
- This is normal if your database is empty
- Add some sample data first
- Or the knowledge base will only contain domain knowledge (which is still useful!)

### "Error adding documents"
**Solution**:
- Check vector store path permissions
- For cloud mode, verify `CHROMA_CLOUD_API_KEY`
- Check embedding model API key is valid

### "Import errors"
**Solution**:
```bash
pip install -r requirements.txt
```

## Updating the Knowledge Base

### Refresh with New Data
Just run the script again:
```bash
python scripts/build_knowledge_base.py
```

It will add new documents. Note: It doesn't delete old ones by default.

### Clear and Rebuild
If you want to start fresh:

```python
from app.ai_agent.knowledge_base_builder import KnowledgeBaseBuilder
from app.models.schema import get_engine, get_session

engine = get_engine(DATABASE_URL)
session = get_session(engine)
builder = KnowledgeBaseBuilder(session)

# Clear and rebuild
result = builder.build_knowledge_base(clear_existing=True)
```

**Note**: ChromaDB doesn't have a direct delete method in LangChain, so you may need to manually delete the `vector_store/` directory for local mode.

## Verification

### Check Knowledge Base
```python
from app.ai_agent.rag_engine import get_rag_engine

rag = get_rag_engine()
docs = rag.retrieve_context("employee summary", k=3)
print(f"Found {len(docs)} documents")
for doc in docs:
    print(f"- {doc.metadata.get('type')}: {doc.page_content[:100]}...")
```

### Test Search
```python
from app.ai_agent.vector_store import get_vector_store

store = get_vector_store()
results = store.similarity_search("financial trends", k=5)
print(f"Found {len(results)} results")
```

## Storage Location

### Local Mode (Default)
- **Location**: `./vector_store/` (or `VECTOR_STORE_PATH`)
- **Files**: ChromaDB SQLite database and index files
- **Size**: ~10-50 MB for small knowledge base, can grow to GBs

### Cloud Mode
- **Location**: ChromaDB Cloud
- **Access**: Via API with `CHROMA_CLOUD_API_KEY`
- **Size**: Managed by ChromaDB

## Best Practices

1. **Build regularly**: Run after adding significant data
2. **Monitor size**: Large knowledge bases can be slow
3. **Backup**: For local mode, backup `vector_store/` directory
4. **Test after build**: Verify retrieval works
5. **Incremental updates**: Just run script again (adds new docs)

## Time Estimates

- **Small database** (< 100 employees): 1-2 minutes
- **Medium database** (100-1000 employees): 2-5 minutes
- **Large database** (> 1000 employees): 5-15 minutes

Time depends on:
- Number of employees
- Amount of historical data
- Embedding model speed
- Network (for cloud embeddings)

## Next Steps

After building the knowledge base:

1. **Test it**: Use RAG engine to retrieve context
2. **Use in AI agent**: Generate summaries and reports
3. **Monitor quality**: Check if retrieved context is relevant
4. **Update regularly**: Rebuild when you add new data

---

**Pro Tip**: Build the knowledge base once, then update it periodically (weekly/monthly) as you add new data to your database.
