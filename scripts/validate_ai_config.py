"""
Script to validate AI Agent configuration.

This script checks if all required environment variables are set
and if the AI agent can be initialized correctly.
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.ai_agent.config import validate_config, get_config_summary


def main():
    """Validate AI agent configuration."""
    print("=" * 60)
    print("AI Agent Configuration Validation")
    print("=" * 60)
    print()
    
    # Validate configuration
    print("Checking configuration...")
    errors = validate_config()
    
    if errors["errors"]:
        print("❌ Configuration errors found:")
        for error in errors["errors"]:
            print(f"   - {error}")
        print()
        print("Please fix these errors before proceeding.")
        return 1
    else:
        print("✅ Configuration is valid!")
        print()
    
    # Display configuration summary
    print("Current Configuration:")
    print("-" * 60)
    config = get_config_summary()
    for key, value in config.items():
        # Mask sensitive information
        if "key" in key.lower():
            value = "***SET***" if value else "❌ NOT SET"
        print(f"  {key}: {value}")
    print()
    
    # Test imports
    print("Testing imports...")
    try:
        from app.ai_agent.llm_provider import get_llm, get_embedding_model
        from app.ai_agent.vector_store import get_vector_store
        from app.ai_agent.rag_engine import get_rag_engine
        print("✅ All imports successful!")
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   Make sure all dependencies are installed:")
        print("   pip install -r requirements.txt")
        return 1
    
    print()
    print("=" * 60)
    print("✅ AI Agent configuration is ready!")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    exit(main())
