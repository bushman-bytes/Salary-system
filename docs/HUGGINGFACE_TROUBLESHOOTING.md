# Hugging Face Model Troubleshooting

## Common Issues

### 1. StopIteration Error

**Error**: `StopIteration` when calling Hugging Face model

**Cause**: The model is not available via Hugging Face Inference API or requires special access.

**Solution**: 
- Use a model that's publicly available via Inference API
- Current recommended model: `mistralai/Mistral-Small-Instruct-2409`
- Alternative models that work:
  - `mistralai/Mixtral-8x7B-Instruct-v0.1`
  - `Qwen/Qwen2.5-7B-Instruct`
  - `google/flan-t5-large` (smaller, faster)

### 2. Model Not Found

**Error**: Model not found or access denied

**Solution**:
1. Check model name is correct on Hugging Face Hub
2. Verify API key has access
3. Try a different publicly available model

### 3. Chat vs Text Generation

**Issue**: Some models work better with text generation than chat format

**Solution**: The system automatically handles both:
- Tries chat format first (ChatHuggingFace)
- Falls back to text generation if needed
- Converts messages to text when necessary

## Current Configuration

### Model Settings

In `app/config/.env`:
```env
AI_PROVIDER=huggingface
HUGGINGFACE_MODEL=mistralai/Mistral-Small-Instruct-2409
HUGGINGFACE_API_KEY=your_key_here
```

### Why Mistral?

- ✅ Publicly available via Inference API
- ✅ Supports chat format
- ✅ Good performance
- ✅ No special access required

## Testing

### Quick Test

```bash
python scripts/test_huggingface.py
```

### Test in Agent Dashboard

1. Start server: `python main.py`
2. Go to: `http://localhost:8000/agent-dashboard`
3. Try natural language query
4. Check for errors in server logs

## Alternative Models

If Mistral doesn't work, try these in `.env`:

```env
# Option 1: Qwen (good for instructions)
HUGGINGFACE_MODEL=Qwen/Qwen2.5-7B-Instruct

# Option 2: Mixtral (larger, more capable)
HUGGINGFACE_MODEL=mistralai/Mixtral-8x7B-Instruct-v0.1

# Option 3: Flan-T5 (smaller, faster)
HUGGINGFACE_MODEL=google/flan-t5-large
```

## Switching Back to OpenAI

If Hugging Face continues to have issues:

1. Change in `.env`:
   ```env
   AI_PROVIDER=openai
   ```

2. Restart application

3. System automatically uses OpenAI collection and model

## Error Messages

### "Failed to initialize Hugging Face model"

**Check**:
- API key is valid
- Model name is correct
- Model is available on Hugging Face Hub
- Internet connection is working

### "StopIteration" or "Provider not found"

**Solution**: Model not available via Inference API. Switch to a different model.

### "Rate limit exceeded"

**Solution**: 
- Wait a few minutes
- Check Hugging Face API usage limits
- Consider upgrading API tier

## Performance Notes

- **First request**: May be slow (cold start)
- **Subsequent requests**: Faster
- **Response time**: Generally slower than OpenAI
- **Cost**: Free tier available, but has limits

## Getting Help

1. Check Hugging Face model page: https://huggingface.co/models
2. Verify model supports Inference API
3. Check API key permissions
4. Review server logs for detailed errors
