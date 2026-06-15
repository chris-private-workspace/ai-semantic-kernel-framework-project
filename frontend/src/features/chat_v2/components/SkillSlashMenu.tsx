/**
 * File: frontend/src/features/chat_v2/components/SkillSlashMenu.tsx
 * Purpose: /skill-name composer autocomplete — a filtered, keyboard-navigable skill picker.
 * Category: Frontend / chat_v2 / components
 * Scope: Phase 57 / Sprint 57.115 (Skills slash-command); Sprint 57.121 (mockup re-point)
 *
 * Description:
 *   A dropdown floated above the composer when the user types a leading "/". The
 *   InputBar owns the filtering + the activeIndex (keyboard ↑/↓/Enter/Esc need
 *   filtered.length), so this component is presentational: it renders the
 *   ALREADY-FILTERED skills, highlights activeIndex, and reports select/hover.
 *
 *   Sprint 57.121: re-pointed from greenfield inline token-styles to the mockup
 *   .skill-menu* classes (reference/design-mockups/styles.css, copied byte-identical
 *   into styles-mockup.css; the SkillMenu component in page-chat.jsx is the source),
 *   adding the "Skills" group header + the kbd footer to match. The inline-style
 *   escape-hatch is gone — all visuals are mockup classes now.
 *
 * Created: 2026-06-14 (Sprint 57.115)
 * Last Modified: 2026-06-15
 *
 * Modification History (newest-first):
 *   - 2026-06-15: Sprint 57.121 — re-point inline-styles → mockup .skill-menu* classes + group header + kbd footer
 *   - 2026-06-14: Initial creation (Sprint 57.115)
 *
 * Related:
 *   - reference/design-mockups/page-chat.jsx (SkillMenu — the mockup source) + styles.css (.skill-menu*)
 *   - ./InputBar.tsx (owns the "/" trigger, the filter, the activeIndex + keyboard)
 *   - ../hooks/useChatSkills.ts (the skill list source)
 */

import type { ChatSkill } from "../services/chatService";

type Props = {
  /** Already filtered by the InputBar's slash query. */
  skills: ChatSkill[];
  activeIndex: number;
  onSelect: (name: string) => void;
  onHover: (index: number) => void;
};

export default function SkillSlashMenu({
  skills,
  activeIndex,
  onSelect,
  onHover,
}: Props): JSX.Element {
  return (
    <div className="skill-menu" data-testid="skill-slash-menu" role="listbox" aria-label="Skills">
      <div className="skill-menu-list">
        {skills.length === 0 ? (
          <div className="skill-menu-empty" data-testid="skill-slash-empty">
            No matching skills
          </div>
        ) : (
          <>
            <div className="skill-menu-group">Skills</div>
            {skills.map((skill, index) => {
              const active = index === activeIndex;
              return (
                <div
                  key={skill.name}
                  role="option"
                  aria-selected={active}
                  // Keyboard nav lives on the composer textarea (↑/↓/Enter); options are
                  // not tab-stops but must be focusable per the listbox role (tabIndex -1).
                  tabIndex={-1}
                  data-testid={`skill-slash-item-${skill.name}`}
                  className={active ? "skill-menu-item active" : "skill-menu-item"}
                  // onMouseDown (not onClick) fires BEFORE the textarea blur — a menu
                  // click must select without losing the composer focus first.
                  onMouseDown={(event) => {
                    event.preventDefault();
                    onSelect(skill.name);
                  }}
                  onMouseEnter={() => onHover(index)}
                >
                  <span className="skill-menu-name">/{skill.name}</span>
                  <span className="skill-menu-desc">{skill.description}</span>
                </div>
              );
            })}
          </>
        )}
      </div>
      {skills.length > 0 && (
        <div className="skill-menu-foot">
          <span>
            <span className="kbd">↑↓</span> navigate
          </span>
          <span>
            <span className="kbd">↵</span> select
          </span>
          <span>
            <span className="kbd">ESC</span> close
          </span>
          <span className="grow" />
          <span>
            {skills.length} skill{skills.length === 1 ? "" : "s"}
          </span>
        </div>
      )}
    </div>
  );
}
