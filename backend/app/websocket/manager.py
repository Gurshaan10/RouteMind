"""WebSocket connection manager for real-time features."""

from typing import Dict, Set, Optional
from fastapi import WebSocket
import json
import logging

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections for real-time collaboration."""

    def __init__(self):
        # session_id -> set of WebSocket connections
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # collaboration_session_id -> set of session_ids
        self.collaboration_sessions: Dict[str, Set[str]] = {}

    async def connect(self, websocket: WebSocket, session_id: str):
        """Accept a new WebSocket connection."""
        await websocket.accept()

        if session_id not in self.active_connections:
            self.active_connections[session_id] = set()

        self.active_connections[session_id].add(websocket)
        logger.info(f"WebSocket connected for session: {session_id}")

    def disconnect(self, websocket: WebSocket, session_id: str):
        """Remove a WebSocket connection."""
        if session_id in self.active_connections:
            self.active_connections[session_id].discard(websocket)

            # Clean up empty session
            if not self.active_connections[session_id]:
                del self.active_connections[session_id]

        logger.info(f"WebSocket disconnected for session: {session_id}")

    async def send_personal_message(self, message: dict, session_id: str):
        """Send a message to a specific session's connections."""
        if session_id in self.active_connections:
            for connection in self.active_connections[session_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error sending message to session {session_id}: {e}")

    async def broadcast_to_collaboration(self, message: dict, collab_session_id: str, exclude_session: Optional[str] = None):
        """Broadcast a message to all participants in a collaboration session."""
        if collab_session_id not in self.collaboration_sessions:
            return

        for session_id in self.collaboration_sessions[collab_session_id]:
            # Skip the sender if specified
            if exclude_session and session_id == exclude_session:
                continue

            await self.send_personal_message(message, session_id)

    async def join_collaboration(self, session_id: str, collab_session_id: str):
        """Add a session to a collaboration session."""
        if collab_session_id not in self.collaboration_sessions:
            self.collaboration_sessions[collab_session_id] = set()

        self.collaboration_sessions[collab_session_id].add(session_id)

        # Notify others about new participant
        await self.broadcast_to_collaboration(
            {
                "type": "user_joined",
                "session_id": session_id,
                "collab_session_id": collab_session_id,
            },
            collab_session_id,
            exclude_session=session_id
        )

        logger.info(f"Session {session_id} joined collaboration {collab_session_id}")

    async def leave_collaboration(self, session_id: str, collab_session_id: str):
        """Remove a session from a collaboration session."""
        if collab_session_id in self.collaboration_sessions:
            self.collaboration_sessions[collab_session_id].discard(session_id)

            # Notify others about participant leaving
            await self.broadcast_to_collaboration(
                {
                    "type": "user_left",
                    "session_id": session_id,
                    "collab_session_id": collab_session_id,
                },
                collab_session_id
            )

            # Clean up empty collaboration session
            if not self.collaboration_sessions[collab_session_id]:
                del self.collaboration_sessions[collab_session_id]

        logger.info(f"Session {session_id} left collaboration {collab_session_id}")

    def get_collaboration_participants(self, collab_session_id: str) -> Set[str]:
        """Get all session IDs in a collaboration session."""
        return self.collaboration_sessions.get(collab_session_id, set())


# Global connection manager instance
manager = ConnectionManager()
