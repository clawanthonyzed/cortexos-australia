"""Seed CortexOS memory with empire knowledge."""
import asyncio
import json
import sys
sys.path.insert(0, '/opt/cortexos/backend')

from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.memory_item import MemoryItem
from app.models.agent import Agent
from app.models.venture import Venture
from app.models.workflow import Workflow

EMPIRE_FACTS = [
    ("empire:entity:yeti-trust", "YETI Asset Holding Trust", "Empire wealth vehicle. ABN 39 225 792 867. Discretionary trust receives distributions from operating entities. Trustee: YETI Tipi Holdings PTY LTD (ACN 674 161 141). Completely separate from Cudan Studio.", "long_term", "financial", 1.0),
    ("empire:entity:cudan-pty", "Cudan Studio PTY LTD", "Primary operating company. ACN 677 490 032, ABN 40 677 490 032. ALL business revenue flows here — never to Anthony personally. Has TFN and GST registration. Located Kenwick WA. Monthly rent AUD 2400.", "long_term", "financial", 1.0),
    ("empire:entity:yeti-tipi", "YETI Tipi Holdings PTY LTD", "Corporate trustee of YETI Asset Holding Trust. ACN 674 161 141. NOT an operating entity — trustee role only. Not the same as Imara.", "long_term", "financial", 0.9),
    ("empire:target:revenue", "Empire Revenue Target AUD 50K/month", "Target: AUD 50000 per month by 2026-07-22 which is Empire Day 90. Day 1 was 2026-04-22. 42 active ventures across content, ecommerce, SaaS, services, and media categories. Current revenue is 0.", "long_term", "empire", 1.0),
    ("empire:fact:tpi-pension", "Anthony TPI Pension Rule", "Anthony receives a TPI/SRDP pension that is NOT means-tested. Business revenue MUST flow through Cudan Studio PTY LTD — never through Anthony's personal income. This preserves pension eligibility.", "long_term", "financial", 1.0),
    ("empire:fact:qc-standard", "Empire QC Standard 9.5/10", "Minimum quality score for all agent output: 9.5/10 (95 out of 100). Target 9.5/10. Flagship output 10/10. Any output below 9.5 is rejected and reworked. Zoe is QC Inspector for Bloom and Bub only.", "procedural", "empire", 0.9),
    ("empire:fact:imara", "Imara is Anthony's Partner", "Imara is Anthony's partner — a person, not a business entity. NOT the corporate trustee. The corporate trustee is YETI Tipi Holdings PTY LTD. Never confuse Imara with a corporate or financial role.", "long_term", "empire", 1.0),
    ("empire:fact:revenue-current", "Revenue Status Day 49", "Total revenue 0 per month at Empire Day 49. Sessions paused Day 42-49 for foundation sprint. Critical revenue path: Cudan Studio active bookings, then Bloom and Bub Gumroad listings, then YouTube trio first videos.", "episodic", "empire", 0.9),
    ("empire:blocker:instagram", "Instagram Blocks Harper and Neve", "Harper (Affiliate Empire) and Neve (Sage AI) are blocked until Anthony creates a personal Instagram account. Requires phone number. Alternative: Neve can pivot to Pinterest automatically.", "episodic", "empire", 0.8),
    ("empire:blocker:felix-gmail", "Felix Gmail OAuth Broken", "felix-gmail OAuth 400 error because refresh token was revoked. Fix: run gmail_reauth.py interactively on server. Anthony must visit the Google URL in a browser and paste the code back.", "episodic", "empire", 0.7),
    ("empire:infra:server", "Empire Server", "Primary server at root@46.250.244.248. Empire root at /opt/openclaw/. CortexOS at /opt/cortexos/. 329 agent files in /root/.claude/agents/. Registry rebuilt nightly by build_registry.py.", "long_term", "empire", 0.9),
    ("empire:infra:cortexos", "CortexOS Tech Stack", "FastAPI backend on port 8200. Next.js 14 frontend on port 3010. PostgreSQL with pgvector extension. Redis for cache and Celery broker. Docker Compose with Traefik. Live at dash.anthonyzed.work. GitHub repo: clawanthonyzed/business-idea-dash.", "long_term", "empire", 0.9),
    ("empire:infra:protocols", "Empire Protocol Ports", "MCP port 8600. A2A port 8400. ACP port 8500. ANP port 8700. AG-UI port 8800. All live on server as systemd services. Mattermost at dash.anthonyzed.work/chat port 8065. Plane at port 8090.", "long_term", "empire", 0.8),
    ("empire:rule:one-agent-per-venture", "Hard Rule: One Agent Per Venture", "Every named agent owns exactly one venture. Cross-venture assignment is forbidden. Cruz is Cudan Studio ONLY — never assign Cruz to KDP, Bloom and Bub, Sage AI, MapDrop, or any other venture. Check registry.json before assigning.", "procedural", "empire", 1.0),
    ("empire:rule:new-agent-workforce", "New Agent Must Update WORKFORCE.md", "When any agent creates a new agent .md file: (1) add entry to /opt/openclaw/WORKFORCE.md under correct section, (2) post to Mattermost #new-hires channel, (3) build_registry.py catches misses nightly as backup.", "procedural", "empire", 0.9),
    ("empire:fact:platforms", "Empire Sales Platforms", "Digital products sell via Gumroad, LemonSqueezy, and Etsy. Studio bookings direct via Cudan Studio website. Publishing via Amazon KDP. Music distribution via Distrokid. Video content on YouTube, Instagram, Pinterest.", "long_term", "empire", 0.8),
    ("empire:fact:youtube-channels", "Empire YouTube Trio", "Three YouTube channels: The Footnote (history and culture, managed by Callum), Ambient Escapes (relaxation soundscapes, managed by Murray), Scroll and Stone (ancient history, managed by Levi). All three have workers deployed and YouTube API connected.", "episodic", "empire", 0.8),
    ("empire:fact:einstein-gate", "Einstein Credit Gatekeeper", "Einstein approves ALL credit-burning tool use. Send EINSTEIN REQUEST before using: RunPod, HeyGen, Ideogram, KLING, Higgsfield, PDFMonkey, OpenAI API, Apify. Leonardo is free tier 150 credits per day — no Einstein gate needed.", "procedural", "empire", 0.9),
    ("empire:fact:github", "Empire GitHub", "GitHub org: clawanthonyzed. Main dashboard repo: business-idea-dash (also CortexOS repo). Each venture has its own repo. business-idea-dash is CortexOS ONLY — never use it for venture files.", "procedural", "empire", 0.8),
    ("empire:fact:workforce", "WORKFORCE.md Location", "WORKFORCE.md at /opt/openclaw/WORKFORCE.md and mirrored on GitHub at clawanthonyzed/business-idea-dash/WORKFORCE.md. Contains all 329 agents across 42 ventures. Auto-synced. All agents must read before operating.", "long_term", "empire", 0.9),
]

