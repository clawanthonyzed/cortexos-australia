# Stage 4 (2026-10-10) one-off DB scripts

Already applied to production. Kept as a record of what changed in the database:

- mem_trigger.sql: memory_items BEFORE INSERT trigger (agent/venture attribution)
- mem_backfill.sql: one-off attribution of existing memories
- seed_workflows.py: real step graphs for 8 workflows
- seed_tasks.sql: 4 priority-venture tasks
- link_workers.sql, link_qc.py, fix_research.sql: org-chart reporting lines and venture tags
