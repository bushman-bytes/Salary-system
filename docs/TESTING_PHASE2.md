# Testing Phase 2 - AI Agent Components

## Quick Start

### Basic Test (No API Calls)
```bash
python scripts/test_ai_agent_phase2.py
```

This tests:
- ✅ Configuration validation
- ✅ Vector store initialization
- ✅ Document loader structure
- ✅ RAG engine functionality
- ✅ Chain initialization
- ✅ Report generator structure

### Full Test (With LLM API Calls)
```bash
python scripts/test_ai_agent_phase2.py --run-llm
```

**Warning**: This will make actual API calls to OpenAI/Hugging Face and may incur costs.

## Test Coverage

### Phase 2.1: Foundation Setup
- [x] Configuration validation
- [x] LLM provider initialization
- [x] Embedding model initialization
- [x] Vector store initialization
- [x] Vector store operations (add, search)

### Phase 2.2: RAG Implementation
- [x] Document loader initialization
- [x] Employee summary loading
- [x] Financial pattern loading
- [x] RAG engine initialization
- [x] Context retrieval
- [x] Context formatting
- [x] Query expansion
- [x] Knowledge base builder

### Phase 2.3: LLM Integration
- [x] RAG chain initialization
- [x] Structured output chain
- [x] Chain orchestrator
- [x] Report generator structure
- [x] Chain integration

## What Gets Tested

### ✅ Structure Tests (Always Run)
- Module imports
- Class initialization
- Method availability
- Configuration validation

### ⚠️ Functional Tests (Requires Database)
- Document loading from database
- Knowledge base building
- Vector store operations with real data

### 💰 LLM Tests (Requires --run-llm flag)
- Actual LLM API calls
- Report generation
- Structured output parsing

## Expected Output

### Successful Test Run
```
======================================================================
  AI Agent Phase 2 - Comprehensive Test Suite
======================================================================

======================================================================
  Phase 2.1: Foundation Setup Tests
======================================================================
✅ Configuration Validation
✅ Configuration Summary
✅ LLM Provider Initialization
✅ Embedding Model Initialization
✅ Vector Store Initialization
✅ Vector Store - Add Documents
✅ Vector Store - Similarity Search

======================================================================
  Phase 2.2: RAG Implementation Tests
======================================================================
✅ Document Loader Initialization
✅ Document Loader - Employee Summaries
✅ Document Loader - Financial Patterns
✅ RAG Engine Initialization
✅ RAG Engine - Context Retrieval
✅ RAG Engine - Context Formatting
✅ RAG Engine - Query Expansion
✅ Knowledge Base Builder Initialization

======================================================================
  Phase 2.3: LLM Integration Tests
======================================================================
✅ RAG Chain Initialization
✅ Structured Output Chain Initialization
✅ Chain Orchestrator Initialization
✅ Report Generator Initialization
✅ Report Generator - RAG Chain
✅ Report Generator - Employee Summary Chain
✅ Report Generator - Financial Report Chain

======================================================================
  Test Summary
======================================================================
Total Tests: 25
✅ Passed: 20
❌ Failed: 0
⚠️  Warnings: 5

Phase Status:
  Phase 2.1 (Foundation): PASS
  Phase 2.2 (RAG): PASS
  Phase 2.3 (LLM Integration): PASS

✅ All critical tests passed!
```

## Troubleshooting

### "Configuration Validation FAIL"
**Solution**: Check your `.env` file:
- `OPENAI_API_KEY` or `HUGGINGFACE_API_KEY` must be set
- `AI_PROVIDER` must be "openai" or "huggingface"

### "Vector Store FAIL"
**Solution**:
- Check `VECTOR_STORE_PATH` exists and is writable
- For cloud mode, verify `CHROMA_CLOUD_API_KEY` is set

### "Database not configured"
**Solution**: 
- Set `DATABASE_URL` in your `.env` file
- This is expected if you haven't set up the database yet
- Tests will skip database-dependent tests

### "No documents found"
**Solution**:
- This is normal if your database is empty
- Run `python scripts/build_knowledge_base.py` to populate
- Or add sample data to your database

### "LLM API Error"
**Solution**:
- Check your API key is valid
- Verify you have API credits/quota
- Check network connection
- Review error message for specific issue

## Manual Testing

### Test Vector Store
```python
from app.ai_agent.vector_store import get_vector_store
from langchain.schema import Document

store = get_vector_store()
doc = Document(page_content="Test", metadata={"test": True})
store.add_documents([doc])
results = store.similarity_search("test", k=1)
print(results)
```

### Test RAG Engine
```python
from app.ai_agent.rag_engine import get_rag_engine

rag = get_rag_engine()
docs = rag.retrieve_context("employee summary", k=3)
context = rag.format_context(docs)
print(context)
```

### Test Knowledge Base
```python
from app.ai_agent.knowledge_base_builder import KnowledgeBaseBuilder
from app.models.schema import get_engine, get_session

engine = get_engine(DATABASE_URL)
session = get_session(engine)
builder = KnowledgeBaseBuilder(session)
result = builder.build_knowledge_base(employee_limit=5)
print(result)
```

### Test Report Generation (Requires API)
```python
from app.ai_agent.agent import get_ai_agent
from app.models.schema import get_engine, get_session

engine = get_engine(DATABASE_URL)
session = get_session(engine)
agent = get_ai_agent(session)

result = agent.generate_summary(
    query_type="employee_summary",
    employee_id=1
)
print(result)
```

## Next Steps After Testing

1. **If all tests pass**: You're ready to use the AI agent!
2. **If warnings appear**: Review them - they're usually non-critical
3. **If tests fail**: Fix the issues before proceeding
4. **Build knowledge base**: Run `python scripts/build_knowledge_base.py`
5. **Test with real data**: Use `--run-llm` flag to test actual generation

---

**Note**: The test script is designed to be safe - it won't make expensive API calls unless you explicitly use the `--run-llm` flag.
