"""
Session management for tracking thread_ids across requests.
Enables checkpointing to work with stateless HTTP requests.
"""
from typing import Dict, Optional
import uuid
from datetime import datetime, timedelta

from common.logging_config import get_logger

logger = get_logger(__name__)


class SessionManager:
    """
    Manages session to thread_id mappings for checkpointing.
    
    When checkpointing is enabled, this ensures the same thread_id
    is used for all requests in a session, enabling conversation memory.
    """
    
    def __init__(self, session_timeout_minutes: int = 60):
        """
        Initialize session manager.
        
        Args:
            session_timeout_minutes: Minutes before session expires
        """
        self._sessions: Dict[str, Dict] = {}
        self._timeout_minutes = session_timeout_minutes
        logger.info(f"SessionManager initialized - timeout: {session_timeout_minutes}min")
    
    def get_or_create_thread_id(self, session_id: Optional[str] = None) -> tuple[str, str]:
        """
        Get thread_id for session, creating new one if needed.
        
        Args:
            session_id: Session identifier (auto-generated if None)
            
        Returns:
            Tuple of (session_id, thread_id)
        """
        # Generate session_id if not provided
        if session_id is None:
            session_id = str(uuid.uuid4())
            logger.debug(f"Generated new session_id: {session_id}")
        
        # Clean expired sessions
        self._cleanup_expired()
        
        # Get or create session
        if session_id in self._sessions:
            session = self._sessions[session_id]
            session['last_accessed'] = datetime.now()
            thread_id = session['thread_id']
            logger.debug(f"Reusing thread_id for session {session_id}: {thread_id}")
        else:
            thread_id = str(uuid.uuid4())
            self._sessions[session_id] = {
                'thread_id': thread_id,
                'created_at': datetime.now(),
                'last_accessed': datetime.now()
            }
            logger.info(f"Created new session {session_id} with thread_id: {thread_id}")
        
        return session_id, thread_id
    
    def _cleanup_expired(self):
        """Remove expired sessions."""
        now = datetime.now()
        timeout_delta = timedelta(minutes=self._timeout_minutes)
        
        expired = [
            sid for sid, sess in self._sessions.items()
            if now - sess['last_accessed'] > timeout_delta
        ]
        
        for sid in expired:
            del self._sessions[sid]
            logger.debug(f"Removed expired session: {sid}")
    
    def get_session_count(self) -> int:
        """Get active session count."""
        self._cleanup_expired()
        return len(self._sessions)


# Global session manager instance
_session_manager = SessionManager()


def get_session_manager() -> SessionManager:
    """Get global session manager instance."""
    return _session_manager
