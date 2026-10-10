"""Autonomous web research loop — per venture, daily.

Phase 1 flow:
  1. Intent: pick a query for the venture
  2. Search: Tavily (if key set) else DuckDuckGo
  3. Filter: score relevance, drop < 0.5
  4. Memory: write each finding to CortexOS
  5. Insight: Claude extracts ONE actionable insight
  6. Notify: post to Mattermost #cross-venture-intel

Phase 2 flow (approval + outcome tracking):
  7. Record a ResearchAction row per posted insight (status=pending)
  8. check_action_approvals: poll Mattermost reactions on pending posts,
     flip status to approved/rejected, schedule a +14 day outcome reminder
  9. send_outcome_reminders: thread-reply asking Anthony to report what
     happened (manual metric tracking — no venture analytics API wired yet)
"""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx
import structlog

from app.tasks.celery_app import celery_app

logger = structlog.get_logger(__name__)

MM_BASE = "https://dash.anthonyzed.work/chat/api/v4"
MM_CHANNEL = "rtguyjtcij8dpjppwubrr65pbc"  # #cross-venture-intel
APPROVE_EMOJIS = {"white_check_mark", "heavy_check_mark", "ballot_box_with_check"}
REJECT_EMOJIS = {"x", "negative_squared_cross_mark", "no_entry_sign"}
REMINDER_DELAY_DAYS = 14

VENTURE_CONFIG: dict[str, dict] = {
    "cudan-studio": {
        "name": "Cudan Studio",
        "description": "Physical photography and content creation studio in Kenwick WA. Monthly rent AUD 2400. Offers corporate headshots, event photography, product shoots, studio hire. CURRENT PRICING (confirmed, do not override): $50/hr weekday studio hire, $60/hr weekend studio hire. Owner has stated price is NOT the problem right now — the priority is increasing booking volume and average booking duration, not raising rates. ALREADY DONE (do not re-suggest): Google Business Profile is already set up and live — do not recommend creating or optimizing GBP as if it doesn't exist.",
        "queries": [
            "how to get more bookings photography studio hire marketing",
            "content creation studio hire Perth marketing strategy",
            "studio hire longer session upsell package ideas",
            "photography studio booking platforms Peerspace Tagvenue Perth listing tips",
            "small business studio hire local SEO Google Business Profile",
        ],
        "action_types": "booking volume strategy, session length upsell, marketing copy, SEO/GBP, service offering addition (NOT pricing — current $50/60 per hr weekday/weekend is confirmed correct)",
    },
    "bloom-bub": {
        "name": "Bloom & Bub",
        "description": "Premium digital baby and maternity products brand. Products: Pregnancy Journal, Milestone Cards, Baby Cheat Sheet, Welcome Baby Book. Sold on Etsy and Gumroad. Australian market focus.",
        "queries": [
            "pregnancy journal Etsy best seller 2026 pricing",
            "baby milestone cards digital download trending Etsy",
            "maternity digital products Australia market",
            "printable baby shower products Etsy competition",
            "pregnancy tracker printable Etsy pricing AU",
        ],
        "action_types": "price change, listing title/tags update, new product idea, bundle strategy, SEO keywords",
    },
    "gtt-perth": {
        "name": "GTT Center Perth",
        "description": "WA's first premium waiting experience for pregnant women undergoing the mandatory 2-3hr Glucose Tolerance Test (GTT). Transforms the wait into a restorative experience: massage, nails, hair, 3D keepsake ultrasound. Model: pathology partner (PathWest/WDP) handles blood draws, sublet practitioners deliver beauty/wellness services. Status: pre-revenue/STANDBY, Perth WA. Entity: YETI Holding Trust.",
        "queries": [
            "pregnancy pamper spa Perth pricing packages",
            "3D 4D keepsake ultrasound Perth pricing studios",
            "pregnancy massage Perth mobile or studio pricing",
            "medical spa sublet practitioner model Australia",
            "pathology clinic partnership wellness studio Perth",
            "pregnant women wellness experience Perth marketing",
        ],
        "action_types": "site/location strategy, pricing packages, pathology partnership positioning, marketing/launch content, sublet practitioner recruitment",
    },
}

INSIGHT_PROMPT = """You are a business strategist analysing web research for: {name}

Venture context: {description}

Web research findings:
{findings}

Extract EXACTLY ONE insight and ONE specific action from this research. Be concrete and specific.

Respond in JSON only:
{{
  "insight": "One sentence: what the research reveals that matters to this venture",
  "action": "One sentence: the specific action to take (include numbers/prices/keywords where relevant)",
  "action_type": "one of: pricing | listing_copy | seo | product_idea | service_offering | marketing",
  "confidence": 0.0-1.0,
  "source_urls": ["url1", "url2"]
}}"""


