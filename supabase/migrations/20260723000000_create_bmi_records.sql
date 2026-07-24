create table if not exists public.bmi_records (
  id bigint generated always as identity primary key,
  height_cm double precision not null,
  weight_kg double precision not null,
  bmi double precision not null,
  category text not null,
  created_at timestamptz not null default now()
);

alter table public.bmi_records enable row level security;

create policy "Allow anonymous insert" on public.bmi_records
  for insert
  to anon
  with check (true);

create policy "Allow anonymous read" on public.bmi_records
  for select
  to anon
  using (true);
