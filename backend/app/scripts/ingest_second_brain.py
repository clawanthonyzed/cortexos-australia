"""Ingest second brain markdown files into CortexOS memory_items table."""
import asyncio, os, json, re
from pathlib import Path
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, text
from app.models.memory_item import MemoryItem, MemoryType

DATABASE_URL = os.getenv('DATABASE_URL')
SECOND_BRAIN_ROOT = '/opt/openclaw/second-brain'

CATEGORY_MAP = {
    'empire': 'empire',
    'agents': 'agents',
    'financial': 'financial',
    'feedback-loop': 'feedback',
    'decisions': 'decisions',
    'daily': 'daily',
    'emails': 'emails',
    'private': 'private',
    'raw': 'raw',
    'interviews': 'interviews',
    'interview-briefs': 'interviews',
}

def classify_type(path_str):
    for key in ('financial', 'private'):
        if key in path_str:
            return MemoryType.LONG_TERM
    for key in ('daily', 'emails', 'raw'):
        if key in path_str:
            return MemoryType.EPISODIC
    for key in ('feedback-loop', 'decisions'):
        if key in path_str:
            return MemoryType.PROCEDURAL
    return MemoryType.SEMANTIC

def get_category(path_str):
    for key, cat in CATEGORY_MAP.items():
        if ('/' + key + '/') in path_str or path_str.endswith('/' + key):
            return cat
    return 'general'

def extract_summary(content, max_len=200):
    lines = [l.strip() for l in content.split('\n') if l.strip() and not l.startswith('#')]
    if lines:
        return lines[0][:max_len]
    return content[:max_len]

async def ingest():
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    # Check existing external_ids to avoid duplicates
    async with async_session() as db:
        result = await db.execute(text("SELECT external_id FROM memory_items WHERE external_id IS NOT NULL"))
        existing_ids = {row[0] for row in result.fetchall()}

    md_files = list(Path(SECOND_BRAIN_ROOT).rglob('*.md'))
    print('Found ' + str(len(md_files)) + ' markdown files in second brain')

    batch = []
    skipped = 0
    for path in md_files:
        ext_id = 'sb:' + str(path.relative_to(SECOND_BRAIN_ROOT))
        if ext_id in existing_ids:
            skipped += 1
            continue
        try:
            content = path.read_text(encoding='utf-8', errors='replace')
        except Exception:
            continue
        if len(content.strip()) < 20:
            continue

        path_str = str(path)
        batch.append(MemoryItem(
            content=content[:8000],
            summary=extract_summary(content),
            memory_type=classify_type(path_str),
            category=get_category(path_str),
            tags=json.dumps(['second-brain', get_category(path_str)]),
            importance_score=0.7,
            external_id=ext_id,
        ))

        if len(batch) >= 50:
            async with async_session() as db:
                db.add_all(batch)
                await db.commit()
            print('  committed ' + str(len(batch)) + ' entries...')
            batch = []

    if batch:
        async with async_session() as db:
            db.add_all(batch)
            await db.commit()

    total = len(md_files) - skipped
    print('Ingested: ' + str(total) + ' entries (skipped ' + str(skipped) + ' existing)')

asyncio.run(ingest())
