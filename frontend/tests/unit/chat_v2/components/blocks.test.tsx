/**
 * File: frontend/tests/unit/chat_v2/components/blocks.test.tsx
 * Purpose: Vitest render coverage for Sprint 57.21 4 block components + dispatcher.
 * Category: Frontend / tests / unit / chat_v2
 * Scope: Phase 57.21 Day 2 §2.2
 *
 * Created: 2026-05-17 (Sprint 57.21 Day 2 §2.2)
 *
 * Modification History:
 *   - 2026-05-17: Initial creation (Sprint 57.21 Day 2 §2.2)
 */

import { render, screen } from "@testing-library/react";
import { describe, expect, test } from "vitest";

import { BlockRender } from "@/features/chat_v2/components/blocks/Block";
import { SubagentForkBlock } from "@/features/chat_v2/components/blocks/SubagentForkBlock";
import { ThinkingBlock } from "@/features/chat_v2/components/blocks/ThinkingBlock";
import { ToolBlock } from "@/features/chat_v2/components/blocks/ToolBlock";
import { VerificationBlock } from "@/features/chat_v2/components/blocks/VerificationBlock";

describe("ThinkingBlock (mockup L200-207)", () => {
  test("renders thinking label + body text", () => {
    render(<ThinkingBlock block={{ type: "thinking", text: "Hmm, let me think." }} />);
    expect(screen.getByText("thinking")).toBeInTheDocument();
    expect(screen.getByText("Hmm, let me think.")).toBeInTheDocument();
  });
});

describe("ToolBlock (mockup L208-223)", () => {
  test("status=pending shows pending badge + dash duration", () => {
    render(
      <ToolBlock
        block={{
          type: "tool",
          toolCallId: "tc-1",
          name: "metrics.query",
          status: "pending",
          input: '{ "q": "test" }',
          output: null,
          durationMs: null,
          isError: false,
        }}
      />,
    );
    expect(screen.getByText("metrics.query")).toBeInTheDocument();
    expect(screen.getByText("pending")).toBeInTheDocument();
    expect(screen.getByText("—")).toBeInTheDocument();
  });

  test("status=ok shows success badge + duration + output", () => {
    render(
      <ToolBlock
        block={{
          type: "tool",
          toolCallId: "tc-2",
          name: "incidents.list",
          status: "ok",
          input: '{ "since": "30d" }',
          output: "[{ id: INC-4012 }]",
          durationMs: 82,
          isError: false,
        }}
      />,
    );
    expect(screen.getByText("success")).toBeInTheDocument();
    expect(screen.getByText("82ms")).toBeInTheDocument();
    expect(screen.getByText(/INC-4012/)).toBeInTheDocument();
  });

  test("status=error shows error badge", () => {
    render(
      <ToolBlock
        block={{
          type: "tool",
          toolCallId: "tc-3",
          name: "k8s.deploy",
          status: "error",
          input: "{}",
          output: "permission denied",
          durationMs: 12,
          isError: true,
        }}
      />,
    );
    expect(screen.getByText("error")).toBeInTheDocument();
  });

  test("error with errorTaxonomy renders the taxonomy chip (Sprint 57.164)", () => {
    render(
      <ToolBlock
        block={{
          type: "tool",
          toolCallId: "tc-4",
          name: "incidents.get",
          status: "error",
          input: "{}",
          output: "not found",
          durationMs: 5,
          isError: true,
          errorTaxonomy: "parameter",
        }}
      />,
    );
    const chip = screen.getByTestId("tool-error-taxonomy");
    expect(chip).toBeInTheDocument();
    expect(chip).toHaveTextContent("parameter");
  });

  test("no chip when errorTaxonomy absent (Sprint 57.164)", () => {
    render(
      <ToolBlock
        block={{
          type: "tool",
          toolCallId: "tc-5",
          name: "metrics.query",
          status: "ok",
          input: "{}",
          output: "ok",
          durationMs: 3,
          isError: false,
        }}
      />,
    );
    expect(screen.queryByTestId("tool-error-taxonomy")).not.toBeInTheDocument();
  });
});

