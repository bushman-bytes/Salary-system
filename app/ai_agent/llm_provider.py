"""
LLM Provider Abstraction Module

This module provides a unified interface for different LLM providers
(OpenAI and Hugging Face) to allow easy switching between providers.
"""

from typing import Optional, Literal, List, Any
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_openai import ChatOpenAI

# Try to import Hugging Face InferenceClient (direct API)
try:
    from huggingface_hub import InferenceClient
    INFERENCE_CLIENT_AVAILABLE = True
except ImportError:
    INFERENCE_CLIENT_AVAILABLE = False
    InferenceClient = None

# Try to import Hugging Face chat models (newer approach)
try:
    from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
except ImportError:
    # Fallback to older imports
    try:
        from langchain_community.chat_models import ChatHuggingFace
        from langchain_community.llms import HuggingFaceEndpoint
    except ImportError:
        from langchain_community.llms import HuggingFaceEndpoint
        ChatHuggingFace = None

# Alternative: Use OpenAI-compatible client for Hugging Face
try:
    from openai import OpenAI as OpenAIClient
    OPENAI_CLIENT_AVAILABLE = True
except ImportError:
    OPENAI_CLIENT_AVAILABLE = False

# Import config after checking for InferenceClient
from app.ai_agent.config import (
    AI_PROVIDER,
    OPENAI_API_KEY,
    OPENAI_MODEL,
    HUGGINGFACE_API_KEY,
    HUGGINGFACE_MODEL,
    MAX_TOKENS,
    TEMPERATURE,
    TOP_P,
)


class HuggingFaceInferenceChatModel(BaseChatModel):
    """
    Custom LangChain chat model wrapper for Hugging Face InferenceClient.
    Uses the same format as the user's example: InferenceClient.chat_completion()
    """
    
    model: str
    api_key: str
    temperature: float = 0.7
    max_tokens: int = 2000
    top_p: float = 0.9
    
    def __init__(self, model: str, api_key: str, temperature: float = 0.7, 
                 max_tokens: int = 2000, top_p: float = 0.9, **kwargs):
        if InferenceClient is None:
            raise ImportError("huggingface_hub is required for InferenceClient. Install with: pip install huggingface_hub")
        super().__init__(**kwargs)
        self.model = model
        self.api_key = api_key
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.top_p = top_p
        self._client = InferenceClient(model=model, token=api_key)
    
    @property
    def _llm_type(self) -> str:
        return "huggingface_inference"
    
    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """Generate chat response using InferenceClient.chat_completion()"""
        # Convert LangChain messages to Hugging Face format
        hf_messages = []
        for msg in messages:
            if isinstance(msg, SystemMessage):
                hf_messages.append({"role": "system", "content": msg.content})
            elif isinstance(msg, HumanMessage):
                hf_messages.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                hf_messages.append({"role": "assistant", "content": msg.content})
        
        # Call chat_completion (same as user's example)
        try:
            response = self._client.chat_completion(
                model=self.model,
                messages=hf_messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                top_p=self.top_p,
            )
            
            # Extract content from response (matching user's example format)
            # User's example: response.choices[0].message["content"]
            if hasattr(response, 'choices'):
                # Object with choices attribute
                if len(response.choices) > 0:
                    message_obj = response.choices[0].message
                    if hasattr(message_obj, 'get'):
                        content = message_obj.get("content", "")
                    elif hasattr(message_obj, '__getitem__'):
                        content = message_obj["content"]
                    else:
                        content = str(message_obj)
                else:
                    content = ""
            elif isinstance(response, dict):
                # Dictionary response
                choices = response.get("choices", [])
                if choices and len(choices) > 0:
                    message = choices[0].get("message", {})
                    content = message.get("content", "")
                else:
                    content = ""
            else:
                # Fallback: try to convert to string
                content = str(response)
            
            # Create ChatResult
            message = AIMessage(content=content)
            generation = ChatGeneration(message=message)
            return ChatResult(generations=[generation])
            
        except Exception as e:
            raise ValueError(f"Hugging Face InferenceClient error: {e}")


