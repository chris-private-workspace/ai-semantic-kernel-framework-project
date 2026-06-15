/**
 * File: frontend/tests/unit/chat_v2/SkillSlashMenu.test.tsx
 * Purpose: Vitest coverage for SkillSlashMenu (presentational skill picker).
 * Category: Frontend / tests / unit / chat_v2
 * Scope: Phase 57 / Sprint 57.115 (Skills slash-command)
 *
 * The menu is presentational (the InputBar owns filtering + activeIndex): renders
 * the already-filtered skills, highlights activeIndex (aria-selected), reports
 * select on click, and shows an empty-state row.
 *
 * Modification History:
 *   - 2026-06-15: Sprint 57.121 — +group header / kbd footer / empty-no-footer / active-class (mockup re-point)
 *   - 2026-06-14: Initial creation (Sprint 57.115)
 */

import "@testing-library/jest-dom/vitest";

import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import SkillSlashMenu from "@/features/chat_v2/components/SkillSlashMenu";

const SKILLS = [
  { name: "code-review", description: "Review code" },
  { name: "release-notes", description: "Write release notes" },
];

describe("SkillSlashMenu (Sprint 57.115)", () => {
  it("renders each skill's /name + description", () => {
    render(<SkillSlashMenu skills={SKILLS} activeIndex={0} onSelect={vi.fn()} onHover={vi.fn()} />);
    const row = screen.getByTestId("skill-slash-item-code-review");
    expect(row).toHaveTextContent("/code-review");
    expect(row).toHaveTextContent("Review code");
    expect(screen.getByTestId("skill-slash-item-release-notes")).toBeInTheDocument();
  });

  it("marks the activeIndex row aria-selected", () => {
    render(<SkillSlashMenu skills={SKILLS} activeIndex={1} onSelect={vi.fn()} onHover={vi.fn()} />);
    expect(screen.getByTestId("skill-slash-item-release-notes")).toHaveAttribute(
      "aria-selected",
      "true",
    );
    expect(screen.getByTestId("skill-slash-item-code-review")).toHaveAttribute(
      "aria-selected",
      "false",
    );
  });

  it("calls onSelect(name) when a row is clicked", async () => {
    const onSelect = vi.fn();
    render(
      <SkillSlashMenu skills={SKILLS} activeIndex={0} onSelect={onSelect} onHover={vi.fn()} />,
    );
    await userEvent.click(screen.getByTestId("skill-slash-item-release-notes"));
    expect(onSelect).toHaveBeenCalledWith("release-notes");
  });

  it("renders an empty-state row when no skills match", () => {
    render(<SkillSlashMenu skills={[]} activeIndex={0} onSelect={vi.fn()} onHover={vi.fn()} />);
    expect(screen.getByTestId("skill-slash-empty")).toBeInTheDocument();
  });

  // Sprint 57.121: the mockup re-point added a "Skills" group header + a kbd footer.
  it("renders the 'Skills' group header when skills are present", () => {
    render(<SkillSlashMenu skills={SKILLS} activeIndex={0} onSelect={vi.fn()} onHover={vi.fn()} />);
    expect(screen.getByText("Skills")).toBeInTheDocument();
  });

  it("renders the kbd footer with the skill count + keyboard hints", () => {
    render(<SkillSlashMenu skills={SKILLS} activeIndex={0} onSelect={vi.fn()} onHover={vi.fn()} />);
    expect(screen.getByText("2 skills")).toBeInTheDocument();
    expect(screen.getByText(/navigate/)).toBeInTheDocument();
    expect(screen.getByText(/select/)).toBeInTheDocument();
    expect(screen.getByText(/close/)).toBeInTheDocument();
  });

  it("omits the footer on the empty state", () => {
    render(<SkillSlashMenu skills={[]} activeIndex={0} onSelect={vi.fn()} onHover={vi.fn()} />);
    expect(screen.queryByText(/navigate/)).not.toBeInTheDocument();
  });

  it("gives the activeIndex row the 'active' class", () => {
    render(<SkillSlashMenu skills={SKILLS} activeIndex={1} onSelect={vi.fn()} onHover={vi.fn()} />);
    expect(screen.getByTestId("skill-slash-item-release-notes")).toHaveClass("active");
    expect(screen.getByTestId("skill-slash-item-code-review")).not.toHaveClass("active");
  });
});
