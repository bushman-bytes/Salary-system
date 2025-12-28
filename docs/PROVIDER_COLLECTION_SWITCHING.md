# Provider-Based Collection Switching

## Overview

The system now automatically uses **different ChromaDB collections** based on the AI provider to handle different embedding dimensions:

- **OpenAI**: `salary_queries` (1536 dimensions)
- **Hugging Face**: `salary_queries_hugFace` (384 dimensions)

## How It Works

### Automatic Collection Selection

The collection name is **automatically determined** in `app/ai_agent/config.py`:

```python
BASE_COLLECTION_NAME = "salary_queries"  # From .env or default

if AI_PROVIDER == "huggingface":
    CHROMA_COLLECTION_NAME = "salary_queries_hugFace"
else:
    CHROMA_COLLECTION_NAME = "salary_queries"
```

### Components Updated

All components automatically use the correct collection:

1. ✅ **config.py** - Dynamically sets collection name
2. ✅ **vector_store.py** - Uses correct collection, recreates on provider switch
3. ✅ **rag_engine.py** - Uses vector store (automatic)
4. ✅ **knowledge_base_builder.py** - Uses vector store (automatic)
5. ✅ **report_generator.py** - Uses RAG engine (automatic)

## Usage

### Building Knowledge Base

The build script automatically uses the correct collection:

```bash
# For Hugging Face (current setting)
AI_PROVIDER=huggingface
python scripts/build_knowledge_base.py
# → Builds: salary_queries_hugFace

# For OpenAI
AI_PROVIDER=openai
python scripts/build_knowledge_base.py
# → Builds: salary_queries
```

### Switching Providers

1. Change `AI_PROVIDER` in `.env`
2. Restart application (vector store auto-recreates)
3. Build knowledge base for new provider (if not already built)

### Both Collections Can Coexist

- Both collections exist simultaneously in ChromaDB Cloud
- Switching providers automatically uses the correct one
- No manual intervention needed

## Testing

Run the test script to verify:

```bash
python scripts/test_collection_switch.py
```

This will show:
- Current provider
- Active collection name
- Whether all components are using the correct collection

## Current Status

✅ **Configuration**: Automatically switches collection based on provider  
✅ **Vector Store**: Recreates instance when collection changes  
✅ **RAG Engine**: Uses correct collection automatically  
✅ **Knowledge Base Builder**: Shows which collection is being used  
✅ **Build Script**: Displays collection information  

## Next Steps

1. **Build Hugging Face collection**:
   ```bash
   python scripts/build_knowledge_base.py
   ```

2. **Test the system**:
   - Use agent dashboard: `http://localhost:8000/agent-dashboard`
   - Try natural language queries
   - Verify responses use Hugging Face model

3. **Switch back to OpenAI** (if needed):
   - Change `AI_PROVIDER=openai` in `.env`
   - Restart application
   - System automatically uses `salary_queries` collection

Everything is ready! 🚀
