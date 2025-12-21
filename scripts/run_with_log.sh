#!/bin/bash
# Usage: ./run_with_log.sh [agent_id] command [arg1 arg2 ...]
#   - agent_id: Optional identifier for tagging in Antigravity agent workflows (e.g., "task-123").
#   - Runs the command, displays output live, and logs artifacts to error_log.md if errors detected.
#   - Tailored for Google Antigravity: Generates verifiable JSON artifacts for agent review/iteration,
#     supports autonomous execution modes, and includes hooks for browser/UI integration.

LOG_FILE="error_log.md"
TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")
AGENT_ID="${1:-}"  # Optional first arg as agent_id
shift  # Shift args if agent_id provided
CMD=("$@")  # Remaining args as command + params

# Create log file if it doesn't exist (as Antigravity artifact header)
if [ ! -f "$LOG_FILE" ]; then
  echo "# Antigravity Agent Execution Artifacts" > "$LOG_FILE"
  echo "Auto-generated logs for agentic verification, self-correction, and task review." >> "$LOG_FILE"
  echo "Includes JSON for automated parsing in workflows." >> "$LOG_FILE"
  echo "" >> "$LOG_FILE"
fi

# Temp files for output capture
TEMP_STDOUT=$(mktemp)
TEMP_STDERR=$(mktemp)
trap 'rm -f "$TEMP_STDOUT" "$TEMP_STDERR"' EXIT  # Clean up temps for clean agent runs

# Run command once: Stream to console while capturing (process substitution for live feedback)
"${CMD[@]}" > >(tee "$TEMP_STDOUT") 2> >(tee "$TEMP_STDERR" >&2)
EXIT_CODE=$?

# Read captured outputs
STDOUT_OUTPUT=$(cat "$TEMP_STDOUT")
STDERR_OUTPUT=$(cat "$TEMP_STDERR")

# Gather contextual data for Antigravity agent debugging (e.g., for plan verification)
CURRENT_DIR=$(pwd)
OS_INFO=$(uname -a)
GIT_HASH=$(git rev-parse HEAD 2>/dev/null || echo "Not in a git repo")
ENV_VARS=$(env | grep -E '^PATH=|^HOME=|^USER=|^TERM=' || echo "No relevant env vars")  # Add TERM for terminal context

# Log as artifact if error (non-zero exit or stderr) – optimizes for Antigravity's iterative loops
if [ $EXIT_CODE -ne 0 ] || [ -n "$STDERR_OUTPUT" ]; then
  echo "## Execution Artifact: \`${CMD[*]}\`" >> "$LOG_FILE"
  if [ -n "$AGENT_ID" ]; then
    echo "**Agent ID:** $AGENT_ID" >> "$LOG_FILE"
  fi
  echo "**Time:** $TIMESTAMP" >> "$LOG_FILE"
  echo "**Exit Code:** $EXIT_CODE" >> "$LOG_FILE"
  echo "**Directory:** $CURRENT_DIR" >> "$LOG_FILE"
  echo "**OS Info:** $OS_INFO" >> "$LOG_FILE"
  echo "**Git Hash:** $GIT_HASH" >> "$LOG_FILE"
  echo "**Relevant Env:**" >> "$LOG_FILE"
  echo "\`\`\`" >> "$LOG_FILE"
  echo "$ENV_VARS" >> "$LOG_FILE"
  echo "\`\`\`" >> "$LOG_FILE"
  echo "" >> "$LOG_FILE"
  
  echo "### Stdout:" >> "$LOG_FILE"
  echo "\`\`\`console" >> "$LOG_FILE"
  echo "$STDOUT_OUTPUT" >> "$LOG_FILE"
  echo "\`\`\`" >> "$LOG_FILE"
  echo "" >> "$LOG_FILE"
  
  echo "### Stderr:" >> "$LOG_FILE"
  echo "\`\`\`console" >> "$LOG_FILE"
  echo "$STDERR_OUTPUT" >> "$LOG_FILE"
  echo "\`\`\`" >> "$LOG_FILE"
  echo "" >> "$LOG_FILE"
  
  # Embedded JSON artifact for Antigravity agent parsing/self-correction
  echo "### JSON Verification Artifact (for agent analysis):" >> "$LOG_FILE"
  echo "\`\`\`json" >> "$LOG_FILE"
  echo "{"
  echo "  \"command\": \"${CMD[*]}\","
  echo "  \"agent_id\": \"$AGENT_ID\","
  echo "  \"timestamp\": \"$TIMESTAMP\","
  echo "  \"exit_code\": $EXIT_CODE,"
  echo "  \"directory\": \"$CURRENT_DIR\","
  echo "  \"os_info\": \"$OS_INFO\","
  echo "  \"git_hash\": \"$GIT_HASH\","
  echo "  \"env_vars\": \"$ENV_VARS\","
  echo "  \"stdout\": \"$(echo "$STDOUT_OUTPUT" | sed 's/"/\\"/g')\","
  echo "  \"stderr\": \"$(echo "$STDERR_OUTPUT" | sed 's/"/\\"/g')\""
  echo "}" >> "$LOG_FILE"
  echo "\`\`\`" >> "$LOG_FILE"
  echo "" >> "$LOG_FILE"
  
  # Optional Antigravity hook: Echo a note for the feed (agents can ingest this for browser/UI tasks)
  echo "Antigravity Note: Command failed – review artifact for iteration. Consider browser screenshot if UI-related." >&2
  
  # Placeholder for advanced integration: If scrot/imagemagick installed, capture screen on failure
  # (Uncomment if in GUI env; aligns with Antigravity's browser watching)
  # if command -v scrot >/dev/null; then
  #   SCREENSHOT="error_screenshot_${TIMESTAMP//[ :-]/_}.png"
  #   scrot "$SCREENSHOT"
  #   echo "**Screenshot Artifact:** $SCREENSHOT" >> "$LOG_FILE"
  # fi
  
  echo "---" >> "$LOG_FILE"
fi

# Exit with original code for seamless chaining in agent workflows
exit $EXIT_CODE