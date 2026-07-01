"""
File: backend/src/agent_harness/verification/llm_judge.py
Purpose: LLMJudgeVerifier — independent LLM call to judge LLM output. Fail-closed.
Category: 範疇 10 (Verification Loops)
Scope: Sprint 54.1 US-2; closes AD-Cat9-1

Description:
    Wraps a ChatClient (LLM-provider-neutral) to spawn a judge LLM call that
    evaluates the candidate output against a judge template. The template
    contains an {output} placeholder; the judge returns JSON which is parsed
    into a VerificationResult.

    **Fail-closed semantics**: any error path (chat client raises, response is
    not valid JSON, missing required keys) returns `passed=False` with the
    error captured in `reason`. This is the spec-mandated behavior (per
    01-eleven-categories-spec.md §範疇 10): a verifier that errors out must
    NOT let the loop proceed as if verification passed.

    **LLM Provider Neutrality**: imports only ChatClient ABC + neutral types
    from agent_harness._contracts. Never imports openai/anthropic directly.
    CI lint enforced (existing leak check covers this module).

Owner: 01-eleven-categories-spec.md §範疇 10
Single-source: 17.md §2.1 (Verifier ABC) / §1.1 (VerificationResult)

Created: 2026-05-04 (Sprint 54.1 Day 2)
Last Modified: 2026-07-01

Modification History:
    - 2026-07-01: Sprint 57.153 — memory-aware {memory} judge grounding block
    - 2026-06-13: Sprint 57.111 A3 — trace-aware {trace} prompt + optional judge temperature
    - 2026-06-05: Sprint 57.82 — capture response.usage + model into result (B-8 cost-ledger)
    - 2026-05-04: AD-Cat10-Obs-1 — accept optional Tracer (Sprint 54.2 US-5)
    - 2026-05-04: Initial (Sprint 54.1 US-2) — closes AD-Cat9-1 (LLM-judge fallback for detectors)
"""

from __future__ import annotations

import json
from dataclasses import replace
from typing import Any

from adapters._base.chat_client import ChatClient
from agent_harness._contracts import (
    LoopState,
    Message,
    TraceContext,
    VerificationResult,
)
from agent_harness._contracts.chat import ChatRequest
from agent_harness.observability import Tracer
from agent_harness.verification._abc import Verifier
from agent_harness.verification._obs import verification_span
from agent_harness.verification._trace import build_trace_block
from agent_harness.verification.templates import load_template