def _run_async(coro: Any) -> Any:
    import asyncio
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def _mm_headers() -> dict:
    tok = os.environ.get("MM_BOT_TOKEN", "")
    return {"Authorization": f"Bearer {tok}"}


def _search_tavily(query: str, api_key: str) -> list[dict]:
    try:
        from tavily import TavilyClient
        client = TavilyClient(api_key=api_key)
        resp = client.search(query, max_results=5, search_depth="basic")
        results = []
        for r in resp.get("results", []):
            results.append({
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "content": r.get("content", "")[:800],
                "score": float(r.get("score", 0.7)),
            })
        return results
    except Exception as e:
        logger.warning("tavily_failed", error=str(e))
        return []


def _search_duckduckgo(query: str) -> list[dict]:
    try:
        from duckduckgo_search import DDGS
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=5):
                results.append({
                    "title": r.get("title", ""),
                    "url": r.get("href", ""),
                    "content": r.get("body", "")[:800],
                    "score": 0.65,
                })
        return results
    except Exception as e:
        logger.warning("duckduckgo_failed", error=str(e))
        return []


def _search(query: str) -> list[dict]:
    tavily_key = os.environ.get("TAVILY_API_KEY", "")
    if tavily_key:
        results = _search_tavily(query, tavily_key)
        if results:
            return results
    return _search_duckduckgo(query)


def _score_relevance(results: list[dict], venture_desc: str) -> list[dict]:
    """Keep results with score >= 0.5 and deduplicate by URL."""
    seen = set()
    out = []
    for r in results:
        url = r.get("url", "")
        if url in seen or not r.get("content"):
            continue
        seen.add(url)
        if r.get("score", 0) >= 0.5:
            out.append(r)
    return out[:6]


def _extract_insight(venture_slug: str, findings: list[dict]) -> dict | None:
    try:
        import anthropic
        config = VENTURE_CONFIG[venture_slug]
        findings_text = "\n\n".join(
            f"Source: {f['url']}\nTitle: {f['title']}\n{f['content']}"
            for f in findings[:5]
        )
        _gate_on = os.environ.get('EMPIRE_USE_SPENDING_GATE', 'true').lower() != 'false'
        _gate_host = os.environ.get('CORTEXOS_GATE_HOST', '172.25.0.1')
        client = anthropic.Anthropic(
            api_key=os.environ["ANTHROPIC_API_KEY"],
            base_url=f'http://{_gate_host}:8900' if _gate_on else None,
            default_headers={'x-gate-venture': 'cortexos-australia', 'x-gate-manager': 'idea-lobster', 'x-gate-task': 'research-task'} if _gate_on else None,
        )
        msg = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=400,
            messages=[{
                "role": "user",
                "content": INSIGHT_PROMPT.format(
                    name=config["name"],
                    description=config["description"],
                    findings=findings_text,
                ),
            }],
        )
        raw = msg.content[0].text.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        return json.loads(raw)
    except Exception as e:
        logger.error("insight_extraction_failed", error=str(e))
        return None


def _post_mattermost(venture_slug: str, insight: dict, memory_count: int) -> str | None:
    """Post the insight to Mattermost. Returns the post_id, or None on failure."""
    config = VENTURE_CONFIG[venture_slug]
    tok = os.environ.get("MM_BOT_TOKEN", "")
    if not tok:
        logger.warning("no_mm_token")
        return None

    action_emoji = {
        "pricing": ":moneybag:",
        "listing_copy": ":pencil:",
        "seo": ":mag:",
        "product_idea": ":bulb:",
        "service_offering": ":sparkles:",
        "marketing": ":mega:",
    }.get(insight.get("action_type", ""), ":robot_face:")

    confidence_pct = int(insight.get("confidence", 0.7) * 100)
    sources = insight.get("source_urls", [])
    source_text = "\n".join(f"  - {u}" for u in sources[:3]) if sources else "  - (no URLs)"

    text = f"""### {action_emoji} Research Insight — {config['name']}

**Insight:** {insight.get('insight', 'N/A')}

**Proposed Action:** {insight.get('action', 'N/A')}

**Type:** `{insight.get('action_type', 'unknown')}` | **Confidence:** {confidence_pct}%

**Sources:**
{source_text}

*{memory_count} new findings stored to memory · React :white_check_mark: to approve or :x: to reject*"""

    try:
        r = httpx.post(
            f"{MM_BASE}/posts",
            headers=_mm_headers(),
            json={"channel_id": MM_CHANNEL, "message": text},
            timeout=10,
        )
        if r.status_code == 201:
            return r.json().get("id")
        logger.error("mattermost_post_failed", status=r.status_code, body=r.text[:200])
        return None
    except Exception as e:
        logger.error("mattermost_post_failed", error=str(e))
        return None


