# ChromaDB Cloud Setup Guide

## Quick Start

### Option 1: Local ChromaDB (Default - Recommended for Development)

```env
# In your .env file
CHROMA_CLOUD_MODE=local
VECTOR_STORE_PATH=./vector_store
CHROMA_COLLECTION_NAME=salary_management_kb
```

**No additional setup needed!** Just works out of the box.

### Option 2: ChromaDB Cloud (Recommended for Production)

#### Step 1: Get ChromaDB Cloud Account

1. Go to [ChromaDB Cloud](https://www.trychroma.com/)
2. Sign up for an account
3. Create a new project/tenant
4. Get your API key from the dashboard

#### Step 2: Configure Environment Variables

```env
# Enable cloud mode
CHROMA_CLOUD_MODE=cloud

# Your ChromaDB Cloud credentials
CHROMA_CLOUD_API_KEY=your_api_key_here
CHROMA_CLOUD_HOST=https://your-tenant.chromadb.cloud  # Optional, if custom host

# Collection settings
CHROMA_COLLECTION_NAME=salary_management_kb
CHROMA_CLOUD_DATABASE=default  # Optional, database name in cloud
```

#### Step 3: Test Connection

Run the validation script:
```bash
python scripts/validate_ai_config.py
```

## Environment Variables Reference

### Local Mode (Default)
```env
CHROMA_CLOUD_MODE=local
VECTOR_STORE_PATH=./vector_store
CHROMA_COLLECTION_NAME=salary_management_kb
```

### Cloud Mode
```env
CHROMA_CLOUD_MODE=cloud
CHROMA_CLOUD_API_KEY=your_api_key_here
CHROMA_CLOUD_HOST=https://your-tenant.chromadb.cloud  # Optional
CHROMA_COLLECTION_NAME=salary_management_kb
CHROMA_CLOUD_DATABASE=default  # Optional
CHROMA_CLOUD_TENANT=your_tenant_id  # Optional, if needed
```

## Switching Between Modes

You can easily switch between local and cloud by changing `CHROMA_CLOUD_MODE`:

```env
# Switch to cloud
CHROMA_CLOUD_MODE=cloud
CHROMA_CLOUD_API_KEY=your_key

# Switch back to local
CHROMA_CLOUD_MODE=local
```

**Note**: Data is not automatically migrated. You'll need to:
1. Export data from one mode
2. Import to the other mode
3. Or rebuild the knowledge base

## Troubleshooting

### Error: "CHROMA_CLOUD_API_KEY is required"
**Solution**: Make sure you've set `CHROMA_CLOUD_API_KEY` in your `.env` file when using cloud mode.

### Error: "Failed to connect to ChromaDB Cloud"
**Solutions**:
1. Check your API key is correct
2. Verify internet connection
3. Check if `CHROMA_CLOUD_HOST` is correct (if using custom host)
4. Verify your ChromaDB Cloud account is active

### Error: "chromadb package is required"
**Solution**: Install ChromaDB:
```bash
pip install chromadb
```

## Best Practices

1. **Development**: Use `local` mode - it's faster and free
2. **Staging**: Use `cloud` mode to test production setup
3. **Production**: Use `cloud` mode for reliability and scalability
4. **Backup**: Regularly export your vector store data
5. **Security**: Never commit API keys to version control

## Cost Considerations

- **Local**: Free (just server costs)
- **Cloud**: Pay-as-you-go, typically $0-50/month for small projects

## Migration Guide

### From Local to Cloud

1. Set up ChromaDB Cloud account
2. Configure cloud credentials in `.env`
3. Set `CHROMA_CLOUD_MODE=cloud`
4. Rebuild knowledge base (or export/import if ChromaDB supports it)

### From Cloud to Local

1. Set `CHROMA_CLOUD_MODE=local`
2. Ensure `VECTOR_STORE_PATH` is set
3. Rebuild knowledge base locally

---

**Recommendation**: Start with local for Phase 2, switch to cloud for production!
