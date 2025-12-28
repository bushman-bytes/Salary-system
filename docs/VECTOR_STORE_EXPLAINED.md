# Vector Store Configuration Explained

## What is a Vector Store?

A **vector store** (also called a vector database) is a specialized database designed to store and search through **embeddings** - numerical representations of text that capture semantic meaning.

### Why Do We Need It?

In our RAG (Retrieval Augmented Generation) system, the vector store is the "memory" that helps the AI agent understand context and provide better answers. Here's how it works:

1. **Text → Embeddings**: We convert documents (reports, queries, knowledge) into numerical vectors
2. **Storage**: These vectors are stored in the vector database
3. **Retrieval**: When you ask a question, we:
   - Convert your question to an embedding
   - Search for similar embeddings in the database
   - Retrieve the most relevant documents
   - Use them as context for the LLM

## Configuration Variables Explained

### `VECTOR_STORE_PATH=./vector_store`

**What it does:**
- Specifies the **file system location** where ChromaDB will store all the vector data
- This is a **local directory path** on your computer/server

**Example:**
```
./vector_store/
├── chroma.sqlite3          # ChromaDB's internal database
├── index/                  # Vector index files
└── ...                     # Other metadata files
```

**Why it matters:**
- **Persistence**: Your vector data is saved to disk, so it persists between application restarts
- **Backup**: You can backup this folder to preserve your knowledge base
- **Location**: You can change this to store vectors in a different location (e.g., `/data/vector_store` or `C:\Data\vector_store`)

**Best Practices:**
- Use an absolute path for production: `/var/app/vector_store` or `C:\AppData\vector_store`
- Make sure the directory is writable by your application
- Consider backing up this directory regularly
- Add it to `.gitignore` (it can be large and shouldn't be in version control)

### `CHROMA_COLLECTION_NAME=salary_management_kb`

**What it does:**
- Defines the **name of the collection** within ChromaDB
- A collection is like a "table" or "namespace" that groups related documents together

**Why collections matter:**
- **Organization**: You can have multiple collections for different purposes:
  - `salary_management_kb` - Main knowledge base
  - `historical_reports` - Past reports
  - `query_patterns` - Common query patterns
- **Isolation**: Each collection is separate, so you can manage different types of data independently
- **Flexibility**: You can switch between collections or query specific ones

**Example Use Cases:**
```python
# Different collections for different purposes
CHROMA_COLLECTION_NAME=salary_management_kb        # Main KB
CHROMA_COLLECTION_NAME=employee_summaries            # Employee-specific data
CHROMA_COLLECTION_NAME=financial_reports             # Financial reports
```

## How They Work Together

Here's the flow in our system:

```
1. Application starts
   ↓
2. VectorStore class reads:
   - VECTOR_STORE_PATH → Creates/loads from ./vector_store/
   - CHROMA_COLLECTION_NAME → Opens "salary_management_kb" collection
   ↓
3. When adding documents:
   - Convert text to embeddings
   - Store in ./vector_store/ under "salary_management_kb" collection
   ↓
4. When querying:
   - Convert query to embedding
   - Search in ./vector_store/ within "salary_management_kb" collection
   - Return similar documents
```

## Real-World Example

Let's say you want to generate a summary for employee "John Doe":

1. **Query comes in**: "Generate summary for John Doe"
2. **Vector store search**:
   - Converts query to embedding: `[0.23, -0.45, 0.67, ...]`
   - Searches in `./vector_store/` collection `salary_management_kb`
   - Finds similar documents about:
     - Past summaries for John
     - Similar employee patterns
     - Relevant report templates
3. **Context retrieved**: "John typically requests advances monthly. His average advance is $500..."
4. **LLM uses context**: Generates a better, more informed summary

## Configuration Options

### Development vs Production

**Development (Current):**
```env
VECTOR_STORE_PATH=./vector_store
CHROMA_COLLECTION_NAME=salary_management_kb
```

**Production (Recommended):**
```env
VECTOR_STORE_PATH=/var/app/data/vector_store
CHROMA_COLLECTION_NAME=salary_management_kb_prod
```

### Multiple Environments

You can use different collections for different environments:

```env
# Development
CHROMA_COLLECTION_NAME=salary_management_kb_dev

# Staging
CHROMA_COLLECTION_NAME=salary_management_kb_staging

# Production
CHROMA_COLLECTION_NAME=salary_management_kb_prod
```

## Storage Considerations

### Size
- Each document embedding is typically 384-1536 numbers (depending on model)
- A small knowledge base (1000 documents) might be ~10-50 MB
- Large knowledge bases can be several GB

### Performance
- Local file system (current setup): Fast for small-medium datasets
- For larger datasets, consider:
  - ChromaDB server mode
  - Cloud vector databases (Pinecone, Weaviate)
  - PostgreSQL with pgvector extension

## Security Notes

⚠️ **Important:**
- The vector store may contain sensitive data (employee info, financial data)
- Ensure proper file permissions
- Consider encryption at rest for production
- Don't commit the `vector_store/` directory to git

## Troubleshooting

### Issue: "Permission denied"
**Solution**: Check that the directory exists and is writable:
```bash
mkdir -p ./vector_store
chmod 755 ./vector_store
```

### Issue: "Collection not found"
**Solution**: ChromaDB will create the collection automatically on first use. If it doesn't, check:
- Path is correct
- Directory is writable
- No conflicting processes

### Issue: "Vector store is empty"
**Solution**: You need to populate it first! The knowledge base needs to be built (Phase 2.2).

## Next Steps

In **Phase 2.2: RAG Implementation**, we'll:
1. Extract historical data from your database
2. Convert it to embeddings
3. Store it in this vector store
4. Build the knowledge base that makes RAG work

---

**Summary:**
- `VECTOR_STORE_PATH`: Where the vector data is stored on disk
- `CHROMA_COLLECTION_NAME`: The "namespace" for organizing related documents
- Together, they create a searchable knowledge base for your AI agent
