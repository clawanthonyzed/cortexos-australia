"""Give every EmpireOS workflow a real step-by-step graph (2026-10-10).

Fills the 6 workflows that had an empty graph ({}) and adds the 2 new assembly lines
Anthony asked for (Content Production, B2B Lead Audit). Domain Arbitrage = the existing
"Domain Flip Scanner" workflow. Every agent named below exists in the agents table and
belongs to that workflow's venture (checked against WORKFORCE.md). Workflows that already
have a graph are not touched. New ones are created as 'draft' so nothing runs by itself.
"""
import json
import subprocess

# (label, agent or None, kind) ; kind: agent | condition ; condition = QC gate with pass/fail
FLOWS = {
    "Domain Flip Scanner": ("domain-flipping", "Domain Arbitrage: dropped list to listing draft", [
        ("Scrape dropped-domain list", "domain-research-analyst", "agent", "Pull today's expiring/dropped .com and .com.au lists; keep brandable names under 15 characters"),
        ("Valuation & scoring", "research-scout", "agent", "Score each name on comparable sales, search volume and resale ceiling; shortlist the top 10"),
        ("QC review (9.5/10)", "quest", "condition", "Shortlist scores 9.5+ on the Domain Flipping QC rubric"),
        ("Listing draft", "domain-listing-and-sales-manager", "agent", "Draft marketplace listings (price, pitch, buyer profile) for approved names"),
        ("Flipper approves purchases", "flipper", "agent", "Flipper presents the final list to Anthony; no domain is bought without his approval"),
    ]),
    "KDP Book Pipeline": ("kdp-colouring-books", "Niche to published colouring book", [
        ("Niche + keyword research", "scout", "agent", "Helium 10 niche and keyword research for the next title"),
        ("40 page descriptions", "quill", "agent", "Write 40 page descriptions for the chosen theme"),
        ("Generate line art", "brush", "agent", "Leonardo AI line art, 300 DPI (free tier, 150 credits/day)"),
        ("QC: lines, repeats, bleed (9.5/10)", "draw", "condition", "Closed lines, no near-duplicates, KDP bleed spec"),
        ("Assemble PDF", "press", "agent", "KDP interior 8.5x11 + printable A4/Letter PDF"),
        ("Listing copy", "herald", "agent", "Titles, keywords and descriptions for KDP, Etsy, Gumroad"),
    ]),
    "Sage AI Video Pipeline": ("sage-ai", "Topic to published Sage AI video", [
        ("Topic + script", "sage-content-creator", "agent", "Pick a topic from research-neve and write the script"),
        ("Visual identity frames", "brand-visual-designer", "agent", "On-brand thumbnails and scene visuals"),
        ("Produce video (Einstein gate)", "sol", "agent", "Render the video; paid tools only after an Einstein approval"),
        ("Neve QC review", "neve", "condition", "Brand, accuracy and hook strength pass"),
        ("Affiliate links + publish", "affiliate-research-manager", "agent", "Attach relevant affiliate links and publish"),
    ]),
    "MapDrop City Generator": ("mapdrop", "City to listed map poster", [
        ("Pick city + render map", "geo", "agent", "Render the city poster from OpenStreetMap (maptoposter pipeline)"),
        ("QC: print-ready (9.5/10)", "pin", "condition", "300 DPI, legible labels, no clipped coastlines"),
        ("SEO keywords", "seo-worker", "agent", "Keyword set for the city (MapDrop context injected)"),
        ("Write listings", "lena", "agent", "Etsy / Gumroad / LemonSqueezy listing copy"),
        ("Remy approves + publishes", "remy", "agent", "Final approval and publish"),
    ]),
    "Affiliate Newsletter Loop": ("affiliate-empire", "Offer research to sent newsletter", [
        ("Find offers", "affiliate-program-manager", "agent", "Shortlist 3 affiliate offers with real commission terms"),
        ("Research angle", "research-harper", "agent", "Audience pain points and proof for each offer"),
        ("Write issue", "content-creator", "agent", "Draft the newsletter issue around one hero offer"),
        ("QC (9.5/10)", "qc-affiliate-empire", "condition", "Accuracy, disclosure, no hype claims"),
        ("Send + track", "analytics-and-optimisation-specialist", "agent", "Send via Resend, track clicks and conversions"),
    ]),
    "Lo-Fi Track Release": ("lo-fi-engine", "Trend to released lo-fi track", [
        ("Trend research", "research-kai", "agent", "Find the mood/tempo currently trending in lo-fi"),
        ("Produce track", "music-production-specialist", "agent", "Produce and master the track"),
        ("Kai QC listen", "kai", "condition", "Mix quality and brand fit"),
        ("Distribute + license", "music-distribution-and-licensing-manager", "agent", "Distribute to streaming platforms, register licensing"),
        ("YouTube upload", "youtube-channel-manager", "agent", "Upload with artwork, title and description"),
    ]),
}
NEW_FLOWS = {
    "Content Production Line (The Footnote)": ("the-footnote", "Keyword research to published long-form content", [
        ("Keyword research", "channel-growth-strategist", "agent", "YouTube SEO: pick the topic with demand and a gap"),
        ("Research + script", "script-writer", "agent", "Historical narrative script with sources"),
        ("QC score (9.5/10)", "slate", "condition", "Accuracy, sourcing, retention hooks"),
        ("Format + push", "callum", "agent", "Final formatting, title/description, push to the channel queue"),
    ]),
    "B2B Lead Audit (Security Audit)": ("security-audit", "Local business list to outbound-ready audit", [
        ("Scrape local businesses", "research-vault", "agent", "Perth small businesses with public websites (public data only)"),
        ("Website / SEO audit", "penetration-testing-specialist", "agent", "Passive, non-intrusive checks only: TLS, headers, outdated CMS, SEO basics. No active testing without written consent"),
        ("Write audit report", "security-report-writer", "agent", "One-page plain-English findings per business"),
        ("QC (9.5/10)", "guard", "condition", "Accurate, non-alarmist, no false positives"),
        ("Outbound prep", "vault", "agent", "Personalised outreach draft per business; Anthony approves before anything is sent"),
    ]),
}