class LLMJudgeVerifier(Verifier):
    """Verify LLM output via an independent LLM judge call. Fail-closed."""

    def __init__(
        self,
        *,
        chat_client: ChatClient,
        judge_template: str,
        name: str = "llm_judge",
        tracer: Tracer | None = None,
        temperature: float = 1.0,
    ) -> None:
        """
        Args:
            chat_client: ChatClient ABC (LLM-provider-neutral). Tests pass MockChatClient.
            judge_template: Either a template name (e.g. "factual_consistency") or a raw
                template string. Names are loaded via `load_template()`. Raw strings must
                contain a literal `{output}` placeholder; an optional `{trace}` placeholder
                receives the A3 trace block; an optional `{memory}` placeholder (Sprint
                57.153) receives the injected-memory grounding block.
            name: Verifier display name (used in VerificationResult.verifier_name).
            temperature: judge sampling temperature (default 1.0 = pre-A3 behavior). The
                cheap-judge accuracy benchmark (Sprint 57.111) constructs judges at 0.0 for
                a stable accuracy number; production verification keeps the default.
        """
        self._chat = chat_client
        self._template_arg = judge_template
        self._name = name
        self._tracer = tracer
        self._temperature = temperature

    async def verify(
        self,
        *,
        output: str,
        state: LoopState | None = None,
        trace_context: TraceContext | None = None,
    ) -> VerificationResult:
        async with verification_span(self._tracer, self._name):
            try:
                prompt = self._build_prompt(output, state)
                request = ChatRequest(
                    messages=[Message(role="user", content=prompt)],
                    temperature=self._temperature,
                )
                response = await self._chat.chat(request, trace_context=trace_context)
                result = self._parse_response(response.content)
                # Sprint 57.82 (B-8 leg-1): attach judge token usage + model so the
                # correction-loop wrapper can bubble it to LoopCompleted for cost-ledger
                # / quota accounting. Even a malformed-response result carries the tokens
                # — the LLM call was made and is chargeable. The fail-closed except path
                # below keeps 0 (the call raised / may not have completed).
                usage = response.usage
                return replace(
                    result,
                    input_tokens=usage.prompt_tokens if usage else 0,
                    output_tokens=usage.completion_tokens if usage else 0,
                    model=response.model or None,
                )
            except Exception as e:  # noqa: BLE001 — fail-closed: ALL errors → passed=False
                return VerificationResult(
                    passed=False,
                    verifier_name=self._name,
                    verifier_type="llm_judge",
                    reason=f"judge_error: {type(e).__name__}: {e}",
                )

    def _build_prompt(self, output: str, state: LoopState | None) -> str:
        """Resolve template (name or raw) and substitute {output} (+ optional {trace}/{memory}).

        {trace} (Sprint 57.111 A3): when `state` carries a loop trace, substitute the
        recent turns + tool errors so the judge critiques trace-aware.

        {memory} (Sprint 57.153, AD-Verification-Judge-Memory-Inject-Blind): when `state`
        carries `transient.injected_memory`, substitute the memory injected into THIS turn's
        prompt so the judge does NOT false-positive-reject a memory-grounded recall as
        fabrication (the injected memory lives in the system prompt, never in the trace).

        Absent state OR a template without a `{trace}`/`{memory}` placeholder → each
        substitution is a no-op (an empty block; `.replace` on a string with no placeholder
        is byte-identical to the prior prompt). Only output_quality.txt + key_condition.txt
        carry `{memory}`; the Cat 9 fallback templates are `{output}`-only.
        """
        if "{output}" in self._template_arg:
            # Raw template string
            template_text = self._template_arg
        else:
            # Template name → load from templates/
            template_text = load_template(self._template_arg)
        trace_block = build_trace_block(state.transient.messages) if state is not None else ""
        memory_block = (state.transient.injected_memory or "") if state is not None else ""
        return (
            template_text.replace("{output}", output)
            .replace("{trace}", trace_block)
            .replace("{memory}", memory_block)
        )

    def _parse_response(self, content: str | list[Any]) -> VerificationResult:
        """Parse judge JSON response into VerificationResult. Fail-closed on errors."""
        # ChatResponse.content can be str or list[ContentBlock]; we expect str for judge
        if not isinstance(content, str):
            return VerificationResult(
                passed=False,
                verifier_name=self._name,
                verifier_type="llm_judge",
                reason=(
                    "malformed_judge_response: expected str content, "
                    f"got {type(content).__name__}"
                ),
            )

        try:
            data = json.loads(content)
        except json.JSONDecodeError as e:
            return VerificationResult(
                passed=False,
                verifier_name=self._name,
                verifier_type="llm_judge",
                reason=f"malformed_judge_response: not valid JSON: {e}",
            )

        if not isinstance(data, dict) or "passed" not in data:
            return VerificationResult(
                passed=False,
                verifier_name=self._name,
                verifier_type="llm_judge",
                reason="malformed_judge_response: missing 'passed' key in JSON object",
            )

        score_raw = data.get("score")
        score: float | None
        if isinstance(score_raw, (int, float)):
            score = float(score_raw)
        else:
            score = None

        return VerificationResult(
            passed=bool(data["passed"]),
            verifier_name=self._name,
            verifier_type="llm_judge",
            score=score,
            reason=data.get("reason"),
            suggested_correction=data.get("suggested_correction"),
        )
