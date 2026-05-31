# Pull Request

## Summary

<!-- 1-3 sentences. What changed and why? -->

## Sprint linkage

- Sprint plan: `docs/sprints/sprint-XX-Y-plan.md`
- Sprint checklist: `docs/sprints/sprint-XX-Y-checklist.md`
- Progress doc: `docs/sprints/sprint-XX-Y/progress.md`

## Anti-Patterns Checklist (.claude/rules/anti-patterns-checklist.md)

- [ ] AP-U1: No orphan / side-track code (traceable from entry point)
- [ ] AP-U2: No partial features / TODO stubs (works end-to-end + tests)
- [ ] AP-U3: No cross-directory scattering (one concern, one place)
- [ ] AP-U4: Name matches behavior (+ negative test)
- [ ] AP-U5: Mock and real share the same interface
- [ ] AP-U6: No version suffixes; naming consistent
<!-- add AP-P* project-specific rows here -->

## Test plan

<!-- How were the changes verified? -->

- [ ]
- [ ]

## CI Gates

- [ ] `{{FORMAT_CMD}}` (check mode)
- [ ] `{{LINT_CMD}}`
- [ ] `{{TYPECHECK_CMD}}`
- [ ] `{{TEST_CMD}}`
- [ ] `python scripts/lint/run_all.py`

🤖 Per `.claude/rules/sprint-workflow.md` Before-Commit checklist
