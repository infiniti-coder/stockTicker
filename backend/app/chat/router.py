import json

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db import get_db
from app.session import get_session_id

from . import service

router = APIRouter(prefix="/chat", tags=["chat"])


class PostMessageBody(BaseModel):
    content: str


@router.get("/messages")
def get_messages(db: Session = Depends(get_db), session_id: str = Depends(get_session_id)) -> list[dict]:
    return [
        {
            "role": m.role,
            "content": m.content,
            "sources": m.sources,
            "created_at": m.created_at.isoformat(),
        }
        for m in service.list_messages(db, session_id)
    ]


@router.post("/messages")
async def post_message(body: PostMessageBody, session_id: str = Depends(get_session_id)) -> StreamingResponse:
    async def event_stream():
        async for kind, payload in service.stream_chat_reply(session_id, body.content):
            if kind == "delta":
                yield f"event: delta\ndata: {json.dumps({'text': payload})}\n\n"
            else:
                yield f"event: sources\ndata: {payload}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
