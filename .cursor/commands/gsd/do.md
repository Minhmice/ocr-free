---
name: gsd-do
description: Route freeform text to the closest local GSD command
argument-hint: "<what you want done>"
tools:
  read: true
  grep: true
  glob: true
---

<objective>
Infer the user's intent, choose the closest command in `.cursor/commands/gsd/`, read that command file, and follow its workflow. Act as a dispatcher only.
</objective>

<routing_rules>
- Prefer exact lifecycle matches: new-project, discuss-phase, plan-phase, execute-phase, verify-work, debug, progress, quick, map-codebase.
- If multiple commands fit, summarize the top match and use it unless a safety-critical ambiguity blocks execution.
- Do not paste or preload all GSD commands; load only the selected command and directly referenced local workflow files.
- If no GSD command fits, say so and hand back to the normal orchestrator flow.
</routing_rules>

<context>
$ARGUMENTS
</context>
