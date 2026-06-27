"""adapters._base — ChatClient ABC + neutral types. See README.md.

Single-source map:
- ChatClient: chat_client.py
- ModelProfile: model_profile.py
- ModelInfo / StreamEvent: types.py
- PricingInfo: pricing.py
- ProviderError / AdapterException: errors.py
- StopReason: re-exported from agent_harness._contracts.chat (per 17.md §1.1)
"""

from adapters._base.chat_client import ChatClient
from adapters._base.circuit_breaker_wrapper import CircuitBreakerWrapper
from adapters._base.embedding_client import EmbeddingClient
from adapters._base.errors import AdapterException, ProviderError
from adapters._base.model_profile import ModelProfile
from adapters._base.pricing import PricingInfo
from adapters._base.types import ModelInfo, StopReason, StreamEvent

__all__ = [
    "AdapterException",
    "ChatClient",
    "CircuitBreakerWrapper",
    "EmbeddingClient",
    "ModelInfo",
    "ModelProfile",
    "PricingInfo",
    "ProviderError",
    "StopReason",
    "StreamEvent",
]
