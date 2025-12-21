# Antigravity Agency Protocols
## Core Rules
- Always wrap shell commands in `./run_with_log.sh [agent_id] [command]` for artifact generation.
- Before any PLANNING, EXECUTION, or VERIFICATION step, review `error_log.md` and `lessons_learned.md` (if exists) using the view_file tool.
- If an error occurs, analyze it in VERIFICATION: Document root cause, why it failed, invalidated hypotheses, and prevention steps.

## Logging Execution Rule
[Your existing logging details here...]

## Error Learning Protocol
- **Pre-Task Review**: Use view_file to grep/search `error_log.md` and `lessons_learned.md` for similar issues. If matches found, adjust plan to avoid (e.g., "Avoid X because it caused Y in past run Z").
- **Post-Error Reflection**: In VERIFICATION, create/update `lessons_learned.md` artifact with:
  - Error summary (from JSON in error_log.md).
  - Root cause analysis (e.g., "Hallucinated command due to ambiguous spec").
  - Prevention rule (e.g., "Always confirm specs with notify_user before EXECUTION").
  - Add as a new section in this file for persistence across sessions.
- **Regression Testing**: For every bug fix, generate a "regression test" to capture the mistake and prevent recurrence (e.g., unit tests that fail on the bad pattern).

## Accumulated Lessons
- [Dynamic Section: Agent-Appended Entries]
  ### Lesson 1: NPM Dependency Conflicts (From Task-123, 2025-12-20)
  - Root Cause: Installed incompatible versions without checking package.json.
  - Prevention: Run `npm outdated` before installs; pin versions in plan.