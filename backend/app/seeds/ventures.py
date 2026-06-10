"""Canonical empire venture registry — seed data for the `ventures` table.

Source of truth for the 18 tracked ventures (was previously hardcoded as
`_VENTURES` in `app/api/v1/dashboard.py`). Used by:
- Alembic migration 0002 (initial table seed + agent venture_id backfill)
- `app/scripts/seed_ventures.py` (idempotent re-sync after edits here)
"""
from __future__ import annotations

VENTURE_SEED_DATA: list[dict[str, str]] = [
    {"slug": "bloom-and-bub", "name": "Bloom & Bub", "manager_name": "maren", "category": "digital_product"},
    {"slug": "cudan-studio", "name": "Cudan Studio", "manager_name": "cruz", "category": "service"},
    {"slug": "kdp-colouring-books", "name": "KDP Colouring Books", "manager_name": "atlas", "category": "digital_product"},
    {"slug": "mapdrop", "name": "MapDrop", "manager_name": "remy", "category": "digital_product"},
    {"slug": "lo-fi-engine", "name": "Lo-Fi Engine", "manager_name": "kai", "category": "content"},
    {"slug": "ambient-escapes", "name": "Ambient Escapes", "manager_name": "murray", "category": "content"},
    {"slug": "domain-flipping", "name": "Domain Flipping", "manager_name": "scout", "category": "arbitrage"},
    {"slug": "polymarket-tracker", "name": "Polymarket Tracker", "manager_name": "quant", "category": "fintech"},
    {"slug": "prediction-pulse", "name": "Prediction Pulse", "manager_name": "quant", "category": "fintech"},
    {"slug": "handwritten-book", "name": "Handwritten Book", "manager_name": "wren", "category": "digital_product"},
    {"slug": "affiliate-empire", "name": "Affiliate Empire", "manager_name": "harper", "category": "affiliate"},
    {"slug": "weekly-wonder", "name": "Weekly Wonder", "manager_name": "wonder", "category": "content"},
    {"slug": "meal-plan-cart", "name": "Meal Plan Cart", "manager_name": "bondi", "category": "digital_product"},
    {"slug": "scroll-and-stone", "name": "Scroll & Stone", "manager_name": "levi", "category": "digital_product"},
    {"slug": "agentic-os", "name": "CortexOS", "manager_name": "orbit", "category": "saas"},
    {"slug": "wantsyoutoknow", "name": "WantsYouToKnow", "manager_name": "ellis", "category": "content"},
    {"slug": "the-footnote", "name": "The Footnote", "manager_name": "callum", "category": "content"},
    {"slug": "sage-ai", "name": "Sage AI", "manager_name": "neve", "category": "saas"},
]
