# Deployment guide (exact steps, about 30 minutes)

You need four free accounts: **GitHub**, **Supabase**, **Cloudflare**, and **Streamlit Community Cloud** (sign in there with GitHub). Menu names below were checked against each service's documentation in October 2026; a button may be worded slightly differently, but the path is the same.

You will collect **6 values** along the way. Keep a notepad open:

| Value | Comes from |
|---|---|
| `DATABASE_URL` | Supabase, step 1 |
| `R2_ACCOUNT_ID` | Cloudflare, step 2 |
| `R2_ACCESS_KEY_ID` | Cloudflare, step 2 |
| `R2_SECRET_ACCESS_KEY` | Cloudflare, step 2 (shown only once) |
| `R2_BUCKET` | the bucket name you choose, step 2 |
| `ADMIN_PASSWORD` | you invent it (long, only for you) |

---

## 1. Supabase: the database

1. Go to supabase.com, sign in, **New project**. Choose a name, a region close to your contributors, and a **database password**. Use only letters and digits to avoid encoding problems, and save it. Wait until the project is ready.
2. Left menu → **SQL Editor** → **New query**. Open `schema.sql`, copy **all** of it, paste, press **Run**. You should see "Success. No rows returned".
3. Left menu → **Table Editor**. You should see two tables: `prompts` and `recordings`.
4. At the top of the project page click **Connect**, choose **Session pooler**, and copy the connection string. It looks like
   `postgresql://postgres.<project-ref>:[YOUR-PASSWORD]@aws-…-<region>.pooler.supabase.com:5432/postgres`
   Replace `[YOUR-PASSWORD]` (brackets included) with your database password. This is your `DATABASE_URL`.
   - Use **Session pooler**, not "Direct connection": the direct one is IPv6-only and Streamlit Cloud cannot reach it.
   - The host may start with `aws-0-` or `aws-1-`. Copy it exactly as shown.

## 2. Cloudflare R2: the audio files

1. Cloudflare dashboard → **R2 Object Storage**. If asked, complete the activation (a payment method may be requested; the free tier is 10 GB).
2. **Create bucket**, name it (for example `bambara-audio`), keep it **private**. Do not enable public access. That name is `R2_BUCKET`.
3. On the R2 overview page, copy your **Account ID** (32 characters): `R2_ACCOUNT_ID`.
4. Same page → **API Tokens → Manage** → **Create Account API token**:
   - Permission: **Object Read & Write**
   - Apply to specific buckets only → select your bucket
   - **Create API Token**
5. Copy the **Access Key ID** and the **Secret Access Key** right away. The secret is shown only once. If you lose it, create a new token.

## 3. GitHub: put the code online

Unzip `bambara-collector.zip`. Open a terminal **inside the unzipped folder** (the one that contains `app.py`), then:

```bash
git init
git add .
git commit -m "Bambara collector"
git branch -M main
git remote add origin https://github.com/<your-username>/bambara-collector.git
git push -u origin main
```

(Create the empty repository first on github.com → **New repository**, no README.) `app.py` and `requirements.txt` must be at the **top level** of the repository, not inside a sub-folder. Your secrets are never pushed: `.streamlit/secrets.toml` is in `.gitignore`.

## 4. Streamlit Community Cloud: the website

1. Go to share.streamlit.io and sign in with GitHub.
2. **Create app** (or **New app**) → deploy from a GitHub repository → choose your repository, branch `main`, main file path `app.py`.
3. Click **Advanced settings**:
   - **Python version: choose 3.12** (the code needs 3.10 or newer; do not leave an older default).
   - **Secrets**: paste this, with your 6 values:
     ```toml
     DATABASE_URL = "postgresql://postgres.xxxx:PASSWORD@aws-0-REGION.pooler.supabase.com:5432/postgres"
     R2_ACCOUNT_ID = "your-32-character-account-id"
     R2_ACCESS_KEY_ID = "your-access-key-id"
     R2_SECRET_ACCESS_KEY = "your-secret-access-key"
     R2_BUCKET = "bambara-audio"
     ADMIN_PASSWORD = "a-long-password-only-you-know"
     ```
