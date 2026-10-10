"""Populate knowledge graph episodes from agent .md files and WORKFORCE.md."""
import asyncio, os, re, json
from pathlib import Path
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, text
from app.models.memory_item import MemoryItem, MemoryType

DATABASE_URL = os.getenv('DATABASE_URL')
AGENTS_DIR = '/root/.claude/agents'
WORKFORCE_PATH = '/opt/openclaw/WORKFORCE.md'

def parse_agent_md(path):
    """Extract name, venture, description, tools from agent .md frontmatter."""
    try:
        content = path.read_text(encoding='utf-8', errors='replace')
    except Exception:
        return None
    name = path.stem
    venture = None
    description = ''
    tools = ''
    # Parse frontmatter
    fm_match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
    if fm_match:
        fm = fm_match.group(1)
        for line in fm.split('\n'):
            if line.startswith('description:'):
                description = line.split(':', 1)[1].strip().strip('"')
            if line.startswith('tools:'):
                tools = line.split(':', 1)[1].strip()
    # Extract venture from body
    venture_match = re.search(r'venture[:\s]+([a-z-]+)', content, re.IGNORECASE)
    if venture_match:
        venture = venture_match.group(1).lower()
    # Build observation text
    obs = f'Agent: {name}. '
    if description:
        obs += description[:300] + ' '
    if venture and venture not in ('specialist', ''):
        obs += f'Venture: {venture}. '
    if tools:
        obs += f'Tools: {tools}.'
    return {
        'name': name,
        'venture': venture,
        'description': description,
        'observation': obs,
        'external_id': 'kg:agent:' + name,
    }

async def populate():
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    # Get existing external_ids
    async with async_session() as db:
        result = await db.execute(text("SELECT external_id FROM memory_items WHERE external_id LIKE 'kg:%'"))
        existing = {row[0] for row in result.fetchall()}

    agent_files = list(Path(AGENTS_DIR).glob('*.md'))
    print('Agent files found: ' + str(len(agent_files)))

    batch = []
    for path in agent_files:
        data = parse_agent_md(path)
        if not data or not data['observation'].strip():
            continue
        ext_id = data['external_id']
        if ext_id in existing:
            continue
        batch.append(MemoryItem(
            content=data['observation'],
            summary=data['description'][:200] if data['description'] else data['name'],
            memory_type=MemoryType.SEMANTIC,
            category='knowledge-graph',
            tags=json.dumps(['agent', 'entity', data.get('venture') or 'specialist']),
            importance_score=0.8,
            external_id=ext_id,
        ))

    # Also add venture entities from WORKFORCE.md
    try:
        wf_content = Path(WORKFORCE_PATH).read_text(encoding='utf-8', errors='replace')
        venture_matches = re.findall(r'^### \d+\. (.+)$', wf_content, re.MULTILINE)
        for venture_name in venture_matches:
            ext_id = 'kg:venture:' + venture_name.lower().replace(' ', '-').replace('&', 'and')
            if ext_id in existing:
                continue
            batch.append(MemoryItem(
                content=f'Venture: {venture_name}. Part of Anthony Zed empire. Target: revenue generation.',
                summary=f'Empire venture: {venture_name}',
                memory_type=MemoryType.SEMANTIC,
                category='knowledge-graph',
                tags=json.dumps(['venture', 'entity', 'empire']),
                importance_score=0.9,
                external_id=ext_id,
            ))
        print('Ventures from WORKFORCE.md: ' + str(len(venture_matches)))
    except Exception as e:
        print('WORKFORCE.md error: ' + str(e))

    if batch:
        async with async_session() as db:
            db.add_all(batch)
            await db.commit()
    print('Knowledge graph populated: ' + str(len(batch)) + ' entities')

asyncio.run(populate())
