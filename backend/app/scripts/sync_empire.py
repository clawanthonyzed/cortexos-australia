"""Sync empire ventures + agents from WORKFORCE.md and registry.json into CortexOS DB."""
import asyncio, os, uuid, re, json
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from app.models.venture import Venture
from app.models.agent import Agent

DATABASE_URL = os.getenv('DATABASE_URL')

VENTURES = [
    ('bloom-bub', 'Bloom & Bub', 'maren'),
    ('affiliate-empire', 'Affiliate Empire', 'harper'),
    ('cudan-studio', 'Cudan Studio', 'cruz'),
    ('sage-ai', 'Sage AI', 'neve'),
    ('handwritten-book', 'Handwritten Book', 'wren'),
    ('the-footnote', 'The Footnote', 'callum'),
    ('lo-fi-engine', 'Lo-Fi Engine', 'kai'),
    ('boomer-and-roo', 'Boomer & Roo', None),
    ('scroll-and-stone', 'Scroll & Stone', 'levi'),
    ('dva-navigator', 'DVA Navigator', None),
    ('niche-digital', 'Niche Digital', None),
    ('trend-clothing', 'Trend Clothing', None),
    ('zara-marin', 'Zara Marin', None),
    ('polymarket-tracker', 'Polymarket Tracker', 'quant'),
    ('prediction-pulse', 'Prediction Pulse', 'quant'),
    ('print-shop', 'Print Shop', None),
    ('heartfelt-social', 'Heartfelt Social', None),
    ('kidsmilestones', 'KidsMilestones', None),
    ('maternity-aid', 'Maternity Aid', None),
    ('affirmplus', 'AffirmPlus', None),
    ('open-agents', 'Open Agents Platform', None),
    ('studymate-ai', 'StudyMate AI', None),
    ('wantsyoutoknow', 'wantsyoutoknow', 'ellis'),
    ('cv-match-pro', 'CV Match Pro', None),
    ('amazon-reseller', 'Amazon Reseller', None),
    ('meal-plan-cart', 'Meal Plan Cart', 'bondi'),
    ('custom-sandals', 'Custom Sandals', None),
    ('domain-flipping', 'Domain Flipping', 'scout'),
    ('skill-forge', 'Skill Forge', None),
    ('ai-mentor', 'AI Mentor', None),
    ('ai-chat-character', 'AI Chat Character', None),
    ('red-pill-ai', 'Red Pill AI', None),
    ('plastics-scanner', 'Plastics Scanner', None),
    ('security-audit', 'Security Audit', None),
    ('ambient-escapes', 'Ambient Escapes', 'murray'),
    ('weekly-wonder', 'Weekly Wonder', 'wonder'),
    ('mapdrop', 'MapDrop', 'remy'),
    ('kdp-colouring-books', 'KDP Colouring Books', 'atlas'),
    ('income-sprint', 'Income Sprint', None),
    ('agentic-os', 'Agentic OS', 'orbit'),
    ('stylematch', 'StyleMatch', None),
    ('personal-finance-dashboard', 'Personal Finance Dashboard', None),
]

async def sync():
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as db:
        venture_id_map = {}
        print('Syncing ventures...')
        for slug, name, manager_name in VENTURES:
            result = await db.execute(select(Venture).where(Venture.slug == slug))
            existing = result.scalar_one_or_none()
            if existing:
                venture_id_map[slug] = existing.id
                continue
            v = Venture(slug=slug, name=name, manager_name=manager_name or 'tbd', category='empire')
            db.add(v)
            await db.flush()
            await db.refresh(v)
            venture_id_map[slug] = v.id
            print('  + venture: ' + name)
        await db.commit()
        print('Ventures done: ' + str(len(VENTURES)))

        print('Syncing agents from registry...')
        with open('/opt/openclaw/orchestration/registry.json') as f:
            registry = json.load(f)
        agents_data = registry.get('agents', [])
        created = 0
        for agent_data in agents_data:
            name = agent_data.get('name', '')
            if not name:
                continue
            result = await db.execute(select(Agent).where(Agent.name == name))
            if result.scalar_one_or_none():
                continue
            venture_slug = agent_data.get('venture', '')
            is_specialist = agent_data.get('is_specialist', False) or venture_slug in ('specialist', '')
            venture_id = venture_id_map.get(venture_slug) if not is_specialist else None
            model = agent_data.get('model', 'sonnet')
            agent = Agent(
                name=name,
                purpose=(agent_data.get('description') or (name + ' agent'))[:500],
                description=agent_data.get('description', ''),
                model_provider='claude',
                model_name='claude-' + model,
                status='idle',
                agent_type='specialist' if is_specialist else 'venture',
                tags=venture_slug or 'specialist',
                venture_id=venture_id,
            )
            db.add(agent)
            created += 1
        await db.commit()
        print('Agents synced: ' + str(created) + ' new')

asyncio.run(sync())
