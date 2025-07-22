"""
Session management for interactive edits
"""

import json
import os
import uuid
from typing import Dict, Any, Optional
from datetime import datetime, timedelta


class EditSession:
    """Manages an interactive edit session."""
    
    def __init__(self, session_id: str, filename: str, original_content: str, 
                 new_content: str, tool_call: Dict[str, Any]):
        self.session_id = session_id
        self.filename = filename
        self.original_content = original_content
        self.new_content = new_content
        self.tool_call = tool_call
        self.created_at = datetime.now()
        self.status = "pending"  # pending, applied, cancelled
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary for storage."""
        return {
            "session_id": self.session_id,
            "filename": self.filename,
            "original_content": self.original_content,
            "new_content": self.new_content,
            "tool_call": self.tool_call,
            "created_at": self.created_at.isoformat(),
            "status": self.status
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EditSession':
        """Create session from dictionary."""
        session = cls(
            data["session_id"],
            data["filename"],
            data["original_content"],
            data["new_content"],
            data["tool_call"]
        )
        session.created_at = datetime.fromisoformat(data["created_at"])
        session.status = data["status"]
        return session


class EditSessionManager:
    """Manages multiple edit sessions."""
    
    def __init__(self, storage_dir: str = ".claude_edit_sessions"):
        self.storage_dir = storage_dir
        self.sessions: Dict[str, EditSession] = {}
        self._ensure_storage_dir()
        self._load_sessions()
    
    def _ensure_storage_dir(self):
        """Ensure storage directory exists."""
        if not os.path.exists(self.storage_dir):
            os.makedirs(self.storage_dir)
    
    def _get_session_file(self, session_id: str) -> str:
        """Get file path for session storage."""
        return os.path.join(self.storage_dir, f"{session_id}.json")
    
    def _load_sessions(self):
        """Load existing sessions from storage."""
        if not os.path.exists(self.storage_dir):
            return
        
        for filename in os.listdir(self.storage_dir):
            if filename.endswith('.json'):
                session_id = filename[:-5]  # Remove .json
                try:
                    with open(os.path.join(self.storage_dir, filename), 'r') as f:
                        data = json.load(f)
                        session = EditSession.from_dict(data)
                        self.sessions[session_id] = session
                except Exception as e:
                    print(f"Error loading session {session_id}: {e}")
    
    def create_session(self, filename: str, original_content: str, 
                      new_content: str, tool_call: Dict[str, Any]) -> str:
        """Create a new edit session."""
        session_id = str(uuid.uuid4())[:8]  # Short ID for user convenience
        session = EditSession(session_id, filename, original_content, new_content, tool_call)
        
        self.sessions[session_id] = session
        self._save_session(session)
        
        return session_id
    
    def _save_session(self, session: EditSession):
        """Save session to storage."""
        session_file = self._get_session_file(session.session_id)
        with open(session_file, 'w') as f:
            json.dump(session.to_dict(), f, indent=2)
    
    def get_session(self, session_id: str) -> Optional[EditSession]:
        """Get session by ID."""
        return self.sessions.get(session_id)
    
    def apply_session(self, session_id: str) -> bool:
        """Apply the changes from a session."""
        session = self.get_session(session_id)
        if not session or session.status != "pending":
            return False
        
        try:
            # Write the new content to the file
            with open(session.filename, 'w') as f:
                f.write(session.new_content)
            
            session.status = "applied"
            self._save_session(session)
            return True
        except Exception as e:
            print(f"Error applying session {session_id}: {e}")
            return False
    
    def cancel_session(self, session_id: str) -> bool:
        """Cancel a session."""
        session = self.get_session(session_id)
        if not session:
            return False
        
        session.status = "cancelled"
        self._save_session(session)
        return True
    
    def list_pending_sessions(self) -> List[EditSession]:
        """List all pending sessions."""
        return [s for s in self.sessions.values() if s.status == "pending"]
    
    def cleanup_old_sessions(self, max_age_hours: int = 24):
        """Clean up old sessions."""
        cutoff = datetime.now() - timedelta(hours=max_age_hours)
        to_remove = []
        
        for session_id, session in self.sessions.items():
            if session.created_at < cutoff:
                to_remove.append(session_id)
                # Remove file
                session_file = self._get_session_file(session_id)
                if os.path.exists(session_file):
                    os.remove(session_file)
        
        for session_id in to_remove:
            del self.sessions[session_id]
