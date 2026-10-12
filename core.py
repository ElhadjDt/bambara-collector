"""Everything that touches audio, Supabase (Postgres) and Cloudflare R2.

Secrets come from Streamlit's secrets (see .streamlit/secrets.toml.example) and are only
used on the server side, so they are never sent to the visitor's browser.
"""
import io
import re
import unicodedata
import uuid

import boto3
import numpy as np
import psycopg
import soundfile as sf
import streamlit as st
from botocore.config import Config
from psycopg.rows import dict_row

SAMPLE_RATE = 24000       # record 24 kHz mono: good for TTS, easy to downsample to 16 kHz for ASR
STORE_FORMAT = "flac"     # "flac" = lossless, ~half the size of "wav" (change to "wav" if you prefer)
MAX_PER_PROMPT = 1        # recordings of one sentence before it leaves the pool (raise for more speakers)
MIN_SEC, MAX_SEC = 1.0, 30.0

SPEAKER_RE = re.compile(r"^[A-Z]{1,4}(19|20)\d{2}(0[1-9]|1[0-2])$")      # AT199503
SPECIAL_CHARS = ["ɛ", "ɔ", "ɲ", "ŋ", "Ɛ", "Ɔ", "Ɲ", "Ŋ"]                # Bambara letters missing on most keyboards


class UserError(Exception):
    """A problem the contributor can fix. `code` selects the translated message (err_<code>)."""

    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


# ------------------------------------------------------------------ connections
def db():
    return psycopg.connect(
        st.secrets["DATABASE_URL"], row_factory=dict_row, prepare_threshold=None, connect_timeout=10
    )


@st.cache_resource
def _s3():
    return boto3.client(
        "s3",
        endpoint_url=f"https://{st.secrets['R2_ACCOUNT_ID']}.r2.cloudflarestorage.com",
        aws_access_key_id=st.secrets["R2_ACCESS_KEY_ID"],
        aws_secret_access_key=st.secrets["R2_SECRET_ACCESS_KEY"],
        region_name="auto",
        config=Config(
            retries={"max_attempts": 3},
            request_checksum_calculation="when_required",   # R2 does not need the extra checksums
            response_checksum_validation="when_required",
        ),
    )


# ------------------------------------------------------------------ helpers
def clean(text: str) -> str:
    """Unicode-NFC normalise (one consistent form for accents) and collapse whitespace."""
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", text or "")).strip()


def prepare_audio(raw: bytes):
    """Validate the recording, force mono 16-bit, encode as FLAC/WAV. Returns (bytes, sample_rate, seconds)."""
    try:
        data, sr = sf.read(io.BytesIO(raw), dtype="int16", always_2d=True)
    except Exception:
        raise UserError("unreadable")
    if data.shape[1] > 1:
        data = data.mean(axis=1, keepdims=True).astype(np.int16)
    seconds = len(data) / sr
    if not MIN_SEC <= seconds <= MAX_SEC:
        raise UserError("duration")
    if int(np.abs(data.astype(np.int32)).max()) < 300:
        raise UserError("silent")
    buf = io.BytesIO()
    sf.write(buf, data, sr, format=STORE_FORMAT.upper(), subtype="PCM_16")
    return buf.getvalue(), sr, seconds


# ------------------------------------------------------------------ contributor actions
def next_prompt():
    """A random sentence that still needs recordings, or None."""
    with db() as conn:
        return conn.execute(
            "select id::text as id, bambara, french from prompts "
            "where recorded_count < %s order by random() limit 1",
            (MAX_PER_PROMPT,),
        ).fetchone()


def save_recording(audio: bytes, speaker_id: str, bambara: str, french: str = "", prompt_id: str | None = None):
    """Upload the audio to R2, then insert the row in Supabase. Raises UserError for fixable problems."""
    speaker = speaker_id.strip().upper()
    if not SPEAKER_RE.match(speaker):
        raise UserError("speaker")
    bambara, french = clean(bambara), clean(french)
    if not 2 <= len(bambara) <= 500 or len(french) > 500:
        raise UserError("text")
    payload, sample_rate, seconds = prepare_audio(audio)

    rec_id = uuid.uuid4()
    audio_name = f"audio_{speaker}_{rec_id}.{STORE_FORMAT}"    # audio_<speaker_id>_<uuid>.<ext>
    bucket = st.secrets["R2_BUCKET"]
    _s3().put_object(Bucket=bucket, Key=audio_name, Body=payload, ContentType=f"audio/{STORE_FORMAT}")
    try:
        with db() as conn:
            conn.execute(
                "insert into recordings (uuid, speaker_id, bambara, french, audio_name, "
                "duration_sec, sample_rate, prompt_id) values (%s,%s,%s,%s,%s,%s,%s,%s)",
                (rec_id, speaker, bambara, french or None, audio_name, round(seconds, 2), sample_rate,
                 uuid.UUID(prompt_id) if prompt_id else None),
            )
    except Exception:
        _s3().delete_object(Bucket=bucket, Key=audio_name)            # never leave an orphan audio file
        raise
    return seconds


@st.cache_data(ttl=60)
def get_stats():
    try:
        with db() as conn:
            rec = conn.execute(
                "select count(*) as recordings, coalesce(sum(duration_sec), 0) as seconds, "
                "count(distinct speaker_id) as speakers from recordings"
            ).fetchone()
            left = conn.execute(
                "select count(*) as n from prompts where recorded_count < %s", (MAX_PER_PROMPT,)
            ).fetchone()["n"]
        return {"recordings": rec["recordings"], "hours": float(rec["seconds"]) / 3600,
                "speakers": rec["speakers"], "left": left}
    except Exception:
        return None


# ------------------------------------------------------------------ admin actions
def add_prompts(rows: list[dict]):
    """Add Bambara/French pairs. Returns (received, inserted); existing Bambara sentences are skipped."""
    pairs = {}
    for r in rows:
        b = clean(r.get("bambara", ""))
        if 2 <= len(b) <= 500:
            pairs.setdefault(b, clean(r.get("french", "")))
    if not pairs:
        return len(rows), 0
    with db() as conn:
        cur = conn.execute(
            "insert into prompts (bambara, french) "
            "select * from unnest(%s::text[], %s::text[]) on conflict (bambara) do nothing",
            (list(pairs.keys()), list(pairs.values())),
        )
        return len(rows), cur.rowcount


def list_prompts(limit: int = 200):
    with db() as conn:
        items = conn.execute(
            "select bambara, french, recorded_count from prompts order by created_at desc limit %s",
            (limit,),
        ).fetchall()
        total = conn.execute("select count(*) as n from prompts").fetchone()["n"]
    return total, items