VENTURE_NOTES = {
    "cudan-studio": "Physical photography and content creation studio in Kenwick WA. Monthly rent AUD 2400. Currently running at a loss with active bookings. Critical priority. Workers: Jordan (SEO/GBP), Kira (social media), Maya (copywriter). Squarespace website needs update via changelist.",
    "bloom-bub": "Premium baby and maternity digital products brand. Products: Pregnancy Journal, Milestone Cards, Cheat Sheet, Welcome Baby Book, Complete Collection. Platforms: Gumroad and Etsy. Five products pending listing — direct revenue path. Critical priority.",
    "the-footnote": "History and culture YouTube channel managed by Callum. Long-form educational content. First video target 7 days after launch. YouTube API connected.",
    "ambient-escapes": "Ambient relaxation YouTube channel managed by Murray. Soundscapes and visual escapes. First video target 3 days after launch.",
    "scroll-and-stone": "Ancient history and archaeology YouTube channel managed by Levi. First video target 7 days after launch.",
    "sage-ai": "AI-generated short-form video content brand. Neve manages overall, Sol handles video production. Blocked on Instagram account creation. Alternative is Pinterest pivot.",
    "lo-fi-engine": "Lo-fi music production and distribution managed by Kai. Overnight pipeline paused for 522 hours. Distributes via Distrokid to all streaming platforms.",
    "affiliate-empire": "Affiliate marketing and newsletter empire managed by Harper. Weekly newsletter plus DM funnels. Blocked on Instagram. Uses Resend for email and n8n for automation.",
    "handwritten-book": "Handwritten and illustrated book publishing via Amazon KDP. Managed by Wren. In progress phase.",
    "kdp-colouring-books": "KDP colouring book publishing managed by Atlas. World Cup 2026 themed books. Uses Leonardo AI free tier (150 credits per day, no Einstein gate).",
    "mapdrop": "City map poster business — PDF and print-on-demand. Manager: Remy. Geo renders maps. Lena manages listings. Target AUD 3000 per month by Day 90. Platforms: Etsy and Redbubble.",
    "dva-navigator": "DVA Department of Veterans Affairs navigation service for veterans. Managed by Cipher. Legal accuracy is critical.",
    "wantsyoutoknow": "Viral social media content brand managed by Ellis. Platforms: TikTok, Instagram, YouTube Shorts.",
    "agentic-os": "CortexOS the empire Agentic OS platform. Orbit manages backend, Helix manages frontend. Stack: FastAPI, Next.js, PostgreSQL, Docker Compose. Live at dash.anthonyzed.work.",
    "prediction-pulse": "Prediction market newsletter managed by Quant. Currently blocked on billing.",
    "polymarket-tracker": "Polymarket prediction market trading signals managed by Quant.",
    "meal-plan-cart": "Meal planning digital products managed by Bondi. Gumroad and Etsy.",
    "weekly-wonder": "Weekly Wonder email newsletter managed by Wonder.",
    "ai-mentor": "AI coaching and mentorship platform managed by Mentor.",
    "mapdrop": "City map posters print-on-demand. Manager Remy. Workers: Geo (renderer), Lena (listings). Target AUD 3K/month Day 90.",
    "affiliate-empire": "Affiliate marketing and newsletters. Manager Harper. Resend + n8n. Blocked on Instagram.",
}


