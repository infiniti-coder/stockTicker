import json
from typing import Literal

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from . import service

router = APIRouter(prefix="/screener", tags=["screener"])


class ScreenerRunBody(BaseModel):
    region: Literal["india", "world"]
    criteria: str


@router.post("/run")
async def run_screener(body: ScreenerRunBody) -> StreamingResponse:
    async def event_stream():
        async for kind, payload in service.stream_screener_run(body.region, body.criteria):
            if kind == "delta":
                yield f"event: delta\ndata: {json.dumps({'text': payload})}\n\n"
            else:
                yield f"event: sources\ndata: {payload}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
