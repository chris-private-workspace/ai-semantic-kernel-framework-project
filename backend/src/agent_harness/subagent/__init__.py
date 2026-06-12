"""Category 11: Subagent Orchestration (4 modes, no worktree). See README.md.

Sprint 54.2 US-1 adds DefaultSubagentDispatcher + BudgetEnforcer +
BudgetExceededError. Fork / Teammate / AsTool mode executors + Mailbox.
HANDOFF is loop-intercepted (Sprint 57.107 B3): make_handoff_spec provides
the spec-only trigger tool; the platform layer boots the child session.
"""

from agent_harness.subagent._abc import SubagentDispatcher
from agent_harness.subagent.budget import BudgetEnforcer
from agent_harness.subagent.dispatcher import DefaultSubagentDispatcher
from agent_harness.subagent.exceptions import (
    BudgetExceededError,
    SubagentLaunchError,
)
from agent_harness.subagent.mailbox import MailboxStore
from agent_harness.subagent.modes.as_tool import AsToolWrapper
from agent_harness.subagent.modes.fork import ForkExecutor
from agent_harness.subagent.modes.teammate import TeammateExecutor
from agent_harness.subagent.tools import (
    make_handoff_spec,
    make_send_to_parent_tool,
    make_task_spawn_tool,
)

__all__ = [
    "SubagentDispatcher",
    "DefaultSubagentDispatcher",
    "BudgetEnforcer",
    "BudgetExceededError",
    "SubagentLaunchError",
    "MailboxStore",
    "ForkExecutor",
    "AsToolWrapper",
    "TeammateExecutor",
    "make_task_spawn_tool",
    "make_handoff_spec",
    "make_send_to_parent_tool",
]
