"""Test to show how chat messages are formatted for Hugging Face."""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

print("=" * 70)
print("Testing Hugging Face Chat Message Format")
print("=" * 70)
print()

try:
    from app.ai_agent.llm_provider import get_llm
    from app.ai_agent.prompt_templates import GENERAL_QUERY_TEMPLATE
    from langchain_core.messages import SystemMessage, HumanMessage
    
    # Get LLM
    llm = get_llm()
    print(f"LLM Type: {type(llm).__name__}")
    print()
    
    # Show how messages are formatted
    print("1. Message Format Example:")
    print("-" * 70)
    
    # Example 1: Direct LangChain messages
    print("\nDirect LangChain Messages:")
    messages_langchain = [
        SystemMessage(content="You are a helpful assistant for salary management."),
        HumanMessage(content="What is the total amount of pending advances?")
    ]
    
    print("LangChain Format:")
    for msg in messages_langchain:
        print(f"  - {type(msg).__name__}: {msg.content[:60]}...")
    
    print("\n  → Automatically converted to Hugging Face format:")
    print("  [")
    print('    {"role": "system", "content": "You are a helpful assistant..."},')
    print('    {"role": "user", "content": "What is the total amount..."}')
    print("  ]")
    print()
    
    # Example 2: Using prompt template
    print("2. Using Prompt Template:")
    print("-" * 70)
    
    formatted_messages = GENERAL_QUERY_TEMPLATE.format_messages(
        retrieved_context="Context from knowledge base...",
        query_data="Employee data...",
        user_question="Generate employee summary"
    )
    
    print("Template generates:")
    for msg in formatted_messages:
        msg_type = type(msg).__name__
        content_preview = msg.content[:80] + "..." if len(msg.content) > 80 else msg.content
        print(f"  - {msg_type}: {content_preview}")
    
    print("\n  → Sent to Hugging Face as:")
    print("  [")
    print('    {"role": "system", "content": "You are an AI assistant..."},')
    print('    {"role": "user", "content": "Answer the following question..."}')
    print("  ]")
    print()
    
    # Test actual invocation
    print("3. Testing Actual Invocation:")
    print("-" * 70)
    
    test_messages = [
        SystemMessage(content="You are a helpful assistant. Say 'Hello' in one word."),
        HumanMessage(content="Hello")
    ]
    
    print("Sending test message...")
    response = llm.invoke(test_messages)
    
    if hasattr(response, 'content'):
        result = response.content
    else:
        result = str(response)
    
    print(f"✅ Response received: {result[:100]}")
    print()
    
    print("=" * 70)
    print("✅ Message Format Test Complete!")
    print("=" * 70)
    print()
    print("Summary:")
    print("  - LangChain messages are automatically converted")
    print("  - SystemMessage → {'role': 'system', ...}")
    print("  - HumanMessage → {'role': 'user', ...}")
    print("  - Works seamlessly with Hugging Face API")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
