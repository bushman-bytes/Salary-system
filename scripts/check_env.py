"""Quick script to check environment variables are loaded correctly."""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.ai_agent.config import (
    validate_config,
    get_config_summary,
    OPENAI_API_KEY,
    AI_PROVIDER,
    CHROMA_CLOUD_MODE,
    CHROMA_CLOUD_API_KEY,
)

print("=" * 60)
print("Environment Configuration Check")
print("=" * 60)
print()

# Check validation
errors = validate_config()
if errors["errors"]:
    print("❌ Configuration Errors:")
    for error in errors["errors"]:
        print(f"   - {error}")
    print()
else:
    print("✅ Configuration is valid!")
    print()

# Show config summary
config = get_config_summary()
print("Configuration Summary:")
print(f"  AI Provider: {config['ai_provider']}")
print(f"  OpenAI API Key Set: {config['openai_api_key_set']}")
print(f"  HuggingFace API Key Set: {config['huggingface_api_key_set']}")
print(f"  Chroma Cloud Mode: {config['chroma_cloud_mode']}")
print(f"  Chroma Cloud API Key Set: {config.get('chroma_cloud_api_key_set', 'N/A')}")
print()

# Show raw values (first/last few chars for security)
if OPENAI_API_KEY:
    masked = OPENAI_API_KEY[:10] + "..." + OPENAI_API_KEY[-10:] if len(OPENAI_API_KEY) > 20 else "***"
    print(f"  OPENAI_API_KEY: {masked} (length: {len(OPENAI_API_KEY)})")
else:
    print("  OPENAI_API_KEY: NOT SET")

if CHROMA_CLOUD_API_KEY:
    masked = CHROMA_CLOUD_API_KEY[:10] + "..." + CHROMA_CLOUD_API_KEY[-10:] if len(CHROMA_CLOUD_API_KEY) > 20 else "***"
    print(f"  CHROMA_CLOUD_API_KEY: {masked} (length: {len(CHROMA_CLOUD_API_KEY)})")
else:
    print("  CHROMA_CLOUD_API_KEY: NOT SET")

print()
print("=" * 60)
