/**
 * File: frontend/tests/unit/chat_v2/InputBar.slash.test.tsx
 * Purpose: Vitest coverage for InputBar's Sprint 57.115 /skill-name slash-command.
 * Category: Frontend / tests / unit / chat_v2
 * Scope: Phase 57 / Sprint 57.115 (Skills slash-command force-load)
 *
 * Description:
 *   "/" opens the picker; ↑/↓/Enter/Esc drive it; a leading "/skill-name" token
 *   (only a KNOWN skill) becomes force_load_skill + is stripped from the message;
 *   an unmatched "/foo" or a non-leading "/" stays plain text. Separate file from
 *   InputBar.test.tsx (the 57.101 inject coverage) — distinct basename, same harness.
 *
 * Modification History:
 *   - 2026-06-14: Initial creation (Sprint 57.115)
 */

import "@testing-library/jest-dom/vitest";

import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import InputBar from "@/features/chat_v2/components/InputBar";
import { useChatStore } from "@/features/chat_v2/store/chatStore";

const h = vi.hoisted(() => ({
  sendSpy: vi.fn(),
  injectSpy: vi.fn(),
  cancelSpy: vi.fn(),
  isRunning: false,
}));

vi.mock("@/features/chat_v2/hooks/useLoopEventStream", () => ({
  useLoopEventStream: () => ({
    send: h.sendSpy,
    inject: h.injectSpy,
    cancel: h.cancelSpy,
    resume: vi.fn(),
    isRunning: h.isRunning,
  }),
}));

vi.mock("react-i18next", () => ({
  useTranslation: () => ({ t: (k: string) => k }),
}));

vi.mock("@/features/chat_v2/hooks/useChatSkills", () => ({
  useChatSkills: () => ({
    data: [
      { name: "code-review", description: "Review code" },
      { name: "release-notes", description: "Write release notes" },
    ],
  }),
}));

const textarea = (): HTMLTextAreaElement =>
  screen.getByPlaceholderText(/Ask the agent/i) as HTMLTextAreaElement;

describe("InputBar — /skill-name slash command (Sprint 57.115)", () => {
  beforeEach(() => {
    h.isRunning = false;
    useChatStore.getState().reset();
    useChatStore.setState({ status: "idle", mode: "real_llm" });
  });
  afterEach(() => {
    useChatStore.getState().reset();
    vi.clearAllMocks();
  });

  it("typing '/' opens the skill menu with the tenant's skills", async () => {
    render(<InputBar />);
    await userEvent.type(textarea(), "/");
    expect(screen.getByTestId("skill-slash-menu")).toBeInTheDocument();
    expect(screen.getByTestId("skill-slash-item-code-review")).toBeInTheDocument();
    expect(screen.getByTestId("skill-slash-item-release-notes")).toBeInTheDocument();
  });

  it("filters the menu by the typed prefix", async () => {
    render(<InputBar />);
    await userEvent.type(textarea(), "/rel");
    expect(screen.getByTestId("skill-slash-item-release-notes")).toBeInTheDocument();
    expect(screen.queryByTestId("skill-slash-item-code-review")).not.toBeInTheDocument();
  });

  it("Enter selects the active item (inserts /name + space, no send)", async () => {
    render(<InputBar />);
    await userEvent.type(textarea(), "/rel");
    await userEvent.keyboard("{Enter}");
    expect(textarea().value).toBe("/release-notes ");
    expect(h.sendSpy).not.toHaveBeenCalled();
  });

  it("ArrowDown moves the active item then Enter selects it", async () => {
    render(<InputBar />);
    await userEvent.type(textarea(), "/");
    await userEvent.keyboard("{ArrowDown}{Enter}"); // index 0 → 1 = release-notes
    expect(textarea().value).toBe("/release-notes ");
  });

  it("Escape dismisses the menu", async () => {
    render(<InputBar />);
    await userEvent.type(textarea(), "/");
    expect(screen.getByTestId("skill-slash-menu")).toBeInTheDocument();
    await userEvent.keyboard("{Escape}");
    expect(screen.queryByTestId("skill-slash-menu")).not.toBeInTheDocument();
  });

  it("a leading /skill-name token force-loads + is stripped on send", async () => {
    render(<InputBar />);
    await userEvent.type(textarea(), "/code-review please look");
    await userEvent.click(screen.getByRole("button", { name: "Send" }));
    expect(h.sendSpy).toHaveBeenCalledWith("please look", { forceLoadSkill: "code-review" });
  });

  it("an unmatched /foo stays plain text (no force-load)", async () => {
    render(<InputBar />);
    await userEvent.type(textarea(), "/unknown do it");
    await userEvent.click(screen.getByRole("button", { name: "Send" }));
    expect(h.sendSpy).toHaveBeenCalledWith("/unknown do it");
  });

  it("a non-leading / stays plain text", async () => {
    render(<InputBar />);
    await userEvent.type(textarea(), "compute a/b ratio");
    await userEvent.click(screen.getByRole("button", { name: "Send" }));
    expect(h.sendSpy).toHaveBeenCalledWith("compute a/b ratio");
  });
});
