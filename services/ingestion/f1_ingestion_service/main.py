"""Ingestion runtime: owns the stream connection + checkpoints.

Runs outside Temporal. Emits normalized events; Temporal activities consume
feature-snapshot references, never raw stream handles.
"""

import asyncio
import os


async def run() -> None:
    session = os.environ.get("SESSION_ID", "")
    print(f"[ingestion] scaffold running (SESSION_ID={session!r}); live feed TODO week 2")
    await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(run())
