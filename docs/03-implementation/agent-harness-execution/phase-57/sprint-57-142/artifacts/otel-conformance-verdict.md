# OTel GenAI Conformance — 2026-06-25T09:09:28

- mode: **real**
- spans: **3** · GenAI spans: **2** · conformant: **2**
- **conformance ratio: 100.00%**
- chat span carries usage tokens (latent bug FIXED): **YES**
- chat span carries gen_ai.response.finish_reasons: **YES**

## Per span

| span name | operation | conformant | usage | finish_reasons |
|-----------|-----------|------------|-------|----------------|
| `chat gpt-5.2` | chat | ✅ | ✅ | ✅ |
| `agent_loop.turn` | — | — | — | — |
| `invoke_agent` | invoke_agent | ✅ | — | — |
