# =============================================================================
# IPA Platform - Hybrid Architecture Examples
# =============================================================================
# Phase 13-14: Hybrid MAF + Claude SDK Integration
#
# This file contains practical examples for using the hybrid architecture.
# These examples demonstrate common patterns and best practices.
#
# Run examples:
#   python -m docs.guides.examples.hybrid-examples
# =============================================================================

"""
Hybrid Architecture Usage Examples

This module provides practical code examples for:
1. Basic hybrid execution
2. Mode switching
3. Checkpoint management
4. Risk assessment integration
5. Error handling patterns
"""

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, Optional
import uuid

# =============================================================================
# Example 1: Basic Hybrid Execution
# =============================================================================


async def example_basic_execution():
    """
    Basic hybrid execution with automatic mode routing.

    The orchestrator automatically detects whether the input
    should be processed as a workflow or chat interaction.
    """
    from src.integrations.hybrid.orchestrator_v2 import (
        create_orchestrator_v2,
        OrchestratorConfig,
        ExecutionMode,
    )

    # Create orchestrator with default config
    config = OrchestratorConfig(
        default_mode=ExecutionMode.HYBRID_MODE,
        auto_switch_enabled=True,
    )
    orchestrator = create_orchestrator_v2(config)

    # Execute with automatic routing
    # This input will likely route to WORKFLOW_MODE
    result = await orchestrator.execute(
        input_text="Process invoice #INV-2026-001 for approval",
        session_id=f"session-{uuid.uuid4().hex[:8]}",
    )

    print(f"Execution Mode: {result.execution_mode}")
    print(f"Output: {result.output}")
    print(f"Checkpoint ID: {result.checkpoint_id}")

    return result


# =============================================================================
# Example 2: Forced Mode Execution
# =============================================================================


async def example_forced_mode():
    """
    Execute with explicitly forced mode.

    Use force_mode when you know the desired execution path.
    """
    from src.integrations.hybrid.orchestrator_v2 import (
        create_orchestrator_v2,
        OrchestratorConfig,
        ExecutionMode,
    )

    orchestrator = create_orchestrator_v2()
    session_id = f"session-{uuid.uuid4().hex[:8]}"

    # Force WORKFLOW_MODE for structured processing
    workflow_result = await orchestrator.execute(
        input_text="Create quarterly report",
        session_id=session_id,
        force_mode=ExecutionMode.WORKFLOW_MODE,
    )
    print(f"Workflow result: {workflow_result.execution_mode}")

    # Force CHAT_MODE for conversational interaction
    chat_result = await orchestrator.execute(
        input_text="What information is in the quarterly report?",
        session_id=session_id,
        force_mode=ExecutionMode.CHAT_MODE,
    )
    print(f"Chat result: {chat_result.execution_mode}")

    return workflow_result, chat_result


# =============================================================================
# Example 3: Checkpoint Management
# =============================================================================


