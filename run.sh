#!/bin/bash
# run.sh — start main.py in a tmux session called "manoks"

SESSION="manoks"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# If the session already exists, just attach to it
if tmux has-session -t "$SESSION" 2>/dev/null; then
    echo "[run.sh] Session '$SESSION' already running — attaching..."
    tmux attach -t "$SESSION"
    exit 0
fi

# Create a new detached session and run main.py inside it
tmux new-session -d -s "$SESSION" -c "$SCRIPT_DIR"
tmux send-keys -t "$SESSION" "sudo python main.py" Enter

echo "[run.sh] Started in tmux session '$SESSION'."
echo "  Attach : tmux attach -t $SESSION"
echo "  Detach : Ctrl+B then D"
echo "  Kill   : tmux kill-session -t $SESSION"

# Attach automatically
tmux attach -t "$SESSION"