async def _run_research(venture_slug: str) -> dict:
    from app.database import AsyncSessionLocal
    from app.models.memory_item import MemoryItem
    from app.models.research_action import ResearchAction
    from sqlalchemy import select

    config = VENTURE_CONFIG.get(venture_slug)
    if not config:
        return {"error": f"unknown venture: {venture_slug}"}

    today = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")
    queries = config["queries"]

    day_num = datetime.now(tz=timezone.utc).timetuple().tm_yday
    selected = [queries[day_num % len(queries)], queries[(day_num + 1) % len(queries)]]

    all_findings: list[dict] = []
    for q in selected:
        results = _search(q)
        scored = _score_relevance(results, config["description"])
        all_findings.extend(scored)

    if not all_findings:
        return {"venture": venture_slug, "findings": 0, "error": "no results"}

    async with AsyncSessionLocal() as db:
        existing = set(
            (await db.execute(
                select(MemoryItem.external_id).where(
                    MemoryItem.external_id.like(f"research:{venture_slug}:%")
                )
            )).scalars().all()
        )
        added = 0
        for f in all_findings:
            url_hash = hashlib.md5(f["url"].encode()).hexdigest()[:12]
            ext_id = f"research:{venture_slug}:{url_hash}"
            if ext_id in existing:
                continue
            content = (
                f"Web research for {config['name']} [{today}]: "
                f"{f['title']}. {f['content']} Source: {f['url']}"
            )
            db.add(MemoryItem(
                external_id=ext_id,
                summary=f"Research: {f['title'][:80]}",
                content=content,
                memory_type="semantic",
                category="research",
                importance_score=min(0.9, f.get("score", 0.65)),
                tags=json.dumps([venture_slug, "web-research", "auto"]),
            ))
            existing.add(ext_id)
            added += 1
        await db.commit()

    insight = _extract_insight(venture_slug, all_findings)
    if not insight:
        return {"venture": venture_slug, "findings": added, "insight": None}

    async with AsyncSessionLocal() as db:
        ext_id = f"insight:{venture_slug}:{today}"
        existing_insight = (await db.execute(
            select(MemoryItem).where(MemoryItem.external_id == ext_id)
        )).scalar_one_or_none()
        content = (
            f"Daily insight for {config['name']} [{today}]: "
            f"{insight.get('insight')} "
            f"Proposed action: {insight.get('action')} "
            f"Type: {insight.get('action_type')} "
            f"Confidence: {insight.get('confidence', 0):.0%}"
        )
        if existing_insight:
            existing_insight.content = content
        else:
            db.add(MemoryItem(
                external_id=ext_id,
                summary=f"Insight [{config['name']}]: {insight.get('action', '')[:80]}",
                content=content,
                memory_type="episodic",
                category="empire",
                importance_score=0.85,
                tags=json.dumps([venture_slug, "insight", "action-pending"]),
            ))
        await db.commit()

    post_id = _post_mattermost(venture_slug, insight, added)

    if post_id:
        async with AsyncSessionLocal() as db:
            db.add(ResearchAction(
                venture_slug=venture_slug,
                mm_post_id=post_id,
                mm_channel_id=MM_CHANNEL,
                insight=insight.get("insight", ""),
                action=insight.get("action", ""),
                action_type=insight.get("action_type", "unknown"),
                confidence=float(insight.get("confidence", 0.5)),
            ))
            await db.commit()

    return {
        "venture": venture_slug,
        "queries": selected,
        "findings_raw": len(all_findings),
        "findings_stored": added,
        "insight": insight.get("action"),
        "mattermost": post_id is not None,
    }


@celery_app.task(name="app.tasks.research_tasks.research_cudan_studio")
def research_cudan_studio() -> dict:
    result = _run_async(_run_research("cudan-studio"))
    logger.info("research_cudan_studio", **{k: v for k, v in result.items() if k != "insight"})
    return result


@celery_app.task(name="app.tasks.research_tasks.research_bloom_bub")
def research_bloom_bub() -> dict:
    result = _run_async(_run_research("bloom-bub"))
    logger.info("research_bloom_bub", **{k: v for k, v in result.items() if k != "insight"})
    return result


@celery_app.task(name="app.tasks.research_tasks.research_gtt_perth")
def research_gtt_perth() -> dict:
    result = _run_async(_run_research("gtt-perth"))
    logger.info("research_gtt_perth", **{k: v for k, v in result.items() if k != "insight"})
    return result


