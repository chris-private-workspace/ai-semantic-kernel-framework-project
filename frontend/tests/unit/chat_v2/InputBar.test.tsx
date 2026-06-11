/**
 * File: frontend/tests/unit/chat_v2/InputBar.test.tsx
 * Purpose: Vitest coverage for InputBar's Sprint 57.101 B1 mid-run injection routing.
 * Category: Frontend / tests / unit / chat_v2
 * Scope: Phase 57 / Sprint 57.101 (B1 — between-turns message injection primitive)
 *
 * Description:
 *   InputBar's composer is usable mid-run ONLY for real_llm (echo_demo is a
 *   scripted mock that cannot act on a mid-run note — gating avoids a dead control).
 *   Asserts:
 *     - idle: Send → useLoopEventStream.send (not inject)
 *     - running + real_llm: the textarea is enabled + the Inject button → inject (not send)
 *     - running + echo_demo: the textarea is disabled + there is no Inject button
 *
 * Modification History:
 *   - 2026-06-11: Initial creation (Sprint 57.101 B1)
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

describe("InputBar — mid-run injection vs idle send (Sprint 57.101 B1)", () => {
  beforeEach(() => {
    h.isRunning = false;
    useChatStore.getState().reset();
  });
  afterEach(() => {
    useChatStore.getState().reset();
    vi.clearAllMocks();
  });

  it("idle: typing + Send calls send (not inject)", async () => {
    h.isRunning = false;
    useChatStore.setState({ status: "idle", mode: "real_llm" });
    render(<InputBar />);

    await userEvent.type(screen.getByPlaceholderText(/Ask the agent/i), "hello");
    await userEvent.click(screen.getByRole("button", { name: "Send" }));

    expect(h.sendSpy).toHaveBeenCalledWith("hello");
    expect(h.injectSpy).not.toHaveBeenCalled();
  });

  it("running + real_llm: textarea enabled + Inject routes to inject (not send)", async () => {
    h.isRunning = true;
    useChatStore.setState({ status: "running", mode: "real_llm" });
    render(<InputBar />);

    const ta = screen.getByPlaceholderText(/Add an instruction for the running agent/i);
    expect(ta).not.toBeDisabled();
    await userEvent.type(ta, "also check X");
    await userEvent.click(screen.getByTestId("inject-send"));

    expect(h.injectSpy).toHaveBeenCalledWith("also check X");
    expect(h.sendSpy).not.toHaveBeenCalled();
  });

  it("running + echo_demo: textarea disabled + no Inject button", () => {
    h.isRunning = true;
    useChatStore.setState({ status: "running", mode: "echo_demo" });
    render(<InputBar />);

    expect(screen.getByPlaceholderText(/Ask the agent/i)).toBeDisabled();
    expect(screen.queryByTestId("inject-send")).not.toBeInTheDocument();
  });
});
