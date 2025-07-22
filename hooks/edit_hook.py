"""
Main hook implementation for Aider-style /edit functionality
"""

import json
import os
import sys
from typing import Dict, Any, Optional
from .edit_session import EditSessionManager
from .diff_utils import (
    generate_unified_diff, 
    format_diff_for_display, 
    is_complex_edit,
    count_changes
)


class EditHook:
    """Main hook class for intercepting and managing edit operations."""
    
    def __init__(self):
        self.session_manager = EditSessionManager()
        self.enabled = True
    
    def handle_pre_tool_use(self, tool_call: Dict[str, Any]) -> Dict[str, Any]:
        """Handle PreToolUse hook for edit operations."""
        tool_name = tool_call.get("name", "")
        
        # Check if this is an edit operation
        if tool_name not in ["Edit", "MultiEdit", "Write"]:
            return {"allow": True}
        
        # Check for edit control commands
        if self._is_edit_command(tool_call):
            return self._handle_edit_command(tool_call)
        
        # Handle regular edit operations
        return self._handle_edit_operation(tool_call)
    
    def _is_edit_command(self, tool_call: Dict[str, Any]) -> bool:
        """Check if this is an edit control command."""
        content = str(tool_call.get("parameters", {}))
        commands = ["/edit-apply", "/edit-review", "/edit-cancel", "/edit-list"]
        return any(cmd in content for cmd in commands)
    
    def _handle_edit_command(self, tool_call: Dict[str, Any]) -> Dict[str, Any]:
        """Handle edit control commands."""
        content = str(tool_call.get("parameters", {}))
        
        if "/edit-apply" in content:
            return self._handle_apply_command(content)
        elif "/edit-review" in content:
            return self._handle_review_command(content)
        elif "/edit-cancel" in content:
            return self._handle_cancel_command(content)
        elif "/edit-list" in content:
            return self._handle_list_command()
        
        return {"allow": True}
    
    def _handle_apply_command(self, content: str) -> Dict[str, Any]:
        """Handle /edit-apply command."""
        # Extract session ID
        parts = content.split()
        session_id = None
        for part in parts:
            if part.startswith("/edit-apply"):
                continue
            if len(part) == 8:  # Our session IDs are 8 characters
                session_id = part
                break
        
        if not session_id:
            return {
                "allow": False,
                "response": "❌ Please specify a session ID: /edit-apply <session_id>"
            }
        
        session = self.session_manager.get_session(session_id)
        if not session:
            return {
                "allow": False,
                "response": f"❌ Session {session_id} not found."
            }
        
        if session.status != "pending":
            return {
                "allow": False,
                "response": f"❌ Session {session_id} is already {session.status}."
            }
        
        # Apply the changes
        if self.session_manager.apply_session(session_id):
            return {
                "allow": False,
                "response": f"✅ Applied changes from session {session_id} to {session.filename}"
            }
        else:
            return {
                "allow": False,
                "response": f"❌ Failed to apply session {session_id}"
            }
    
    def _handle_review_command(self, content: str) -> Dict[str, Any]:
        """Handle /edit-review command."""
        # Extract session ID
        parts = content.split()
        session_id = None
        for part in parts:
            if part.startswith("/edit-review"):
                continue
            if len(part) == 8:
                session_id = part
                break
        
        if not session_id:
            return {
                "allow": False,
                "response": "❌ Please specify a session ID: /edit-review <session_id>"
            }
        
        session = self.session_manager.get_session(session_id)
        if not session:
            return {
                "allow": False,
                "response": f"❌ Session {session_id} not found."
            }
        
        # Generate and display diff
        diff = generate_unified_diff(
            session.original_content,
            session.new_content,
            session.filename
        )
        formatted_diff = format_diff_for_display(diff)
        additions, deletions = count_changes(diff)
        
        response = f"""
📋 **Review Session {session_id}**

**File:** {session.filename}
**Status:** {session.status}
**Changes:** +{additions} -{deletions}

**Diff:**
```diff
{formatted_diff}
```

**Commands:**
- `/edit-apply {session_id}` - Apply these changes
- `/edit-cancel {session_id}` - Cancel this session
"""
        
        return {
            "allow": False,
            "response": response.strip()
        }
    
    def _handle_cancel_command(self, content: str) -> Dict[str, Any]:
        """Handle /edit-cancel command."""
        # Extract session ID
        parts = content.split()
        session_id = None
        for part in parts:
            if part.startswith("/edit-cancel"):
                continue
            if len(part) == 8:
                session_id = part
                break
        
        if not session_id:
            return {
                "allow": False,
                "response": "❌ Please specify a session ID: /edit-cancel <session_id>"
            }
        
        if self.session_manager.cancel_session(session_id):
            return {
                "allow": False,
                "response": f"✅ Cancelled session {session_id}"
            }
        else:
            return {
                "allow": False,
                "response": f"❌ Session {session_id} not found"
            }
    
    def _handle_list_command(self) -> Dict[str, Any]:
        """Handle /edit-list command."""
        pending_sessions = self.session_manager.list_pending_sessions()
        
        if not pending_sessions:
            return {
                "allow": False,
                "response": "📝 No pending edit sessions."
            }
        
        response = "📝 **Pending Edit Sessions:**\n\n"
        for session in pending_sessions:
            diff = generate_unified_diff(
                session.original_content,
                session.new_content,
                session.filename
            )
            additions, deletions = count_changes(diff)
            
            response += f"**{session.session_id}** - {session.filename} (+{additions} -{deletions})\n"
        
        response += "\n**Commands:**\n"
        response += "- `/edit-review <session_id>` - Review changes\n"
        response += "- `/edit-apply <session_id>` - Apply changes\n"
        response += "- `/edit-cancel <session_id>` - Cancel session"
        
        return {
            "allow": False,
            "response": response
        }
    
    def _handle_edit_operation(self, tool_call: Dict[str, Any]) -> Dict[str, Any]:
        """Handle regular edit operations."""
        parameters = tool_call.get("parameters", {})
        
        # Extract file information
        if tool_call["name"] == "Edit":
            filename = parameters.get("path", "")
            new_content = parameters.get("content", "")
        elif tool_call["name"] == "Write":
            filename = parameters.get("path", "")
            new_content = parameters.get("content", "")
        elif tool_call["name"] == "MultiEdit":
            # For MultiEdit, we'll handle the first file for simplicity
            edits = parameters.get("edits", [])
            if not edits:
                return {"allow": True}
            filename = edits[0].get("path", "")
            new_content = edits[0].get("content", "")
        else:
            return {"allow": True}
        
        if not filename:
            return {"allow": True}
        
        # Read original content
        original_content = ""
        if os.path.exists(filename):
            try:
                with open(filename, 'r') as f:
                    original_content = f.read()
            except Exception:
                # If we can't read the file, allow the operation
                return {"allow": True}
        
        # Check if this is a complex edit that needs confirmation
        if not is_complex_edit(new_content, filename):
            return {"allow": True}
        
        # Create an interactive session
        session_id = self.session_manager.create_session(
            filename, original_content, new_content, tool_call
        )
        
        # Generate diff for preview
        diff = generate_unified_diff(original_content, new_content, filename)
        formatted_diff = format_diff_for_display(diff)
        additions, deletions = count_changes(diff)
        
        response = f"""
🔄 **Interactive Edit Mode** for `{filename}`

**Proposed changes:** +{additions} -{deletions}

**Preview:**
```diff
{formatted_diff}
```

**Edit session:** `{session_id}`

**Commands:**
- `/edit-apply {session_id}` - Apply these changes
- `/edit-review {session_id}` - Review changes again  
- `/edit-cancel {session_id}` - Cancel this edit
- `/edit-list` - List all pending edits

*This edit was intercepted because it appears to be complex or affects sensitive files.*
"""
        
        return {
            "allow": False,
            "response": response.strip()
        }


# Global hook instance
edit_hook = EditHook()


def pre_tool_use_hook(tool_call: Dict[str, Any]) -> Dict[str, Any]:
    """Entry point for PreToolUse hook."""
    return edit_hook.handle_pre_tool_use(tool_call)


if __name__ == "__main__":
    # Handle command line usage for testing
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "cleanup":
            edit_hook.session_manager.cleanup_old_sessions()
            print("Cleaned up old sessions")
        elif command == "list":
            sessions = edit_hook.session_manager.list_pending_sessions()
            if sessions:
                for session in sessions:
                    print(f"{session.session_id}: {session.filename} ({session.status})")
            else:
                print("No pending sessions")
