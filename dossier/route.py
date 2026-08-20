"""FastAPI wiring. One route ships in the image; every dossier after that is a
database row, so publishing one needs no deploy and no container restart.

Two lifecycle rules:
  - a dossier belongs to a session and dies when that session resets
  - `pinned` survives, for the one you actually want tomorrow
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, HTTPException, Response

from .render import CSP, render

router = APIRouter(prefix="/dossier", tags=["dossier"])

DEFAULT_TTL_HOURS = 48


async def create(session, *, session_id: str, doc: dict[str, Any],
                 pinned: bool = False) -> tuple[str, dict[str, Any]]:
    """Render now, store the html. Returns (dossier_id, meta).

    meta['identifiers'] holds what was stripped from the page — kept so the
    agent can resolve back to records, never shown to a reader.
    """
    html, meta = render(doc)
    did = uuid.uuid4().hex[:12]
    await session.execute(
        "INSERT INTO dossiers (id, session_id, title, html, meta, pinned, expires_at)"
        " VALUES (:id,:sid,:t,:h,:m,:p,:e)",
        {"id": did, "sid": session_id, "t": str(doc.get("title") or "Dossier"),
         "h": html, "m": meta, "p": pinned,
         "e": datetime.now(timezone.utc) + timedelta(hours=DEFAULT_TTL_HOURS)},
    )
    await session.commit()
    return did, meta


@router.get("/{dossier_id}")
async def get_dossier(dossier_id: str, session=None) -> Response:
    row = await _load(session, dossier_id)
    if row is None:
        raise HTTPException(status_code=404, detail="No such dossier")
    return Response(
        content=row["html"], media_type="text/html; charset=utf-8",
        headers={
            "Content-Security-Policy": CSP,
            # served to a person, never cached by a proxy in between
            "Cache-Control": "private, no-store",
            "X-Content-Type-Options": "nosniff",
            "Referrer-Policy": "no-referrer",
        },
    )


async def _load(session, dossier_id: str):
    res = await session.execute(
        "SELECT html FROM dossiers WHERE id = :id"
        " AND (pinned OR expires_at > now())", {"id": dossier_id})
    r = res.first()
    return {"html": r[0]} if r else None


async def clear_session(session, session_id: str) -> int:
    """Called on session reset. Pinned dossiers survive."""
    res = await session.execute(
        "DELETE FROM dossiers WHERE session_id = :sid AND NOT pinned",
        {"sid": session_id})
    await session.commit()
    return res.rowcount or 0
