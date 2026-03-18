"""WebSocket routes for real-time features."""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from app.websocket.manager import manager
from app.core.session import get_session_id
import logging
import json

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws/{session_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    session_id: str,
):
    """
    WebSocket endpoint for real-time updates.

    Handles:
    - Real-time itinerary updates
    - Collaborative planning
    - Live activity suggestions
    - Presence indicators
    """
    await manager.connect(websocket, session_id)

    try:
        # Send welcome message
        await websocket.send_json({
            "type": "connected",
            "session_id": session_id,
            "message": "WebSocket connected successfully"
        })

        while True:
            # Receive and process messages
            data = await websocket.receive_text()

            try:
                message = json.loads(data)
                message_type = message.get("type")

                if message_type == "ping":
                    # Heartbeat
                    await websocket.send_json({"type": "pong"})

                elif message_type == "join_collaboration":
                    # Join a collaboration session
                    collab_session_id = message.get("collab_session_id")
                    if collab_session_id:
                        await manager.join_collaboration(session_id, collab_session_id)
                        await websocket.send_json({
                            "type": "collaboration_joined",
                            "collab_session_id": collab_session_id,
                            "participants": list(manager.get_collaboration_participants(collab_session_id))
                        })

                elif message_type == "leave_collaboration":
                    # Leave a collaboration session
                    collab_session_id = message.get("collab_session_id")
                    if collab_session_id:
                        await manager.leave_collaboration(session_id, collab_session_id)

                elif message_type == "collab_update":
                    # Broadcast update to collaboration session
                    collab_session_id = message.get("collab_session_id")
                    if collab_session_id:
                        await manager.broadcast_to_collaboration(
                            {
                                "type": "collab_update",
                                "data": message.get("data"),
                                "from_session": session_id,
                            },
                            collab_session_id,
                            exclude_session=session_id
                        )

                elif message_type == "typing":
                    # Typing indicator for collaboration
                    collab_session_id = message.get("collab_session_id")
                    if collab_session_id:
                        await manager.broadcast_to_collaboration(
                            {
                                "type": "typing",
                                "from_session": session_id,
                                "is_typing": message.get("is_typing", False),
                            },
                            collab_session_id,
                            exclude_session=session_id
                        )

                else:
                    logger.warning(f"Unknown message type: {message_type}")

            except json.JSONDecodeError:
                logger.error(f"Invalid JSON received: {data}")
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid JSON format"
                })

    except WebSocketDisconnect:
        manager.disconnect(websocket, session_id)
        logger.info(f"WebSocket disconnected: {session_id}")

    except Exception as e:
        logger.error(f"WebSocket error for session {session_id}: {e}")
        manager.disconnect(websocket, session_id)
