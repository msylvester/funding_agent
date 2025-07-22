---
description: View recent edit prompts
allowed-tools: Bash(tail:*), Bash(jq:*)
---

Recent edit prompts:

!`tail -5 ~/.claude/edit_history.jsonl | jq -r '.content' | head -200`
