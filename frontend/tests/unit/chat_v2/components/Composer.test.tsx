/**
 * File: frontend/tests/unit/chat_v2/components/Composer.test.tsx
 * Purpose: Vitest visual scaffolding coverage for Sprint 57.21 Day 4 §4.2 Composer.
 * Category: Frontend / tests / unit / chat_v2
 * Scope: Phase 57.21 Day 4 §4.2 (visual-only; production send path stays in InputBar.tsx)
 *
 * Created: 2026-05-17 (Sprint 57.21 Day 4 §4.2)
 *
 * Modification History:
 *   - 2026-05-17: Initial creation (Sprint 57.21 Day 4 §4.2)
 */

import { render, screen } from "@testing-library/react";
import { describe, expect, test } from "vitest";

import { Composer } from "@/features/chat_v2/components/Composer";

describe("Composer visual scaffolding (Sprint 57.21 Day 4 §4.2)", () => {
  test("renders textarea with mockup placeholder copy (disabled)", () => {
    render(<Composer />);
    const ta = screen.getByTestId("composer-input") as HTMLTextAreaElement;
    expect(ta).toBeInTheDocument();
    expect(ta.disabled).toBe(true);
    expect(ta.placeholder).toMatch(/Ask the agent/);
    expect(ta.placeholder).toMatch(/INC-4087/);
  });

  test("3 disabled coming-soon buttons render with mockup labels + carryover AD tooltip", () => {
    render(<Composer />);
    const attach = screen.getByTestId("composer-attach") as HTMLButtonElement;
    const tools = screen.getByTestId("composer-tools") as HTMLButtonElement;
    const memScope = screen.getByTestId("composer-memory-scope") as HTMLButtonElement;
    expect(attach.disabled).toBe(true);
    expect(tools.disabled).toBe(true);
    expect(memScope.disabled).toBe(true);
    expect(attach.title).toMatch(/AD-ChatV2-Composer-Richness-Phase2/);
    expect(tools.title).toMatch(/AD-ChatV2-Composer-Richness-Phase2/);
    expect(memScope.title).toMatch(/AD-ChatV2-Composer-Richness-Phase2/);
    expect(screen.getByText("Attach")).toBeInTheDocument();
    expect(screen.getByText("Tools (24)")).toBeInTheDocument();
    expect(screen.getByText("Memory scope")).toBeInTheDocument();
  });

  test("model + provider neutral chips render", () => {
    render(<Composer />);
    expect(screen.getByText("claude-haiku-4-5")).toBeInTheDocument();
    expect(screen.getByText("neutral")).toBeInTheDocument();
  });

  test("Send button disabled with carryover AD tooltip", () => {
    render(<Composer />);
    const send = screen.getByTestId("composer-send") as HTMLButtonElement;
    expect(send.disabled).toBe(true);
    expect(send.title).toMatch(/AD-ChatV2-Composer-Wire-Phase2/);
  });

  test("drop hint with file-type list renders", () => {
    render(<Composer />);
    expect(screen.getByText(/Drop files anywhere/)).toBeInTheDocument();
    expect(screen.getByText(/25MB each/)).toBeInTheDocument();
  });
});
