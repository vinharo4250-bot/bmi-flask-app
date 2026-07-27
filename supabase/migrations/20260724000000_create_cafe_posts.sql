create table if not exists public.cafe_posts (
  id bigint generated always as identity primary key,
  company text not null,
  title text not null,
  url text not null,
  run_at timestamptz not null,
  created_at timestamptz not null default now()
);

create index if not exists cafe_posts_run_at_idx on public.cafe_posts (run_at desc);

alter table public.cafe_posts enable row level security;

create policy "Allow anonymous read" on public.cafe_posts
  for select
  to anon
  using (true);