4. **Deploy**. The first build takes a few minutes. You get a public address like `https://<name>.streamlit.app`.
5. To change a secret later: the app's menu → **Settings → Secrets**. Logs: **Manage app** (bottom right of the app).

## 5. First test (do all of it once)

1. Open the app. The sidebar shows 0 for every number, which is normal: no sentences yet.
2. Sidebar → **Admin** → enter `ADMIN_PASSWORD` → **Add one pair**: Bambara `I ni ce`, French `Bonjour`. Add one or two more.
3. Back to **app**: "Phrases restantes" now shows how many sentences were added. Enter a speaker ID such as `AT199503`, record a few seconds, tick the consent box, **Envoyer**.
4. Check the result:
   - Supabase → Table Editor → `recordings`: a new row with a `uuid`, your `speaker_id`, the texts and `audio_name`.
   - Cloudflare → R2 → your bucket → Objects: a file named `audio_AT199503_<uuid>.flac`, where `<uuid>` is the same as the row's `uuid`.
   - `prompts`: that sentence now has `recorded_count = 1` and no longer appears.

Then share the app address with contributors.

## What the sidebar numbers mean

| Label | Meaning |
|---|---|
| Enregistrements / Recordings | Number of rows in `recordings` (all submitted recordings) |
| Heures d'audio / Hours of audio | Sum of all recording durations |
| Locuteurs / Speakers | Number of different speaker IDs |
| **Phrases restantes / Sentences left** | Sentences added on the Admin page that still need a recording: those with `recorded_count` below `MAX_PER_PROMPT` (default 1, in `core.py`). It starts at 0, goes up when you add pairs, and goes down by one each time a sentence is recorded. It does not count "Say my own sentence" recordings. |

## Download the training data (on your computer, Python 3.11+)

```bash
pip install "psycopg[binary]" boto3
cp .streamlit/secrets.toml.example .streamlit/secrets.toml     # fill in the same 6 values
python export_dataset.py dataset
python export_dataset.py dataset --speaker AT199503 CD198507   # only some speakers
```

## If something goes wrong

| Message / symptom | Cause and fix |
|---|---|
| App says "Erreur du serveur" when submitting or loading a sentence | Open **Manage app** → logs; the Python error is shown there. The causes below are the usual ones. |
| `KeyError` / "No secrets found" / `st.secrets has no key …` | A secret is missing or misspelled. Names must match exactly (see step 4). |
| `Network is unreachable` or connection timeout to the database | `DATABASE_URL` is the *Direct connection*. Use the **Session pooler** string. |
| `password authentication failed` | Wrong database password. In Supabase: Database → Settings → reset the password, update `DATABASE_URL`. If the password contains `@ : / ? #`, replace it with letters and digits. |
| `Tenant or user not found` | The user must be `postgres.<project-ref>` (with the dot), exactly as copied from **Connect → Session pooler**. |
| `relation "prompts" does not exist` | `schema.sql` was not run, or was run on another project. Redo step 1.2. |
| `AccessDenied` / 403 from R2 | The token does not cover this bucket or lacks *Object Read & Write*. Create a new token (step 2.4). |
| `NoSuchBucket` | `R2_BUCKET` is misspelled or `R2_ACCOUNT_ID` belongs to another account. |
| `ModuleNotFoundError` or a syntax error on `str | None` | The Python version is too old. Settings → Python version → 3.12, then reboot the app. |
| The microphone does nothing | The browser blocked it: click the lock icon in the address bar → allow the microphone. The site must be opened over `https://` (Streamlit Cloud does this). |
| After some idle weeks the app errors on every database call | Supabase paused the free project (7 days without activity). Supabase dashboard → **Restore project**; data is kept. |
| "This app has gone to sleep" | Normal on the free plan. Click the button to wake it. |
