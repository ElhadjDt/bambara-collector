"""Download recordings from R2 and write a Hugging Face "audiofolder" dataset.

Run from the project folder (reads .streamlit/secrets.toml, or the same names as env vars):
    pip install "psycopg[binary]" boto3
    python export_dataset.py                            # everything -> ./dataset
    python export_dataset.py out_dir                    # custom output folder
    python export_dataset.py --speaker AT199503 CD198507   # only these speakers

Every audio file is audio_<speaker_id>_<uuid>.flac and metadata.jsonl carries the same uuid,
so audio and transcription always match. Then:
    from datasets import load_dataset
    ds = load_dataset("audiofolder", data_dir="dataset")
"""
import argparse
import json
import os
import tomllib
from pathlib import Path

import boto3
import psycopg
from botocore.config import Config
from psycopg.rows import dict_row

ap = argparse.ArgumentParser()
ap.add_argument("out", nargs="?", default="dataset", help="output folder")
ap.add_argument("--speaker", nargs="+", metavar="ID", help="keep only these speaker IDs")
args = ap.parse_args()

secrets = Path(".streamlit/secrets.toml")
cfg = tomllib.loads(secrets.read_text(encoding="utf-8")) if secrets.exists() else dict(os.environ)

out = Path(args.out)
(out / "audio").mkdir(parents=True, exist_ok=True)

s3 = boto3.client(
    "s3",
    endpoint_url=f"https://{cfg['R2_ACCOUNT_ID']}.r2.cloudflarestorage.com",
    aws_access_key_id=cfg["R2_ACCESS_KEY_ID"],
    aws_secret_access_key=cfg["R2_SECRET_ACCESS_KEY"],
    region_name="auto",
    config=Config(request_checksum_calculation="when_required", response_checksum_validation="when_required"),
)

query = (
    "select uuid::text as uuid, speaker_id, bambara, french, audio_name, duration_sec, sample_rate "
    "from recordings where status <> 'rejected'"
)
params: list = []
if args.speaker:
    query += " and speaker_id = any(%s)"
    params.append([s.upper() for s in args.speaker])
with psycopg.connect(cfg["DATABASE_URL"], row_factory=dict_row, prepare_threshold=None) as conn:
    rows = conn.execute(query + " order by created_at", params).fetchall()

with open(out / "metadata.jsonl", "w", encoding="utf-8") as f:
    for i, r in enumerate(rows, 1):
        dest = out / "audio" / r["audio_name"]
        if not dest.exists():                                   # re-runs only download new files
            s3.download_file(cfg["R2_BUCKET"], r["audio_name"], str(dest))
        f.write(json.dumps({
            "file_name": f"audio/{r['audio_name']}",
            "uuid": r["uuid"],
            "speaker_id": r["speaker_id"],
            "transcription": r["bambara"],
            "french": r["french"] or "",
            "duration": r["duration_sec"],
            "sample_rate": r["sample_rate"],
        }, ensure_ascii=False) + "\n")
        if i % 100 == 0:
            print(f"{i}/{len(rows)}")
print(f"Done: {len(rows)} recordings -> {out}/")
