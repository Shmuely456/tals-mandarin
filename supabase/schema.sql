-- Tal's Mandarin sync server.
-- The browser only ever calls public.api(key, op, payload). Tables are closed to the public key (RLS on, no policies);
-- api() checks the private access key and the role behind it before reading or writing.

create table if not exists public.docs (
  collection text not null,
  id text not null,
  data jsonb not null default '{}'::jsonb,
  deleted boolean not null default false,
  updated_at timestamptz not null default now(),
  primary key (collection, id)
);
create index if not exists docs_updated_at on public.docs (updated_at);

create table if not exists public.access_keys (
  key text primary key,
  role text not null check (role in ('student', 'tutor')),
  label text,
  created_at timestamptz not null default now()
);

alter table public.docs enable row level security;
alter table public.access_keys enable row level security;
revoke all on public.docs, public.access_keys from anon, authenticated;

create or replace function public.api(k text, op text, payload jsonb default '{}'::jsonb)
returns jsonb
language plpgsql
security definer
set search_path = public
as $$
declare
  who text;
  c text := payload->>'collection';
  i text := payload->>'id';
  d jsonb := coalesce(payload->'data', '{}'::jsonb);
  since timestamptz := coalesce(nullif(payload->>'since', '')::timestamptz, 'epoch'::timestamptz);
  writable text[];
  rows jsonb;
begin
  select role into who from access_keys where key = k;
  if who is null then raise exception 'not allowed' using errcode = '42501'; end if;
  if op = 'pull' then
    select coalesce(jsonb_agg(jsonb_build_object('c', collection, 'id', id, 'data', data, 'deleted', deleted) order by updated_at), '[]'::jsonb)
      into rows from docs where updated_at > since;
    return jsonb_build_object('role', who, 'now', now(), 'docs', rows);
  end if;
  writable := case when who = 'student' then array['progress', 'sessions', 'homework', 'messages', 'items']
                   else array['messages', 'homework', 'items'] end;
  if c is null or i is null or length(i) > 200 or not (c = any(writable)) then
    raise exception 'not allowed' using errcode = '42501';
  end if;
  if pg_column_size(d) > 200000 then raise exception 'too large' using errcode = '54000'; end if;
  if op = 'put' then
    insert into docs (collection, id, data, deleted, updated_at) values (c, i, d, false, now())
      on conflict (collection, id) do update set data = excluded.data, deleted = false, updated_at = now();
  elsif op = 'patch' then
    update docs set data = data || d, updated_at = now() where collection = c and id = i and not deleted;
    if not found then raise exception 'missing' using errcode = 'P0002'; end if;
  elsif op = 'delete' then
    update docs set deleted = true, data = '{}'::jsonb, updated_at = now() where collection = c and id = i;
  else
    raise exception 'unknown op' using errcode = '22023';
  end if;
  return jsonb_build_object('ok', true, 'now', now());
end
$$;

revoke all on function public.api(text, text, jsonb) from public;
grant execute on function public.api(text, text, jsonb) to anon, authenticated;