describe("VerificationBlock (mockup L234-244)", () => {
  test("ok variant renders claim + evidence", () => {
    render(
      <VerificationBlock
        block={{ type: "verification", verifier: "rules_v1", ok: true, claim: "Pool saturated", evidence: "metrics series" }}
      />,
    );
    expect(screen.getByText("Pool saturated")).toBeInTheDocument();
    expect(screen.getByText(/metrics series/)).toBeInTheDocument();
  });

  test("failed variant renders danger tone styling", () => {
    // Sprint 57.30 Day 4 §D2: verbatim re-point — failed variant is the
    // .block.verification.failed mockup class (styles-mockup.css L829-832).
    const { container } = render(
      <VerificationBlock
        block={{ type: "verification", verifier: "judge_v1", ok: false, claim: "missing evidence", evidence: "" }}
      />,
    );
    expect(screen.getByText("missing evidence")).toBeInTheDocument();
    expect(container.querySelector(".block.verification.failed")).toBeTruthy();
  });
});

describe("SubagentForkBlock (mockup L245-264)", () => {
  test("renders fork header with spawned count", () => {
    render(
      <SubagentForkBlock
        block={{
          type: "subagent_fork",
          agents: [
            {
              id: "sa-1",
              name: "log-scanner",
              task: "tail logs",
              status: "running",
              mode: "fork",
              tokensUsed: null,
            },
            {
              id: "sa-2",
              name: "dep-checker",
              task: "check deps",
              status: "done",
              mode: "fork",
              tokensUsed: 1500,
            },
          ],
        }}
      />,
    );
    expect(screen.getByText("Fork · concurrent")).toBeInTheDocument();
    expect(screen.getByText(/spawned 2 subagents/)).toBeInTheDocument();
    expect(screen.getByText("log-scanner")).toBeInTheDocument();
    expect(screen.getByText("dep-checker")).toBeInTheDocument();
    expect(screen.getByText("running")).toBeInTheDocument();
    expect(screen.getByText("done")).toBeInTheDocument();
    expect(screen.getByText("1,500 tok")).toBeInTheDocument();
  });

  test("single agent uses singular 'subagent' label", () => {
    render(
      <SubagentForkBlock
        block={{
          type: "subagent_fork",
          agents: [
            {
              id: "sa-x",
              name: "metrics-pull",
              task: "pgbouncer",
              status: "done",
              mode: "fork",
              tokensUsed: 850,
            },
          ],
        }}
      />,
    );
    expect(screen.getByText(/spawned 1 subagent$/)).toBeInTheDocument();
  });

  test("teammate-mode agents render 'Teammate · peer' label + real tokens (B2b)", () => {
    render(
      <SubagentForkBlock
        block={{
          type: "subagent_fork",
          agents: [
            {
              id: "tm-1",
              name: "patrol-peer",
              task: "scan servers",
              status: "done",
              mode: "teammate",
              tokensUsed: 3684,
            },
          ],
        }}
      />,
    );
    expect(screen.getByText("Teammate · peer")).toBeInTheDocument();
    expect(screen.queryByText("Fork · concurrent")).not.toBeInTheDocument();
    expect(screen.getByText("3,684 tok")).toBeInTheDocument();
  });
});

describe("BlockRender dispatcher", () => {
  test("dispatches thinking → ThinkingBlock", () => {
    render(<BlockRender block={{ type: "thinking", text: "ok" }} />);
    expect(screen.getByText("thinking")).toBeInTheDocument();
  });

  test("dispatches tool → ToolBlock", () => {
    render(
      <BlockRender
        block={{
          type: "tool",
          toolCallId: "x",
          name: "foo.bar",
          status: "pending",
          input: "{}",
          output: null,
          durationMs: null,
          isError: false,
        }}
      />,
    );
    expect(screen.getByText("foo.bar")).toBeInTheDocument();
  });

  test("dispatches verification → VerificationBlock", () => {
    render(
      <BlockRender block={{ type: "verification", verifier: "v", ok: true, claim: "c", evidence: "e" }} />,
    );
    expect(screen.getByText("c")).toBeInTheDocument();
  });

  test("dispatches subagent_fork → SubagentForkBlock", () => {
    render(
      <BlockRender
        block={{
          type: "subagent_fork",
          agents: [
            { id: "a", name: "n", task: "t", status: "running", mode: "fork", tokensUsed: null },
          ],
        }}
      />,
    );
    expect(screen.getByText("Fork · concurrent")).toBeInTheDocument();
  });
});
