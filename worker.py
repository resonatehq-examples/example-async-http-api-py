from __future__ import annotations

# python std
import asyncio
import os
import time
from typing import TYPE_CHECKING

# resonate
from resonate.resonate import Resonate

if TYPE_CHECKING:
    from resonate.context import Context


# ---------------------------------------------------------------------------
# Durable function — registered with Resonate under the "worker" group.
# IMPORTANT: All parameters and return values must be JSON-serialisable.
# ---------------------------------------------------------------------------


async def foo(ctx: Context, data: object) -> dict[str, object]:
    # Add your processing, external API calls, database operations, etc.
    print("resolved at worker node", flush=True)
    return {"result": f"Processed: {data}", "timestamp": time.time()}


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


async def main() -> None:
    r = Resonate(
        url=os.environ.get("RESONATE_URL", "http://localhost:8001"),
        group="worker",
    )
    r.register(foo)
    print("worker running...", flush=True)
    await asyncio.Event().wait()  # keep the process alive


if __name__ == "__main__":
    asyncio.run(main())