async def main():
    async with AsyncSessionLocal() as db:
        existing = set(
            (await db.execute(select(MemoryItem.external_id).where(MemoryItem.external_id.isnot(None)))).scalars().all()
        )
        print(f"Existing external_ids: {len(existing)}")
        added = 0

        # 1. Empire strategic facts
        for ext_id, summary, content, mtype, cat, score in EMPIRE_FACTS:
            if ext_id not in existing:
                db.add(MemoryItem(
                    external_id=ext_id, summary=summary, content=content,
                    memory_type=mtype, category=cat, importance_score=score,
                    tags='["empire","structured"]'
                ))
                added += 1

        # 2. Venture facts
        ventures = (await db.execute(select(Venture))).scalars().all()
        for v in ventures:
            ext_id = f"venture:fact:{v.slug}"
            if ext_id not in existing:
                note = VENTURE_NOTES.get(v.slug, "")
                content = f"{v.name} — Category: {v.category}. Manager: {v.manager_name}. Slug: {v.slug}. {note}"
                db.add(MemoryItem(
                    external_id=ext_id, summary=f"Venture: {v.name}",
                    content=content, memory_type="long_term", category="ventures",
                    importance_score=0.8, tags=f'["{v.slug}", "venture"]'
                ))
                added += 1

        # 3. Agent purpose memories
        agents = (await db.execute(select(Agent))).scalars().all()
        for a in agents:
            ext_id = f"agent:purpose:{a.name}"
            if ext_id not in existing and a.purpose:
                raw = a.tags or "[]"
                try:
                    t = json.loads(raw) if isinstance(raw, str) else raw
                    venture_ctx = t[0] if isinstance(t, list) and t else (raw.strip() if raw != "[]" else "specialist")
                except Exception:
                    venture_ctx = raw.strip() if raw and raw != "[]" else "specialist"
                content = (
                    f"{a.name} ({a.model_name}) — {a.purpose[:400]} "
                    f"Venture assignment: {venture_ctx}. Status: {a.status}."
                )
                db.add(MemoryItem(
                    external_id=ext_id, summary=f"Agent: {a.name}",
                    content=content, memory_type="semantic", category="agents",
                    importance_score=0.7, tags=f'["{a.name}", "{venture_ctx}"]'
                ))
                added += 1

        # 4. Workflow memories
        workflows = (await db.execute(select(Workflow))).scalars().all()
        for wf in workflows:
            ext_id = f"workflow:fact:{wf.id}"
            if ext_id not in existing:
                v = wf.venture or "empire"
                desc = wf.description or "No description"
                content = (
                    f"Workflow: {wf.name}. {desc}. Venture: {v}. "
                    f"Status: {wf.status}. Trigger: {wf.trigger_type}. "
                    f"Run count: {wf.run_count}."
                )
                db.add(MemoryItem(
                    external_id=ext_id, summary=f"Workflow: {wf.name}",
                    content=content, memory_type="procedural", category="workflows",
                    importance_score=0.75, tags=f'["workflow", "{v}"]'
                ))
                added += 1

        await db.commit()
        print(f"Added: {added} new memory items")

        total = (await db.execute(select(MemoryItem))).scalars().all()
        print(f"Total memory items: {len(total)}")


asyncio.run(main())
