# Bambara voice + translation data collection (web only, French / English)

```
Streamlit Community Cloud  ──▶  Supabase Postgres   text, speaker ID, metadata   (free: 500 MB)
 (record + type Bambara/French)  └▶ Cloudflare R2      audio_<speaker_id>_<uuid>.flac  (free: 10 GB, no egress fees)
```

One Streamlit app talks directly to Supabase and R2. There is no separate API server, so there is nothing to wake up and one less thing to deploy. The secrets stay on Streamlit's server and are never sent to the visitor's browser.

| File | Role |
|---|---|
| `app.py` | Recording page: speaker ID, "read a sentence" / "say my own", mic, submit |
| `pages/1_Admin.py` | Add Bambara/French pairs (one, pasted, CSV); password protected |
| `core.py` | Audio validation, R2 upload, Supabase queries |
| `i18n.py` | All French and English texts + the language switch (sidebar) |
| `DEPLOY.md` | Step-by-step deployment and troubleshooting |
| `schema.sql` | Tables, auto-counter per sentence, row-level security |
| `export_dataset.py` | Builds a Hugging Face `audiofolder` dataset for training |

## Deploy
Follow **[DEPLOY.md](DEPLOY.md)**: exact steps for Supabase, Cloudflare R2, GitHub and Streamlit Community Cloud, a first-test checklist, an explanation of the sidebar numbers, and a troubleshooting table. In short: run `schema.sql` in Supabase, create a private R2 bucket and token, push this folder to GitHub, deploy `app.py` on Streamlit Community Cloud with Python 3.12 and the secrets from `.streamlit/secrets.toml.example`.

### Run locally
```bash
pip install -r requirements.txt
cp .streamlit/secrets.toml.example .streamlit/secrets.toml     # fill in real values
streamlit run app.py
```

## Data model
Each submitted recording is one row of `recordings`, identified by its own **uuid**:

| column | example | role |
|---|---|---|
| `uuid` | `3f2b…9a1c` | unique id of the entry (primary key, generated automatically) |
| `speaker_id` | `AT199503` | who spoke; used to filter voices |
| `bambara` | `I ka kɛnɛ wa?` | transcript (standard orthography, Unicode NFC) |
| `french` | `Comment vas-tu ?` | French equivalent (optional) |
| `audio_name` | `audio_AT199503_3f2b…9a1c.flac` | file name in R2 |

`audio_name` is always `audio_<speaker_id>_<uuid>.flac`, so an audio file and its transcription are matched by the uuid, and speakers are filtered with `speaker_id`:
```sql
select uuid, bambara, french, audio_name from recordings where speaker_id in ('AT199503', 'CD198507');
```
The same fields are written to `metadata.jsonl` by `export_dataset.py` (`--speaker AT199503 ...` keeps only those speakers).

## Behaviour
- **Language:** the switch is in the sidebar (French by default; change `DEFAULT_LANG` in `i18n.py`). What a contributor typed or selected is kept when they switch language. To change a text or add a language, edit `STR` in `i18n.py`.
- **Speaker ID:** initials + birth year + birth month, e.g. `AT199503`, checked in the page and again in `core.py`.
- **Two modes:** *read a sentence* takes a random pair; after `MAX_PER_PROMPT` recordings (default 1, in `core.py`) it leaves the pool. *Say my own sentence* is free Bambara text plus an optional French translation. Buttons add ɛ ɔ ɲ ŋ.
- **Audio:** recorded at 24 kHz mono, validated (1–30 s, not silent), stored as lossless FLAC (`STORE_FORMAT = "wav"` in `core.py` to keep WAV). If the database insert fails, the uploaded file is deleted.
- **Review:** every recording starts as `pending`. Set `status` to `validated` or `rejected` in the Supabase table editor after listening; rejected ones are skipped by the export.

**Capacity:** 24 kHz mono 16-bit is about 48 KB/s: roughly 58 h of raw WAV in 10 GB, and around 100 h as FLAC (typical, depends on the voices).

## Free-tier things to know (checked Oct 2026)
- **Supabase pauses a free project after 7 days without activity.** Your data is kept, but you must click *Restore* in the dashboard. During a collection campaign this will not happen. To prevent it between campaigns, add a weekly GitHub Actions job that runs `select 1` on your database (store `DATABASE_URL` as a GitHub secret).
- Streamlit Community Cloud apps can go to sleep when nobody visits; a visitor wakes them with one click.

## Get the dataset for training
```bash
pip install "psycopg[binary]" boto3
python export_dataset.py dataset          # reads .streamlit/secrets.toml
python export_dataset.py dataset --speaker AT199503 CD198507   # only some speakers
```
```python
from datasets import load_dataset
ds = load_dataset("audiofolder", data_dir="dataset")   # audio, uuid, speaker_id, transcription, french, ...
```
Resample to 16 kHz for ASR (Whisper, MMS, wav2vec2) and keep 24 kHz for TTS.

## Before collecting real data
Decide the dataset licence and write the consent text you want shown (the checkbox text is `consent` in `i18n.py`). Speaker IDs contain birth year and month, so say clearly how the data will be shared.
