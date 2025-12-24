# Quick Test Guide - Phase 2 AI Agent

## 🚀 Quick Start

### Step 1: Validate Configuration
```bash
python scripts/validate_ai_config.py
```

### Step 2: Run Comprehensive Tests (No API Costs)
```bash
python scripts/test_ai_agent_phase2.py
```

### Step 3: Build Knowledge Base (If Database is Ready)
```bash
python scripts/build_knowledge_base.py
```

### Step 4: Test with Real LLM (Optional - Costs Money)
```bash
python scripts/test_ai_agent_phase2.py --run-llm
```

## 📋 What Each Test Does

### `validate_ai_config.py`
- ✅ Checks environment variables
- ✅ Validates API keys
- ✅ Verifies configuration
- ✅ Tests imports

**Time**: < 1 second  
**Cost**: Free

### `test_ai_agent_phase2.py` (without --run-llm)
- ✅ Tests all module initialization
- ✅ Tests vector store operations
- ✅ Tests RAG engine
- ✅ Tests chain structure
- ⚠️ Skips actual LLM API calls

**Time**: 5-10 seconds  
**Cost**: Free

### `test_ai_agent_phase2.py --run-llm`
- ✅ Everything above PLUS
- ✅ Actual LLM API calls
- ✅ Report generation
- ✅ Structured output parsing

**Time**: 30-60 seconds  
**Cost**: ~$0.01-0.05 (depends on model)

### `build_knowledge_base.py`
- ✅ Extracts data from database
- ✅ Creates embeddings
- ✅ Stores in vector database
- ✅ Builds knowledge base

**Time**: 1-5 minutes (depends on data size)  
**Cost**: Free (local) or minimal (cloud)

## 🎯 Testing Checklist

Before testing, ensure:
- [ ] `.env` file exists with required keys
- [ ] `OPENAI_API_KEY` or `HUGGINGFACE_API_KEY` is set
- [ ] `DATABASE_URL` is set (for database tests)
- [ ] Dependencies installed: `pip install -r requirements.txt`

## 📊 Expected Results

### ✅ All Good
```
✅ All critical tests passed!
Phase 2.1 (Foundation): PASS
Phase 2.2 (RAG): PASS
Phase 2.3 (LLM Integration): PASS
```

### ⚠️ Warnings (Usually OK)
- "Database not configured" - Expected if DB not set up
- "No documents found" - Expected if DB is empty
- "No context retrieved" - Expected if KB not built yet

### ❌ Failures (Need Fixing)
- "Configuration Validation FAIL" - Check .env file
- "LLM Provider FAIL" - Check API key
- "Vector Store FAIL" - Check permissions/path

## 🔧 Common Issues

### Issue: "Module not found"
**Fix**: 
```bash
pip install -r requirements.txt
```

### Issue: "API key not set"
**Fix**: Add to `.env`:
```env
OPENAI_API_KEY=your_key_here
```

### Issue: "Vector store permission denied"
**Fix**:
```bash
mkdir -p ./vector_store
chmod 755 ./vector_store
```

### Issue: "Database connection failed"
**Fix**: Check `DATABASE_URL` in `.env` is correct

## 📝 Test Output Interpretation

### Phase 2.1 Tests
- **Configuration**: Should PASS
- **LLM Provider**: Should PASS
- **Vector Store**: Should PASS

### Phase 2.2 Tests
- **Document Loader**: May WARN if DB empty (OK)
- **RAG Engine**: Should PASS
- **Knowledge Base**: May WARN if DB empty (OK)

### Phase 2.3 Tests
- **Chains**: Should PASS
- **Orchestrator**: Should PASS
- **Report Generator**: Should PASS

## 🎓 Next Steps

1. **If tests pass**: You're ready! Build knowledge base and start using
2. **If warnings**: Review them, usually non-critical
3. **If failures**: Fix issues before proceeding
4. **After tests pass**: Move to Phase 2.4 or 2.5

---

**Pro Tip**: Run tests without `--run-llm` first to verify setup, then use `--run-llm` to test actual generation.