def get_llm():
    """
    Get the configured LLM instance based on AI_PROVIDER setting.
    
    Returns:
        LLM instance (ChatOpenAI or HuggingFaceEndpoint)
        
    Raises:
        ValueError: If provider is not configured correctly
    """
    if AI_PROVIDER == "openai":
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is required when AI_PROVIDER is 'openai'")
        
        return ChatOpenAI(
            model=OPENAI_MODEL,
            api_key=OPENAI_API_KEY,
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
            top_p=TOP_P,
        )
    
    elif AI_PROVIDER == "huggingface":
        if not HUGGINGFACE_API_KEY:
            raise ValueError("HUGGINGFACE_API_KEY is required when AI_PROVIDER is 'huggingface'")
        
        # Method 1: Use InferenceClient directly (preferred - matches user's example)
        # This uses the same format as the user's Query_ChromaCloud.py example
        if INFERENCE_CLIENT_AVAILABLE and InferenceClient is not None:
            try:
                print(f"[LLM Provider] Attempting to use InferenceClient for {HUGGINGFACE_MODEL}")
                # Create our custom wrapper directly (it will create InferenceClient internally)
                llm_instance = HuggingFaceInferenceChatModel(
                    model=HUGGINGFACE_MODEL,
                    api_key=HUGGINGFACE_API_KEY,
                    temperature=TEMPERATURE,
                    max_tokens=MAX_TOKENS,
                    top_p=TOP_P,
                )
                # Verify it's properly initialized
                if hasattr(llm_instance, '_client') and llm_instance._client is not None:
                    print(f"[LLM Provider] ✅ Successfully using InferenceClient with model: {HUGGINGFACE_MODEL}")
                    print(f"[LLM Provider] LLM type: {type(llm_instance).__name__}")
                    return llm_instance
                else:
                    raise ValueError("InferenceClient not properly initialized in wrapper")
            except Exception as e:
                import warnings
                import traceback
                error_msg = f"InferenceClient initialization failed: {e}"
                print(f"[LLM Provider] ❌ {error_msg}")
                print(f"[LLM Provider] Full traceback:\n{traceback.format_exc()}")
                warnings.warn(
                    f"{error_msg}. Trying other methods...",
                    UserWarning
                )
                # Don't pass silently - log the error but continue to fallback
                pass
        
        # Method 2: Try using OpenAI-compatible endpoint (fallback)
        # NOTE: Some models like Mistral-7B-Instruct-v0.3 may not support OpenAI-compatible endpoint
        # Skip this for models that are known to not work with chat completion API
        skip_openai_compatible = "Mistral-7B-Instruct" in HUGGINGFACE_MODEL
        
        if OPENAI_CLIENT_AVAILABLE and not skip_openai_compatible:
            try:
                # Use ChatOpenAI with Hugging Face's OpenAI-compatible endpoint
                print(f"[LLM Provider] Trying OpenAI-compatible endpoint for {HUGGINGFACE_MODEL}")
                return ChatOpenAI(
                    model=HUGGINGFACE_MODEL,
                    base_url="https://router.huggingface.co/v1/",
                    api_key=HUGGINGFACE_API_KEY,
                    temperature=TEMPERATURE,
                    max_tokens=MAX_TOKENS,
                    top_p=TOP_P,
                )
            except Exception as e:
                # If OpenAI-compatible endpoint fails, continue to other methods
                import warnings
                print(f"[LLM Provider] OpenAI-compatible endpoint failed: {e}")
                warnings.warn(
                    f"OpenAI-compatible endpoint failed: {e}. Trying other methods...",
                    UserWarning
                )
                pass
        elif skip_openai_compatible:
            print(f"[LLM Provider] Skipping OpenAI-compatible endpoint for {HUGGINGFACE_MODEL} (not supported)")
        
        # Method 3: Try ChatHuggingFace (skip for Mistral models - they don't work well with this)
        # Skip ChatHuggingFace for models that are known to not work with it
        skip_chat_hf = "Mistral-7B-Instruct" in HUGGINGFACE_MODEL
        
        if ChatHuggingFace is not None and not skip_chat_hf:
            try:
                print(f"[LLM Provider] Trying ChatHuggingFace for {HUGGINGFACE_MODEL}")
                # Create HuggingFaceEndpoint first, then wrap with ChatHuggingFace
                endpoint = HuggingFaceEndpoint(
                    repo_id=HUGGINGFACE_MODEL,
                    task="text-generation",
                    huggingfacehub_api_token=HUGGINGFACE_API_KEY,
                    temperature=TEMPERATURE,
                    max_new_tokens=MAX_TOKENS,
                    top_p=TOP_P,
                )
                # Wrap endpoint with ChatHuggingFace for chat interface
                return ChatHuggingFace(llm=endpoint)
            except Exception as e:
                # Log error but continue to fallback
                import warnings
                print(f"[LLM Provider] ChatHuggingFace failed: {e}")
                warnings.warn(
                    f"ChatHuggingFace initialization failed: {e}. "
                    "Falling back to HuggingFaceEndpoint directly.",
                    UserWarning
                )
                # Continue to fallback options
                pass
        elif skip_chat_hf:
            print(f"[LLM Provider] Skipping ChatHuggingFace for {HUGGINGFACE_MODEL} (not compatible)")
        
        # Method 3: Fallback to HuggingFaceEndpoint directly (text generation)
        try:
            return HuggingFaceEndpoint(
                repo_id=HUGGINGFACE_MODEL,
                task="text-generation",
                huggingfacehub_api_token=HUGGINGFACE_API_KEY,
                temperature=TEMPERATURE,
                max_new_tokens=MAX_TOKENS,
                top_p=TOP_P,
            )
        except (TypeError, ValueError) as e:
            # Fallback to older endpoint_url format (using router endpoint)
            try:
                return HuggingFaceEndpoint(
                    endpoint_url=f"https://router.huggingface.co/models/{HUGGINGFACE_MODEL}",
                    huggingfacehub_api_token=HUGGINGFACE_API_KEY,
                    temperature=TEMPERATURE,
                    max_new_tokens=MAX_TOKENS,
                    top_p=TOP_P,
                )
            except Exception as e2:
                raise ValueError(
                    f"Failed to initialize Hugging Face model '{HUGGINGFACE_MODEL}'. "
                    f"Tried multiple methods. Please check: "
                    f"1) Model is available on Hugging Face Hub, "
                    f"2) API key is valid, 3) Model supports Inference API. "
                    f"Errors: ChatHuggingFace={str(e)}, HuggingFaceEndpoint={str(e2)}"
                )
    
    else:
        raise ValueError(f"Unsupported AI_PROVIDER: {AI_PROVIDER}. Must be 'openai' or 'huggingface'")


def get_embedding_model():
    """
    Get the configured embedding model based on AI_PROVIDER setting.
    
    Returns:
        Embedding model instance
        
    Raises:
        ValueError: If provider is not configured correctly
    """
    from langchain_openai import OpenAIEmbeddings
    try:
        from langchain_huggingface import HuggingFaceEmbeddings
    except ImportError:
        # Fallback to deprecated import
        from langchain_community.embeddings import HuggingFaceEmbeddings
    from app.ai_agent.config import (
        OPENAI_EMBEDDING_MODEL,
        HUGGINGFACE_EMBEDDING_MODEL,
    )
    
    if AI_PROVIDER == "openai":
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is required when AI_PROVIDER is 'openai'")
        
        return OpenAIEmbeddings(
            model=OPENAI_EMBEDDING_MODEL,
            api_key=OPENAI_API_KEY,
        )
    
    elif AI_PROVIDER == "huggingface":
        return HuggingFaceEmbeddings(
            model_name=HUGGINGFACE_EMBEDDING_MODEL,
        )
    
    else:
        raise ValueError(f"Unsupported AI_PROVIDER: {AI_PROVIDER}. Must be 'openai' or 'huggingface'")
