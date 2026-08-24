-- VitalPeak — Fase 2
-- Pega esto en Supabase: SQL Editor → New query → Run

create table if not exists public.user_accounts (
  username text primary key,
  username_norm text not null unique,
  data jsonb not null default '{}'::jsonb,
  updated_at timestamptz not null default now()
);

create table if not exists public.password_resets (
  username text primary key references public.user_accounts(username) on delete cascade,
  token text not null,
  expires_at bigint not null
);

alter table public.user_accounts enable row level security;
alter table public.password_resets enable row level security;

-- La app Streamlit usa la service_role key (servidor). Esa clave salta RLS.
-- No hace falta política pública: nadie con la anon key puede leer cuentas.

comment on table public.user_accounts is 'Documento JSON por usuario (entrenos, rutinas, peso, perfil).';
