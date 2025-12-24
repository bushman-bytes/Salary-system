# Troubleshooting ChromaDB Connection Issues

## Common Issues and Solutions

### Issue 1: "Permission denied" or "Authentication failed"

**Symptoms:**
- Error: "Failed to connect to ChromaDB Cloud: Permission denied"
- Error: "ChromaDB Cloud authentication failed"

**Solutions:**

#### Option A: Switch to Local Mode (Easiest for Testing)
In your `.env` file, change:
```env
CHROMA_CLOUD_MODE=local
```

This will use local file storage instead of cloud, which is:
- ✅ Free
- ✅ No API key needed
- ✅ Works offline
- ✅ Perfect for development

#### Option B: Fix Cloud Connection

1. **Verify API Key:**
   - Check `CHROMA_CLOUD_API_KEY` in `.env` has no quotes or spaces
   - Format: `CHROMA_CLOUD_API_KEY=ck-...` (no quotes, no spaces)

2. **Check API Key Validity:**
   - Log into ChromaDB Cloud dashboard
   - Verify the API key is active
   - Generate a new key if needed

3. **Verify Host:**
   - ChromaDB Cloud uses: `api.trychroma.com`
   - You can leave `CHROMA_CLOUD_HOST` empty (it defaults correctly)
   - Or set: `CHROMA_CLOUD_HOST=https://api.trychroma.com`

4. **Check Tenant and Database:**
   - Verify `CHROMA_CLOUD_TENANT` matches your account
   - Verify `CHROMA_CLOUD_DATABASE` name is correct
   - Database name should match exactly (case-sensitive)

### Issue 2: "No module named 'langchain.chains'"

**Solution:**
This is fixed! The code now uses `langchain_core` instead. Just install:
```bash
pip install langchain-core
```

### Issue 3: Environment Variables Not Loading

**Symptoms:**
- API keys show as "NOT SET"
- Configuration validation fails

**Solutions:**

1. **Check .env file location:**
   - Should be in: `app/config/.env`
   - Or create one in project root: `.env`

2. **Check .env file format:**
   ```env
   # ✅ CORRECT
   OPENAI_API_KEY=sk-proj-...
   
   # ❌ WRONG (has space and quotes)
   OPENAI_API_KEY= "sk-proj-..."
   OPENAI_API_KEY='sk-proj-...'
   ```

3. **Restart your application** after changing .env

## Quick Fix: Use Local Mode

If you're having cloud connection issues, switch to local mode:

1. Edit `app/config/.env`:
   ```env
   CHROMA_CLOUD_MODE=local
   ```

2. Remove or comment out cloud settings:
   ```env
   # CHROMA_CLOUD_API_KEY=...
   # CHROMA_CLOUD_TENANT=...
   ```

3. Run tests again:
   ```bash
   python scripts/test_ai_agent_phase2.py
   ```

Local mode will create `./vector_store/` directory automatically.

## Testing ChromaDB Connection

### Test Local Mode
```python
from app.ai_agent.vector_store import get_vector_store
from langchain_core.documents import Document

store = get_vector_store()
doc = Document(page_content="Test", metadata={"test": True})
store.add_documents([doc])
print("✅ Local ChromaDB works!")
```

### Test Cloud Mode
```python
from app.ai_agent.config import CHROMA_CLOUD_MODE, CHROMA_CLOUD_API_KEY
from app.ai_agent.vector_store import get_vector_store

print(f"Cloud mode: {CHROMA_CLOUD_MODE}")
print(f"API key set: {bool(CHROMA_CLOUD_API_KEY)}")

try:
    store = get_vector_store()
    print("✅ Cloud connection works!")
except Exception as e:
    print(f"❌ Cloud connection failed: {e}")
```

## Recommended Setup

### For Development
```env
CHROMA_CLOUD_MODE=local
VECTOR_STORE_PATH=./vector_store
```

### For Production
```env
CHROMA_CLOUD_MODE=cloud
CHROMA_CLOUD_API_KEY=your_key_here
CHROMA_CLOUD_TENANT=your_tenant_id
CHROMA_CLOUD_DATABASE=your_database_name
```

## Still Having Issues?

1. **Check ChromaDB Cloud Status:**
   - Visit ChromaDB Cloud dashboard
   - Verify your account is active
   - Check API key permissions

2. **Verify Network:**
   - Ensure you can reach `api.trychroma.com`
   - Check firewall/proxy settings

3. **Check Logs:**
   - Look for detailed error messages
   - The error will indicate if it's authentication, network, or configuration

4. **Use Local Mode:**
   - Switch to local for now
   - Fix cloud connection later
   - Local mode works perfectly for development

---

**Pro Tip**: Start with local mode to get everything working, then switch to cloud when ready for production!
