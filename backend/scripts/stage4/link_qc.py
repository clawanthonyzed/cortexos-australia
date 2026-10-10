"""Link venture-scoped QC inspectors (WORKFORCE.md QC table) to their venture + manager."""
import re
import subprocess


def psql(sql, *args):
    cmd = ["docker", "exec", "-i", "cortexos-postgres-1", "sh", "-c",
           'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -v ON_ERROR_STOP=1 -At -F"|" ' +
           " ".join(f'-v a{i}="${i + 1}"' for i in range(len(args))), "sh", *args]
    r = subprocess.run(cmd, input=sql, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip())
    return [l.split("|") for l in r.stdout.strip().splitlines() if l]


norm = lambda s: re.sub(r"[^a-z0-9]", "", s.lower())
ventures = {norm(name): slug for slug, name in psql("select slug, name from ventures;")}
ventures.update({norm(slug): slug for slug in ventures.values()})

wf = open("/opt/openclaw/WORKFORCE.md", encoding="utf-8").read()
linked, skipped = 0, []
for agent, venture in re.findall(r"^\|\s*([a-z0-9-]+)\s*\|\s*QC Inspector\s*\|\s*(.+?) ONLY\s*\|", wf, re.M):
    slug = ventures.get(norm(venture))
    if not slug:
        skipped.append(f"{agent}->{venture}")
        continue
    n = psql("""update agents w set venture_id = v.id, reporting_manager_id = m.id, updated_at = now()
                from ventures v join agents m on lower(m.name) = lower(v.manager_name)
                where w.name = :'a0' and v.slug = :'a1' and w.id <> m.id
                  and (w.reporting_manager_id is null or w.venture_id is distinct from v.id)
                returning w.name;""", agent, slug)
    linked += len(n)
print("QC linked:", linked, "| no venture match:", skipped)
print(psql("select count(*) filter (where reporting_manager_id is not null), count(*) from agents where role_tier = 'worker';"))