async def example_checkpoint_management():
    """
    Checkpoint creation, restoration, and management.

    Demonstrates how to create manual checkpoints and restore
    from them when needed.
    """
    from src.integrations.hybrid.checkpoint.models import (
        HybridCheckpoint,
        MAFCheckpointState,
        ClaudeCheckpointState,
        CheckpointType,
    )
    from src.integrations.hybrid.checkpoint.storage import (
        StorageConfig,
        StorageBackend,
    )
    from src.integrations.hybrid.checkpoint.backends.memory import (
        MemoryCheckpointStorage,
    )

    # Create in-memory storage for demo
    config = StorageConfig(
        backend=StorageBackend.MEMORY,
        ttl_seconds=3600,
        enable_compression=True,
    )
    storage = MemoryCheckpointStorage(config)

    # Create checkpoint with both MAF and Claude states
    checkpoint = HybridCheckpoint(
        checkpoint_id=str(uuid.uuid4()),
        session_id="demo-session",
        execution_mode="WORKFLOW_MODE",
        checkpoint_type=CheckpointType.MANUAL,
        maf_state=MAFCheckpointState(
            workflow_id="wf-demo-001",
            workflow_name="Demo Workflow",
            current_step=2,
            total_steps=5,
            variables={"input": "test data"},
        ),
        claude_state=ClaudeCheckpointState(
            session_id="demo-session",
            conversation_history=[
                {"role": "user", "content": "Start the demo"},
                {"role": "assistant", "content": "Demo started!"},
            ],
            context_variables={"demo_mode": True},
        ),
        metadata={"created_by": "example_script"},
    )

    # Save checkpoint
    checkpoint_id = await storage.save(checkpoint)
    print(f"Saved checkpoint: {checkpoint_id}")

    # Load checkpoint
    loaded = await storage.load(checkpoint_id)
    print(f"Loaded checkpoint - Step: {loaded.maf_state.current_step}")

    # Restore checkpoint
    result = await storage.restore(checkpoint_id)
    print(f"Restore success: {result.success}")
    print(f"Restored MAF: {result.restored_maf}")
    print(f"Restored Claude: {result.restored_claude}")

    # Query checkpoints
    from src.integrations.hybrid.checkpoint.storage import CheckpointQuery

    query = CheckpointQuery(
        session_id="demo-session",
        checkpoint_type=CheckpointType.MANUAL,
    )
    checkpoints = await storage.query(query)
    print(f"Found {len(checkpoints)} checkpoints")

    return checkpoint_id


# =============================================================================
# Example 4: Risk Assessment
# =============================================================================


async def example_risk_assessment():
    """
    Risk assessment for operations.

    Demonstrates how to evaluate operation risk and use it
    for HITL (Human-in-the-Loop) decisions.
    """
    from src.integrations.hybrid.risk.engine import (
        RiskAssessmentEngine,
        create_engine,
    )
    from src.integrations.hybrid.risk.models import (
        OperationContext,
        RiskConfig,
        RiskLevel,
    )

    # Create risk engine with custom config
    config = RiskConfig(
        high_risk_threshold=0.6,
        critical_risk_threshold=0.85,
        operation_weight=0.3,
        data_weight=0.25,
        environment_weight=0.2,
        history_weight=0.15,
        pattern_weight=0.1,
    )
    engine = create_engine(config=config)

    # Assess a read operation (low risk)
    read_context = OperationContext(
        tool_name="Read",
        command="read file.txt",
        target_path="/data/reports/file.txt",
        environment="development",
        session_id="demo-session",
    )
    read_assessment = engine.assess(read_context)
    print(f"Read operation risk: {read_assessment.overall_level.value}")
    print(f"  Score: {read_assessment.overall_score:.3f}")
    print(f"  Requires approval: {read_assessment.requires_approval}")

    # Assess a destructive operation (high risk)
    delete_context = OperationContext(
        tool_name="Bash",
        command="rm -rf /tmp/data",
        target_path="/tmp/data",
        environment="production",
        session_id="demo-session",
    )
    delete_assessment = engine.assess(delete_context)
    print(f"\nDelete operation risk: {delete_assessment.overall_level.value}")
    print(f"  Score: {delete_assessment.overall_score:.3f}")
    print(f"  Requires approval: {delete_assessment.requires_approval}")
    if delete_assessment.approval_reason:
        print(f"  Reason: {delete_assessment.approval_reason}")

    # Print risk factors
    print("\nRisk factors:")
    for factor in delete_assessment.factors:
        print(f"  - {factor.factor_type.value}: {factor.description}")
        print(f"    Score: {factor.score:.3f}, Weight: {factor.weight:.3f}")

    return read_assessment, delete_assessment


# =============================================================================
# Example 5: Mode Switching
# =============================================================================


