# Human-in-the-Loop Publishing Shield (2026-10-10)

Anthony must approve all Cudan Studio and GTT Center Perth agent output before anything is posted or sent. Applied live to cortexos-postgres-1:

```sql

create or replace function hitl_publishing_shield() returns trigger language plpgsql as $$
begin
  if new.status = 'completed'
     and tg_op = 'UPDATE'
     and old.status in ('queued', 'running', 'retrying')
     and new.venture_id in (select id from ventures where slug in ('cudan-studio', 'gtt-perth')) then
    new.status := 'awaiting_approval';
    new.completed_at := null;
    if new.title not like 'DRAFT%' then
      new.title := left('DRAFT (needs Anthony sign-off) ' || new.title, 255);
    end if;
  end if;
  return new;
end $$;
drop trigger if exists hitl_publishing_shield on tasks;
create trigger hitl_publishing_shield before update on tasks for each row execute function hitl_publishing_shield();
```
