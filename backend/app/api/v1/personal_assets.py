"""Personal wealth & asset ledger (2026-10-10, Theodore + Tally for Anthony).

Anthony's own holdings across 8 asset classes. Values are only ever entered by Anthony;
nothing is estimated or pre-filled by agents (No Assumptions rule). Stored in the
personal_assets table (see backend/scripts/stage5/personal_assets.sql).
"""
from __future__ import annotations

import uuid
from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.rbac import Permission, require_permission
from app.dependencies import get_db
from app.models.user import User

router = APIRouter()

ASSET_CLASSES = [
    {"key": "property", "label": "Property", "icon": "🏠"},
    {"key": "shares", "label": "Shares (equities)", "icon": "📈"},
    {"key": "super", "label": "Superannuation", "icon": "🏦"},
    {"key": "collectibles", "label": "Collectibles (Lego)", "icon": "🧱"},
    {"key": "metals", "label": "Precious metals", "icon": "🥇"},
    {"key": "crypto", "label": "Cryptocurrency", "icon": "🪙"},
    {"key": "cash", "label": "Cash savings", "icon": "💵"},
    {"key": "bonds", "label": "Bonds & fixed income", "icon": "📜"},
]
CLASS_KEYS = {c["key"] for c in ASSET_CLASSES}
OWNERS = ["Anthony (personal)", "YETI Holding Trust", "YETI Tipi Holdings Pty Ltd (as trustee)",
          "Cudan Studio Pty Ltd", "Superannuation fund", "Other / not sure yet"]


class Holding(BaseModel):
    asset_class: str
    name: str = Field(..., min_length=1, max_length=200)
    institution: str | None = Field(None, max_length=200)
    owner: str | None = Field(None, max_length=100)
    purchase_value_aud: float | None = Field(None, ge=0)
    current_estimate_aud: float | None = Field(None, ge=0)
    as_of: date | None = None
    notes: str | None = Field(None, max_length=2000)


def _check(h: Holding) -> None:
    if h.asset_class not in CLASS_KEYS:
        raise HTTPException(status_code=422, detail={"error": f"asset_class must be one of {sorted(CLASS_KEYS)}"})


@router.get("", tags=["personal-assets"])
async def list_assets(db: AsyncSession = Depends(get_db),
                      current_user: User = Depends(require_permission(Permission.FINANCE_READ))) -> dict[str, Any]:
    rows = (await db.execute(text(
        "select id, asset_class, name, institution, owner, purchase_value_aud, current_estimate_aud, as_of, notes, updated_at "
        "from personal_assets order by asset_class, name"))).mappings().all()
    holdings = [{**dict(r), "id": str(r["id"]), "as_of": r["as_of"].isoformat() if r["as_of"] else None,
                 "updated_at": r["updated_at"].isoformat()} for r in rows]
    classes = []
    for c in ASSET_CLASSES:
        hs = [h for h in holdings if h["asset_class"] == c["key"]]
        valued = [h["current_estimate_aud"] for h in hs if h["current_estimate_aud"] is not None]
        classes.append({**c, "holdings": len(hs), "valued": len(valued),
                        "total_aud": round(sum(valued), 2) if valued else None})
    entered = [c["total_aud"] for c in classes if c["total_aud"] is not None]
    return {"net_worth_aud": round(sum(entered), 2) if entered else None,
            "classes_with_values": len(entered), "classes": classes, "holdings": holdings, "owners": OWNERS}


@router.post("", tags=["personal-assets"])
async def add_asset(h: Holding, db: AsyncSession = Depends(get_db),
                    current_user: User = Depends(require_permission(Permission.FINANCE_READ))) -> dict[str, Any]:
    _check(h)
    new_id = uuid.uuid4()
    await db.execute(text(
        "insert into personal_assets (id, asset_class, name, institution, owner, purchase_value_aud, current_estimate_aud, as_of, notes) "
        "values (:id, :c, :n, :i, :o, :p, :v, :d, :notes)"),
        {"id": new_id, "c": h.asset_class, "n": h.name, "i": h.institution, "o": h.owner, "p": h.purchase_value_aud,
         "v": h.current_estimate_aud, "d": h.as_of, "notes": h.notes})
    return {"id": str(new_id)}


@router.put("/{asset_id}", tags=["personal-assets"])
async def update_asset(asset_id: uuid.UUID, h: Holding, db: AsyncSession = Depends(get_db),
                       current_user: User = Depends(require_permission(Permission.FINANCE_READ))) -> dict[str, Any]:
    _check(h)
    res = await db.execute(text(
        "update personal_assets set asset_class=:c, name=:n, institution=:i, owner=:o, purchase_value_aud=:p, "
        "current_estimate_aud=:v, as_of=:d, notes=:notes, updated_at=now() where id=:id"),
        {"id": asset_id, "c": h.asset_class, "n": h.name, "i": h.institution, "o": h.owner, "p": h.purchase_value_aud,
         "v": h.current_estimate_aud, "d": h.as_of, "notes": h.notes})
    if res.rowcount == 0:
        raise HTTPException(status_code=404, detail={"error": "Holding not found"})
    return {"id": str(asset_id)}


@router.delete("/{asset_id}", tags=["personal-assets"])
async def delete_asset(asset_id: uuid.UUID, db: AsyncSession = Depends(get_db),
                       current_user: User = Depends(require_permission(Permission.FINANCE_READ))) -> dict[str, Any]:
    res = await db.execute(text("delete from personal_assets where id=:id"), {"id": asset_id})
    if res.rowcount == 0:
        raise HTTPException(status_code=404, detail={"error": "Holding not found"})
    return {"deleted": str(asset_id)}