def psql(sql, *args):
    cmd = ["docker", "exec", "-i", "cortexos-postgres-1", "sh", "-c",
           'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -v ON_ERROR_STOP=1 -At -F"|" ' +
           " ".join(f'-v a{i}="${i + 1}"' for i in range(len(args))), "sh", *args]
    r = subprocess.run(cmd, input=sql, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip())
    return [l.split("|") for l in r.stdout.strip().splitlines() if l]


known = {r[0] for r in psql("select name from agents;")}


def build(steps):
    nodes, edges, rows = [], [], []
    y = 50
    for i, (label, agent, kind, task) in enumerate(steps, start=1):
        if agent and agent not in known:
            raise SystemExit(f"unknown agent {agent}")
        nid = f"n{i}"
        title = f"{agent}: {label}" if kind == "agent" else label
        nodes.append({"id": nid, "type": kind, "position": {"x": 250, "y": y},
                      "data": {"label": title, "agent": agent, "nodeType": kind, "task": task}})
        if i > 1:
            prev = steps[i - 2]
            edges.append({"id": f"e{i-1}-{i}", "source": f"n{i-1}", "target": nid,
                          **({"label": "pass"} if prev[2] == "condition" else {})})
        cfg = {"agent": agent, "task": task} if kind == "agent" else {"condition": task, "qc_agent": agent, "on_pass": f"n{i+1}", "on_fail": f"n{i-1}"}
        rows.append((i - 1, nid, label, "agent_node" if kind == "agent" else "condition_node", json.dumps(cfg)))
        y += 130
    # QC fail loops back to the step before the gate
    for i, (_, agent, kind, _) in enumerate(steps, start=1):
        if kind == "condition" and i > 1:
            edges.append({"id": f"e{i}-{i-1}-fail", "source": f"n{i}", "target": f"n{i-1}", "label": "fail: rework"})
    return {"nodes": nodes, "edges": edges}, rows


def save(name, venture, desc, steps, create):
    graph, rows = build(steps)
    if create:
        if psql("select count(*) from workflows where name = :'a0';", name)[0][0] != "0":
            return f"{name}: exists, skipped"
        wid = psql("insert into workflows (name, description, graph_json, status, venture, tags) values "
                   "(:'a0', :'a1', :'a2', 'draft', :'a3', :'a4') returning id;",
                   name, desc, json.dumps(graph), venture, json.dumps([venture, "assembly-line"]))[0][0]
    else:
        row = psql("select id, length(graph_json) from workflows where name = :'a0';", name)[0]
        if int(row[1]) > 10:
            return f"{name}: already has a graph, untouched"
        wid = row[0]
        psql("update workflows set graph_json = :'a1', description = coalesce(nullif(description, ''), :'a2'), updated_at = now() "
             "where id = :'a0';", wid, json.dumps(graph), desc)
    psql("delete from workflow_steps where workflow_id = :'a0';", wid)  # only ever empty for these workflows
    for order, nid, label, stype, cfg in rows:
        psql('insert into workflow_steps (workflow_id, name, step_type, config_json, "order", node_id) '
             "values (:'a0', :'a1', :'a2', :'a3', :'a4', :'a5');", wid, label, stype, cfg, str(order), nid)
    return f"{name}: {len(rows)} steps, agents {sorted({s[1] for s in steps})}"


for name, (venture, desc, steps) in FLOWS.items():
    print(save(name, venture, desc, steps, create=False))
for name, (venture, desc, steps) in NEW_FLOWS.items():
    print(save(name, venture, desc, steps, create=True))
print(psql("select count(*), count(*) filter (where length(graph_json) > 10) from workflows;"))
