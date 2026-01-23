#!/bin/bash
# PostToolUse Hook - Runs after every tool use by Claude
# Primary use: Automatic code formatting and linting

# This hook is called with the following environment variables:
# - CLAUDE_TOOL_NAME: The name of the tool that was just used
# - CLAUDE_TOOL_OUTPUT: The output of the tool
# - CLAUDE_SESSION_ID: The current session ID

# Create a secure per-session temp directory
# Use CLAUDE_SESSION_ID to ensure session isolation, with fallback to a unique identifier
SESSION_ID="${CLAUDE_SESSION_ID:-$(id -u)-$$}"
SECURE_TEMP_DIR="${TMPDIR:-/tmp}/claude-hooks-${SESSION_ID}"

# Create the secure temp directory if it doesn't exist (with restrictive permissions)
if [[ ! -d "$SECURE_TEMP_DIR" ]]; then
    mkdir -p "$SECURE_TEMP_DIR"
    chmod 700 "$SECURE_TEMP_DIR"
fi

TIMESTAMP_FILE="${SECURE_TEMP_DIR}/last_run"

# Only run formatting if a file was modified
if [[ "$CLAUDE_TOOL_NAME" == "Edit" ]] || [[ "$CLAUDE_TOOL_NAME" == "Write" ]]; then

    # Extract the file path from the tool output (this is a simplified example)
    # In practice, you'd parse the actual tool output

    echo "🔧 Running post-tool-use formatting..."

    # Python files - Black formatter
    if find . -name "*.py" -newer "$TIMESTAMP_FILE" 2>/dev/null | grep -q .; then
        echo "  Formatting Python files with Black..."
        black --quiet . 2>/dev/null || true
        ruff check --fix . 2>/dev/null || true
    fi

    # JavaScript/TypeScript files - Prettier
    # Group the -name predicates with parentheses and apply -newer to the whole group
    if find . \( -name "*.js" -o -name "*.ts" -o -name "*.jsx" -o -name "*.tsx" \) -newer "$TIMESTAMP_FILE" 2>/dev/null | grep -q .; then
        echo "  Formatting JS/TS files with Prettier..."
        npx prettier --write "**/*.{js,ts,jsx,tsx}" 2>/dev/null || true
        npx eslint --fix . 2>/dev/null || true
    fi

    # Go files - gofmt
    if find . -name "*.go" -newer "$TIMESTAMP_FILE" 2>/dev/null | grep -q .; then
        echo "  Formatting Go files with gofmt..."
        gofmt -w . 2>/dev/null || true
    fi

    # Rust files - rustfmt
    if find . -name "*.rs" -newer "$TIMESTAMP_FILE" 2>/dev/null | grep -q .; then
        echo "  Formatting Rust files with rustfmt..."
        cargo fmt 2>/dev/null || true
    fi

    # Update timestamp in the secure temp directory
    touch "$TIMESTAMP_FILE"

    echo "✅ Formatting complete"
fi

# Track tool usage for metrics (optional)
echo "$(date -Iseconds),${CLAUDE_TOOL_NAME},${CLAUDE_SESSION_ID}" >> .claude/metrics/tool_usage.csv 2>/dev/null || true

# Exit with 0 to continue Claude's execution
exit 0