async def example_mode_switching():
    """
    Dynamic mode switching during execution.

    Demonstrates how to switch between WORKFLOW and CHAT modes
    while preserving context.
    """
    from src.integrations.hybrid.switching.switcher import (
        ModeSwitcher,
        SwitcherConfig,
        MigrationDirection,
    )
    from src.integrations.hybrid.orchestrator_v2 import ExecutionMode

    # Create mode switcher
    config = SwitcherConfig(
        enable_auto_detection=True,
        cooldown_seconds=5,
        max_switches_per_session=10,
    )
    switcher = ModeSwitcher(config)

    # Simulate current workflow state
    current_state = {
        "mode": ExecutionMode.WORKFLOW_MODE,
        "session_id": "demo-session",
        "workflow_step": 3,
        "variables": {"invoice_id": "INV-001"},
    }

    # Detect if switch is needed based on new input
    new_input = "Can you explain what happened in step 2?"

    # This would typically use the trigger detector
    trigger = await switcher.detect_trigger(
        current_state=current_state,
        new_input=new_input,
    )

    if trigger.should_switch:
        print(f"Switch triggered: {trigger.reason}")

        # Create checkpoint before switch
        checkpoint = await switcher.create_switch_checkpoint(current_state)
        print(f"Checkpoint created: {checkpoint.checkpoint_id}")

        # Migrate state
        new_state = await switcher.migrate_state(
            source_state=current_state,
            direction=MigrationDirection.WORKFLOW_TO_CHAT,
        )
        print(f"Migrated to: {new_state['mode']}")
    else:
        print("No switch needed, continuing in current mode")

    return switcher


# =============================================================================
# Example 6: Error Handling Pattern
# =============================================================================


async def example_error_handling():
    """
    Error handling patterns for hybrid operations.

    Demonstrates how to handle common errors and recover
    from failures using checkpoints.
    """
    from src.integrations.hybrid.orchestrator_v2 import (
        create_orchestrator_v2,
        HybridExecutionError,
        ModeDetectionError,
        StateMigrationError,
    )

    orchestrator = create_orchestrator_v2()
    session_id = f"session-{uuid.uuid4().hex[:8]}"

    async def execute_with_recovery(input_text: str) -> dict:
        """Execute with comprehensive error handling."""
        try:
            result = await orchestrator.execute(
                input_text=input_text,
                session_id=session_id,
            )
            return {"success": True, "result": result}

        except ModeDetectionError as e:
            # Fallback to default mode
            print(f"Mode detection failed: {e}")
            result = await orchestrator.execute(
                input_text=input_text,
                session_id=session_id,
                force_mode="CHAT_MODE",  # Fallback
            )
            return {"success": True, "result": result, "fallback": True}

        except StateMigrationError as e:
            # Recover from last checkpoint
            print(f"State migration failed: {e}")
            restored = await orchestrator.restore_from_checkpoint(session_id)
            if restored:
                result = await orchestrator.resume_execution(restored)
                return {"success": True, "result": result, "recovered": True}
            return {"success": False, "error": str(e)}

        except HybridExecutionError as e:
            # Log and re-raise
            print(f"Execution failed: {e}")
            return {"success": False, "error": str(e)}

        except Exception as e:
            # Unexpected error
            print(f"Unexpected error: {e}")
            return {"success": False, "error": str(e), "unexpected": True}

    # Test the pattern
    result = await execute_with_recovery("Test input for error handling")
    print(f"Execution result: {result}")

    return result


# =============================================================================
# Example 7: Full Workflow Example
# =============================================================================


