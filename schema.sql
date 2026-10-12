-- Run once in Supabase -> SQL Editor.

-- Sentence pairs (Bambara + French) that contributors can read aloud.
create table if not exists prompts (
  id             uuid primary key default gen_random_uuid(),
  bambara        text not null,
  french         text,
  recorded_count int  not null default 0,
  created_at     timestamptz not null default now(),
  unique (bambara)
);

-- One row per submitted recording (the audio file itself lives in Cloudflare R2).
-- Matching rule:  audio_name = 'audio_' || speaker_id || '_' || uuid || '.flac'
-- so any audio file can be joined to its transcription through the uuid, and
-- any set of speakers can be selected with  where speaker_id in (...).
create table if not exists recordings (
  uuid         uuid primary key default gen_random_uuid(),   -- unique id of this entry
  speaker_id   text not null,                                -- e.g. AT199503 (filter voices with it)
  bambara      text not null,                                -- transcript, standard Bambara orthography
  french       text,                                         -- French equivalent
  audio_name   text not null unique,                         -- audio_AT199503_<uuid>.flac (file name in R2)
  duration_sec real not null,
  sample_rate  int  not null,
  prompt_id    uuid references prompts(id) on delete set null,
  status       text not null default 'pending'
               check (status in ('pending', 'validated', 'rejected')),
  created_at   timestamptz not null default now()
);
create index if not exists recordings_speaker_idx on recordings (speaker_id);
create index if not exists recordings_prompt_idx  on recordings (prompt_id);

-- Each recording of a prompt bumps its counter automatically (no race conditions).
create or replace function bump_prompt_count() returns trigger
language plpgsql as $$
begin
  if new.prompt_id is not null then
    update prompts set recorded_count = recorded_count + 1 where id = new.prompt_id;
  end if;
  return new;
end $$;

drop trigger if exists recordings_bump_prompt on recordings;
create trigger recordings_bump_prompt after insert on recordings
  for each row execute function bump_prompt_count();

-- Block Supabase's public REST API from touching these tables.
-- Our FastAPI backend connects directly as the postgres role, which bypasses RLS.
alter table prompts    enable row level security;
alter table recordings enable row level security;
