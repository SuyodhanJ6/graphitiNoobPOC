from typing import Dict, Optional
from src.utils.memory import ConversationMemoryManager

class SessionManager:
    """Manages conversation memories for different users/sessions."""
    
    def __init__(self):
        """Initialize the session manager."""
        self.sessions: Dict[str, ConversationMemoryManager] = {}
    
    def get_memory(self, session_id: str) -> ConversationMemoryManager:
        """Get or create a memory manager for a session.
        
        Args:
            session_id: Unique identifier for the user/session
            
        Returns:
            ConversationMemoryManager for the session
        """
        if session_id not in self.sessions:
            self.sessions[session_id] = ConversationMemoryManager()
        return self.sessions[session_id]
    
    def clear_session(self, session_id: str) -> None:
        """Clear a session's conversation memory.
        
        Args:
            session_id: Unique identifier for the user/session
        """
        if session_id in self.sessions:
            self.sessions[session_id].clear()
            del self.sessions[session_id]
    
    def get_all_sessions(self) -> Dict[str, ConversationMemoryManager]:
        """Get all active sessions.
        
        Returns:
            Dictionary of session IDs to memory managers
        """
        return self.sessions.copy()

# Global session manager instance
_session_manager = SessionManager()

def get_session_manager() -> SessionManager:
    """Get the global session manager instance.
    
    Returns:
        Global SessionManager instance
    """
    return _session_manager 