def _post_action_draft(row) -> bool:
    """Post a copy-paste-ready draft reply once an action is approved.

    No live API execution — Etsy app isn't approved for resource endpoints yet
    (OAuth token exchange works, but listings/shop calls 403). Manual-apply only.
    """
    config = VENTURE_CONFIG.get(row.venture_slug, {})
    name = config.get("name", row.venture_slug)
    due = (row.reminder_due_at or datetime.now(tz=timezone.utc)).strftime("%Y-%m-%d")
    text = (
        f"### :white_check_mark: Approved — Ready to Apply ({name})\n\n"
        f"**Action:** {row.action}\n\n"
        f"**Type:** `{row.action_type}`\n\n"
        f"_Apply this manually — no live storefront/booking API is wired up yet. "
        f"Outcome check-in scheduled for {due}._"
    )
    try:
        r = httpx.post(
            f"{MM_BASE}/posts",
            headers=_mm_headers(),
            json={"channel_id": row.mm_channel_id, "message": text, "root_id": row.mm_post_id},
            timeout=10,
        )
        return r.status_code == 201
    except Exception as e:
        logger.warning("draft_post_failed", row_id=str(row.id), error=str(e))
        return False


async def _check_approvals() -> dict:
    from app.database import AsyncSessionLocal
    from app.models.research_action import ResearchAction, ActionStatus
    from sqlalchemy import select

    approved = 0
    rejected = 0
    checked = 0
    drafted = 0

    async with AsyncSessionLocal() as db:
        pending = (await db.execute(
            select(ResearchAction).where(ResearchAction.status == ActionStatus.PENDING)
        )).scalars().all()

        for row in pending:
            checked += 1
            try:
                r = httpx.get(
                    f"{MM_BASE}/posts/{row.mm_post_id}/reactions",
                    headers=_mm_headers(),
                    timeout=10,
                )
                if r.status_code != 200:
                    continue
                reactions = r.json() or []
                emojis = {reaction.get("emoji_name") for reaction in reactions}
            except Exception as e:
                logger.warning("reaction_check_failed", post_id=row.mm_post_id, error=str(e))
                continue

            now = datetime.now(tz=timezone.utc)
            if emojis & APPROVE_EMOJIS:
                row.status = ActionStatus.APPROVED
                row.decided_at = now
                row.reminder_due_at = now + timedelta(days=REMINDER_DELAY_DAYS)
                approved += 1
            elif emojis & REJECT_EMOJIS:
                row.status = ActionStatus.REJECTED
                row.decided_at = now
                rejected += 1

        await db.commit()

        # Phase 3: deliver a ready-to-apply draft for anything newly approved
        newly_approved = (await db.execute(
            select(ResearchAction).where(
                ResearchAction.status == ActionStatus.APPROVED,
                ResearchAction.draft_posted == False,  # noqa: E712
            )
        )).scalars().all()
        for row in newly_approved:
            if _post_action_draft(row):
                row.draft_posted = True
                drafted += 1
        await db.commit()

    return {"checked": checked, "approved": approved, "rejected": rejected, "drafted": drafted}


@celery_app.task(name="app.tasks.research_tasks.check_action_approvals")
def check_action_approvals() -> dict:
    result = _run_async(_check_approvals())
    logger.info("check_action_approvals", **result)
    return result


async def _send_reminders() -> dict:
    from app.database import AsyncSessionLocal
    from app.models.research_action import ResearchAction, ActionStatus
    from sqlalchemy import select

    now = datetime.now(tz=timezone.utc)
    sent = 0

    async with AsyncSessionLocal() as db:
        due = (await db.execute(
            select(ResearchAction).where(
                ResearchAction.status == ActionStatus.APPROVED,
                ResearchAction.reminder_sent == False,  # noqa: E712
                ResearchAction.reminder_due_at <= now,
            )
        )).scalars().all()

        for row in due:
            config = VENTURE_CONFIG.get(row.venture_slug, {})
            name = config.get("name", row.venture_slug)
            text = (
                f"### :hourglass: Outcome Check — {name}\n\n"
                f"14 days ago this action was approved: **{row.action}**\n\n"
                f"Did it get applied? What happened to the relevant metric "
                f"(sales, bookings, views)? Reply in this thread to close the loop."
            )
            try:
                r = httpx.post(
                    f"{MM_BASE}/posts",
                    headers=_mm_headers(),
                    json={
                        "channel_id": row.mm_channel_id,
                        "message": text,
                        "root_id": row.mm_post_id,
                    },
                    timeout=10,
                )
                if r.status_code == 201:
                    row.reminder_sent = True
                    sent += 1
            except Exception as e:
                logger.warning("reminder_post_failed", row_id=str(row.id), error=str(e))

        await db.commit()

    return {"reminders_sent": sent}


@celery_app.task(name="app.tasks.research_tasks.send_outcome_reminders")
def send_outcome_reminders() -> dict:
    result = _run_async(_send_reminders())
    logger.info("send_outcome_reminders", **result)
    return result
