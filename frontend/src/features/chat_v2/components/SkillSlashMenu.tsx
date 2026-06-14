/* eslint-disable no-restricted-syntax -- net-new picker element with no mockup equivalent: inline styles use mockup CSS-var token vocabulary (var(--bg-2)/var(--border)/var(--primary)) for visual continuity, same escape hatch as InputBar production-only widgets (STYLE.md §1 + frontend-mockup-fidelity.md) */
/**
 * File: frontend/src/features/chat_v2/components/SkillSlashMenu.tsx
 * Purpose: /skill-name composer autocomplete — a filtered, keyboard-navigable skill picker.
 * Category: Frontend / chat_v2 / components
 * Scope: Phase 57 / Sprint 57.115 (Skills slash-command)
 *
 * Description:
 *   A net-new dropdown floated above the composer when the user types a leading
 *   "/". The InputBar owns the filtering + the activeIndex (keyboard ↑/↓/Enter/Esc
 *   need filtered.length), so this component is presentational: it renders the
 *   ALREADY-FILTERED skills, highlights activeIndex, and reports select/hover.
 *   No mockup reference exists for this element → inline styles use the mockup
 *   token vocabulary (the InputBar production-only-widget precedent).
 *
 * Created: 2026-06-14 (Sprint 57.115)
 *
 * Modification History (newest-first):
 *   - 2026-06-14: Initial creation (Sprint 57.115)
 *
 * Related:
 *   - ./InputBar.tsx (owns the "/" trigger, the filter, the activeIndex + keyboard)
 *   - ../hooks/useChatSkills.ts (the skill list source)
 *   - frontend/src/styles-mockup.css (the --bg-2 / --border / --primary tokens)
 */

import type { CSSProperties } from "react";

import type { ChatSkill } from "../services/chatService";

type Props = {
  /** Already filtered by the InputBar's slash query. */
  skills: ChatSkill[];
  activeIndex: number;
  onSelect: (name: string) => void;
  onHover: (index: number) => void;
};

const menuStyle: CSSProperties = {
  position: "absolute",
  bottom: "100%",
  left: 0,
  right: 0,
  marginBottom: 6,
  maxHeight: 240,
  overflowY: "auto",
  background: "var(--bg-2)",
  border: "1px solid var(--border)",
  borderRadius: 8,
  boxShadow: "var(--shadow)", // themed elevation token (not a colour literal)
  zIndex: 30,
  padding: 4,
};

export default function SkillSlashMenu({
  skills,
  activeIndex,
  onSelect,
  onHover,
}: Props): JSX.Element {
  return (
    <div
      className="skill-slash-menu"
      data-testid="skill-slash-menu"
      style={menuStyle}
      role="listbox"
      aria-label="Skills"
    >
      {skills.length === 0 ? (
        <div
          data-testid="skill-slash-empty"
          style={{ padding: "8px 10px", fontSize: 12, color: "var(--fg-muted)" }}
        >
          No matching skills
        </div>
      ) : (
        skills.map((skill, index) => {
          const active = index === activeIndex;
          const rowStyle: CSSProperties = {
            display: "flex",
            flexDirection: "column",
            gap: 2,
            padding: "6px 10px",
            borderRadius: 6,
            cursor: "pointer",
            background: active ? "var(--primary)" : "transparent",
            color: active ? "var(--primary-fg)" : "var(--fg)",
          };
          return (
            <div
              key={skill.name}
              role="option"
              aria-selected={active}
              // Keyboard nav lives on the composer textarea (↑/↓/Enter); options are
              // not tab-stops but must be focusable per the listbox role (tabIndex -1).
              tabIndex={-1}
              data-testid={`skill-slash-item-${skill.name}`}
              style={rowStyle}
              // onMouseDown (not onClick) fires BEFORE the textarea blur — a menu
              // click must select without losing the composer focus first.
              onMouseDown={(event) => {
                event.preventDefault();
                onSelect(skill.name);
              }}
              onMouseEnter={() => onHover(index)}
            >
              <span style={{ fontFamily: "var(--font-mono)", fontSize: 13, fontWeight: 500 }}>
                /{skill.name}
              </span>
              <span
                style={{
                  fontSize: 11,
                  color: active ? "var(--primary-fg)" : "var(--fg-muted)",
                }}
              >
                {skill.description}
              </span>
            </div>
          );
        })
      )}
    </div>
  );
}
