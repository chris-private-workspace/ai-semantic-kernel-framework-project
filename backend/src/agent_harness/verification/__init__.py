"""Category 10: Verification Loops.

See README.md for design notes.

Sprint 54.1 (US-1) ships RulesBasedVerifier + VerifierRegistry foundation.
LLMJudgeVerifier ships in US-2; AgentLoop self-correction integration in US-3.
"""

from agent_harness.verification._abc import Verifier
from agent_harness.verification._trace import build_memory_block, build_trace_block
from agent_harness.verification.cat9_fallback import LLMJudgeFallbackGuardrail
from agent_harness.verification.cat9_mutator import LLMVerifyMutateGuardrail
from agent_harness.verification.llm_judge import LLMJudgeVerifier
from agent_harness.verification.persistence import persist_verification_event
from agent_harness.verification.registry import VerifierRegistry
from agent_harness.verification.rules_based import RulesBasedVerifier
from agent_harness.verification.templates import load_template
from agent_harness.verification.tools import make_verify_tool
from agent_harness.verification.types import (
    FormatRule,
    RegexRule,
    Rule,
    SchemaRule,
)

__all__ = [
    "FormatRule",
    "build_memory_block",
    "build_trace_block",
    "LLMJudgeFallbackGuardrail",
    "LLMJudgeVerifier",
    "LLMVerifyMutateGuardrail",
    "RegexRule",
    "Rule",
    "RulesBasedVerifier",
    "SchemaRule",
    "Verifier",
    "VerifierRegistry",
    "load_template",
    "make_verify_tool",
    "persist_verification_event",
]
