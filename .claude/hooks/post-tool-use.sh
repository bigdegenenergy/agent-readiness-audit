#!/bin/bash
# PostToolUse Hook - Runs after every tool use by Claude
# Primary use: Automatic code formatting and linting

# This hook is called with the following environment variables:
# - CLAUDE_TOOL_NAME: The name of the tool that was just used
# - CLAUDE_TOOL_OUTPUT: The output of the tool
# - CLAUDE_SESSION_ID: The current session ID

# Security: Use session-specific temp directory to prevent symlink attacks
# Create secure temp directory if not exists (owned by current user, not world-writable)
CLAUDE_TEMP_DIR="${TMPDIR:-/tmp}/claude-hooks-${UID:-$(id -u)}"
mkdir -p "$CLAUDE_TEMP_DIR" 2>/dev/null
chmod 700 "$CLAUDE_TEMP_DIR" 2>/dev/null
TIMESTAMP_FILE="$CLAUDE_TEMP_DIR/last_run_${CLAUDE_SESSION_ID:-default}"

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
    if find . -name "*.js" -o -name "*.ts" -o -name "*.jsx" -o -name "*.tsx" -newer "$TIMESTAMP_FILE" 2>/dev/null | grep -q .; then
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

    # Update timestamp
    touch "$TIMESTAMP_FILE"

    echo "✅ Formatting complete"
fi

# Track tool usage for metrics (optional)
echo "$(date -Iseconds),${CLAUDE_TOOL_NAME},${CLAUDE_SESSION_ID}" >> .claude/metrics/tool_usage.csv 2>/dev/null || true

# Exit with 0 to continue Claude's execution
exit 0
