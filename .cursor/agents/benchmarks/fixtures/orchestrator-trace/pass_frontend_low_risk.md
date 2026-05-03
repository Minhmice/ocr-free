## Execution Plan

**Goal**: Fix button spacing on dashboard page.

**Code scope**: `app/components/DashboardButton.tsx`

**Parallel agents** (run at the same time):

1. frontend-developer
   Task: Adjust spacing; preserve a11y; keep change minimal.
   Inputs: existing component styles
   Output required: patch + brief test notes

**Rules**: UI bug or design fix; single-file/single-domain low-risk → 1 agent allowed.

**Phase 2 (mandatory unless explicitly skipped)**: After implementation merge, run **code-reviewer** and **qa-tester** in parallel.

Act as frontend-developer per .cursor/agents/specialists/frontend-developer/SKILL.md

