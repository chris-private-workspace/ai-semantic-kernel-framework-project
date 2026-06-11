# Sprint 156 Checklist - U4: Graceful Shutdown Protocol

- [ ] Modify `agent_work_loop.py` run_parallel_team()
  - [ ] Send SHUTDOWN_REQUEST via shared.add_message to each agent
  - [ ] Emit shutdown_request SSE event
  - [ ] Poll for SHUTDOWN_ACK from each agent (10s timeout)
  - [ ] Force shutdown_event.set() after timeout
  - [ ] Cleanup: emit SWARM_WORKER_END for each agent

- [ ] Modify `agent_work_loop.py` _agent_work_loop()
  - [ ] Detect "SHUTDOWN_REQUEST" in inbox during Phase C polling
  - [ ] Complete current work (don't start new LLM call)
  - [ ] Send SHUTDOWN_ACK via shared.add_message
  - [ ] Break out of work loop

- [ ] Modify frontend
  - [ ] useOrchestratorSSE: handle shutdown events in activity log
  - [ ] AgentTeamTestPage: agent card "Shutting down..." state
