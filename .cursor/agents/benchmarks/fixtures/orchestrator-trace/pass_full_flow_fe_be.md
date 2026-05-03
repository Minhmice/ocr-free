## Execution Plan

**Goal**: Implement upload endpoint and wire UI to it.

**Code scope**: `app/api/upload/**`, `components/UploadForm.tsx`

**Parallel agents** (run at the same time):

1. backend-developer
   Task: Add the upload API route with auth checks and validation.
   Inputs: existing auth patterns
   Output required: patch + how to test

2. frontend-developer
   Task: Update upload UI to call the new endpoint and handle loading/error/empty.
   Inputs: API contract (request/response)
   Output required: patch + manual test plan

**Phase 2 (mandatory unless explicitly skipped)**: After implementation merge, run **code-reviewer** and **qa-tester** in parallel.

Act as backend-developer per .cursor/agents/specialists/backend-developer/SKILL.md
Act as frontend-developer per .cursor/agents/specialists/frontend-developer/SKILL.md