async def example_full_workflow():
    """
    Complete workflow demonstrating all features.

    This example shows a realistic scenario combining:
    - Automatic mode routing
    - Risk assessment
    - Checkpoint management
    - Error handling
    """
    from src.integrations.hybrid.orchestrator_v2 import (
        create_orchestrator_v2,
        OrchestratorConfig,
        ExecutionMode,
    )
    from src.integrations.hybrid.risk.engine import create_engine as create_risk_engine
    from src.integrations.hybrid.risk.models import RiskConfig, RiskLevel
    from src.integrations.hybrid.checkpoint.backends.memory import MemoryCheckpointStorage
    from src.integrations.hybrid.checkpoint.storage import StorageConfig, StorageBackend

    # Setup components
    print("=" * 60)
    print("Full Workflow Example")
    print("=" * 60)

    # 1. Initialize orchestrator with risk engine
    risk_config = RiskConfig(high_risk_threshold=0.6)
    risk_engine = create_risk_engine(config=risk_config)

    storage_config = StorageConfig(backend=StorageBackend.MEMORY)
    checkpoint_storage = MemoryCheckpointStorage(storage_config)

    orchestrator_config = OrchestratorConfig(
        default_mode=ExecutionMode.HYBRID_MODE,
        auto_switch_enabled=True,
        require_approval_for_high_risk=True,
    )
    orchestrator = create_orchestrator_v2(
        config=orchestrator_config,
        risk_engine=risk_engine,
        checkpoint_storage=checkpoint_storage,
    )

    session_id = f"workflow-{uuid.uuid4().hex[:8]}"
    print(f"\nSession: {session_id}")

    # 2. Start workflow
    print("\n--- Step 1: Start Invoice Processing ---")
    result1 = await orchestrator.execute(
        input_text="Process invoice #INV-2026-001 for $5,000",
        session_id=session_id,
    )
    print(f"Mode: {result1.execution_mode}")
    print(f"Output: {result1.output.get('message', 'N/A')}")

    # 3. User asks a question (mode may switch to CHAT)
    print("\n--- Step 2: User Question ---")
    result2 = await orchestrator.execute(
        input_text="What is the approval threshold for this amount?",
        session_id=session_id,
    )
    print(f"Mode: {result2.execution_mode}")
    print(f"Output: {result2.output.get('message', 'N/A')}")

    # 4. Continue with approval (back to WORKFLOW)
    print("\n--- Step 3: Submit for Approval ---")
    result3 = await orchestrator.execute(
        input_text="Submit the invoice for manager approval",
        session_id=session_id,
    )
    print(f"Mode: {result3.execution_mode}")
    print(f"Requires Approval: {result3.requires_approval}")
    if result3.requires_approval:
        print(f"Approval Reason: {result3.approval_reason}")

    # 5. Check session state
    print("\n--- Session Summary ---")
    stats = await checkpoint_storage.get_stats()
    print(f"Total checkpoints: {stats.total_checkpoints}")
    print(f"Active checkpoints: {stats.active_checkpoints}")

    print("\n" + "=" * 60)
    print("Workflow Complete")
    print("=" * 60)

    return {
        "session_id": session_id,
        "steps_completed": 3,
        "final_mode": result3.execution_mode,
    }


# =============================================================================
# Run Examples
# =============================================================================


async def run_all_examples():
    """Run all examples."""
    print("\n" + "=" * 60)
    print("IPA Platform - Hybrid Architecture Examples")
    print("=" * 60)

    examples = [
        ("Basic Execution", example_basic_execution),
        ("Forced Mode", example_forced_mode),
        ("Checkpoint Management", example_checkpoint_management),
        ("Risk Assessment", example_risk_assessment),
        ("Mode Switching", example_mode_switching),
        ("Error Handling", example_error_handling),
        ("Full Workflow", example_full_workflow),
    ]

    for name, func in examples:
        print(f"\n{'='*60}")
        print(f"Example: {name}")
        print("=" * 60)
        try:
            await func()
        except Exception as e:
            print(f"Example failed: {e}")


if __name__ == "__main__":
    # Note: In production, use proper async event loop
    # This is simplified for demonstration
    print("Run examples with: python -m asyncio docs/guides/examples/hybrid-examples.py")
    print("Or import and run individual examples.")

    # For demonstration, just show that examples are available
    print("\nAvailable examples:")
    print("  1. example_basic_execution()")
    print("  2. example_forced_mode()")
    print("  3. example_checkpoint_management()")
    print("  4. example_risk_assessment()")
    print("  5. example_mode_switching()")
    print("  6. example_error_handling()")
    print("  7. example_full_workflow()")
