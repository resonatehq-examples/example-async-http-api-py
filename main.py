from __future__ import annotations

# python std
import asyncio
import os
import uuid
from contextlib import asynccontextmanager
from typing import Any

# fast api
from fastapi import FastAPI, HTTPException

# resonate
from resonate.resonate import Resonate

# ---------------------------------------------------------------------------
# Resonate instance — constructed in the FastAPI lifespan so it starts after
# the event loop is running and can be cleanly shut down on exit.
# ---------------------------------------------------------------------------

_resonate: Resonate | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _resonate
    _resonate = Resonate(
        url=os.environ.get("RESONATE_URL", "http://localhost:8001"),
        group="gateway",
    )
    yield
    if _resonate is not None:
        await _resonate.stop()


app = FastAPI(lifespan=lifespan)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@app.post("/begin")
async def begin(data: Any = None, id: str | None = None) -> dict[str, Any]:
    assert _resonate is not None, "Resonate not initialised"

    # IMPORTANT: Provide your own ID for deduplication and retries.
    # Without a client-provided ID, retries will create duplicate work.
    if id is None:
        id = str(uuid.uuid4())

    # Set reasonable defaults for your use case.
    if data is None:
        data = {"foo": "bar"}

    # Dispatch durably to any node registered under the "worker" group.
    # The function will complete even if this process dies.
    handle = _resonate.options(target="worker").rpc(id, "foo", data)

    promise_id = await handle.id()
    return {
        "promise": promise_id,
        "status": "pending",
        "wait": f"/wait?id={promise_id}",
    }


@app.get("/wait")
async def wait(id: str) -> dict[str, Any]:
    assert _resonate is not None, "Resonate not initialised"

    try:
        handle = await _resonate.get(id)

        if handle.done():
            result = await handle.result()
            return {
                "status": "resolved",
                "promise_id": id,
                "result": result,
            }
        else:
            # Still processing — client should poll again.
            return {
                "status": "pending",
                "promise_id": id,
                "message": "Processing in progress",
            }
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"{id} not found") from e
