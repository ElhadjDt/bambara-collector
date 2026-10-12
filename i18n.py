"""French / English texts and the language switch (shared by all pages)."""
import streamlit as st

DEFAULT_LANG = "fr"        # language shown on first visit: "fr" or "en"

STR = {
    "fr": {
        "title": "🎙️ Collecte vocale en bambara",
        "progress": "Progression",
        "m_recordings": "Enregistrements",
        "m_hours": "Heures d'audio",
        "m_speakers": "Locuteurs",
        "m_left": "Phrases restantes",
        "sent_session": "Envoyés par vous pendant cette session : {n}",
        "h_speaker": "1 · Votre identifiant locuteur",
        "speaker_help": "Initiales du prénom et du nom + année de naissance + mois de naissance.  \n"
                        "Exemple : **Amadou Traoré**, né en **mars 1995** → `AT199503`",
        "speaker_label": "Identifiant locuteur",
        "speaker_bad": "Format : 1 à 4 lettres, puis l'année de naissance (4 chiffres), puis le mois de naissance "
                       "(2 chiffres), par exemple AT199503.",
        "h_text": "2 · Qu'allez-vous dire ?",
        "mode_read": "Lire une phrase proposée",
        "mode_own": "Dire ma propre phrase",
        "no_prompts": "Toutes les phrases ont été enregistrées 🎉 Choisissez « Dire ma propre phrase ». Merci !",
        "load_fail": "Impossible de charger une phrase. Veuillez réessayer.",
        "skip": "⏭ Passer cette phrase",
        "bam_label": "Texte en bambara (orthographe standard)",
        "pills": "Lettres spéciales : touchez pour les ajouter à la fin du texte",
        "fr_label": "Traduction en français (recommandée)",
        "wrong_chars": "Le texte bambara contient {chars}. Vouliez-vous écrire ɛ, ɔ ou ɲ ?",
        "h_record": "3 · Enregistrer",
        "record_help": "Placez-vous dans un endroit calme. Appuyez sur le micro, parlez clairement, appuyez sur "
                       "stop, puis réécoutez. Pas satisfait ? Enregistrez à nouveau.",
        "record_label": "Enregistrement",
        "consent": "J'accepte que mon enregistrement vocal et ces textes soient utilisés pour constituer des "
                   "jeux de données ouverts de reconnaissance vocale et de traduction en bambara.",
        "submit": "✅ Envoyer",
        "missing": "Il manque : {items}",
        "m_speaker_item": "un identifiant valide",
        "m_bambara_item": "le texte bambara",
        "m_audio_item": "un enregistrement",
        "m_consent_item": "votre consentement",
        "uploading": "Envoi en cours…",
        "saved": "✅ Enregistré. Merci ! Vous pouvez en faire un autre.",
        "err_speaker": "Identifiant invalide. Exemple : AT199503.",
        "err_text": "Le texte bambara est obligatoire (500 caractères maximum).",
        "err_unreadable": "Impossible de lire l'audio. Veuillez réenregistrer.",
        "err_duration": "L'enregistrement doit durer entre {min:.0f} et {max:.0f} secondes.",
        "err_silent": "L'enregistrement semble silencieux. Vérifiez votre micro et réessayez.",
        "err_server": "Erreur du serveur, rien n'a été enregistré. Veuillez réessayer dans un instant.",
        "admin_title": "🗂️ Paires de phrases (admin)",
        "admin_caption": "Les paires ajoutées ici apparaissent dans « Lire une phrase proposée ». "
                         "Une fois enregistrée, une phrase quitte la liste.",
        "admin_pw": "Mot de passe admin",
        "admin_wrong": "Mot de passe incorrect.",
        "tab_one": "Ajouter une paire",
        "tab_bulk": "Import en masse",
        "tab_list": "Phrases existantes",
        "bambara": "Bambara",
        "french": "Français",
        "add": "Ajouter",
        "paste_help": "**Option A : coller** une paire par ligne : `bambara | français`",
        "paste_label": "Paires",
        "csv_help": "**Option B : fichier CSV** avec les colonnes `bambara` et `french`, enregistré en **UTF-8** "
                    "(nécessaire pour ɛ ɔ ɲ ŋ)",
        "csv_no_col": "Le CSV doit contenir une colonne `bambara`.",
        "preview": "{n} paire(s) prête(s) à importer (aperçu : 50 premières).",
        "import": "Importer",
        "added": "{inserted} nouvelle(s) phrase(s) ajoutée(s) ({skipped} ignorée(s) : doublons ou invalides).",
        "list_caption": "{total} phrase(s) au total (200 dernières affichées).",
    },
    "en": {
        "title": "🎙️ Bambara voice collection",
        "progress": "Progress",
        "m_recordings": "Recordings",
        "m_hours": "Hours of audio",
        "m_speakers": "Speakers",
        "m_left": "Sentences left",
        "sent_session": "Sent by you in this session: {n}",
        "h_speaker": "1 · Your speaker ID",
        "speaker_help": "Initials of your first and last name + year of birth + month of birth.  \n"
                        "Example: **Amadou Traoré**, born in **March 1995** → `AT199503`",
        "speaker_label": "Speaker ID",
        "speaker_bad": "Format: 1–4 letters, then the 4-digit birth year, then the 2-digit birth month "
                       "(e.g. AT199503).",
        "h_text": "2 · What will you say?",
        "mode_read": "Read a sentence given to me",
        "mode_own": "Say my own sentence",
        "no_prompts": "All sentences have been recorded 🎉 Please switch to “Say my own sentence”. Thank you!",
        "load_fail": "Could not load a sentence. Please try again.",
        "skip": "⏭ Skip this sentence",
        "bam_label": "Bambara text (standard orthography)",
        "pills": "Special letters: tap to add at the end of the text",
        "fr_label": "French translation (recommended)",
        "wrong_chars": "The Bambara text contains {chars}. Did you mean ɛ, ɔ or ɲ?",
        "h_record": "3 · Record",
        "record_help": "Find a quiet place. Press the microphone, speak clearly, press stop, then listen back. "
                       "Not happy? Record again.",
        "record_label": "Recording",
        "consent": "I agree that my voice recording and these texts are used to build open Bambara "
                   "speech and translation datasets.",
        "submit": "✅ Submit",
        "missing": "Missing: {items}",
        "m_speaker_item": "a valid speaker ID",
        "m_bambara_item": "the Bambara text",
        "m_audio_item": "a recording",
        "m_consent_item": "your consent",
        "uploading": "Uploading…",
        "saved": "✅ Saved. Thank you! You can record another one.",
        "err_speaker": "Invalid speaker ID. Example: AT199503.",
        "err_text": "The Bambara text is required (500 characters max).",
        "err_unreadable": "Could not read the audio. Please record again.",
        "err_duration": "The recording must last between {min:.0f} and {max:.0f} seconds.",
        "err_silent": "The recording seems silent. Check your microphone and try again.",
        "err_server": "Server error, nothing was saved. Please try again in a moment.",
        "admin_title": "🗂️ Sentence pairs (admin)",
        "admin_caption": "Pairs added here appear in “Read a sentence given to me”. "
                         "Once a sentence has been recorded, it leaves the pool.",
        "admin_pw": "Admin password",
        "admin_wrong": "Wrong password.",
        "tab_one": "Add one pair",
        "tab_bulk": "Bulk import",
        "tab_list": "Existing sentences",
        "bambara": "Bambara",
        "french": "French",
        "add": "Add",
        "paste_help": "**Option A: paste** one pair per line as `bambara | french`",
        "paste_label": "Pairs",
        "csv_help": "**Option B: CSV file** with columns `bambara` and `french`, saved as **UTF-8** "
                    "(needed for ɛ ɔ ɲ ŋ)",
        "csv_no_col": "The CSV needs a `bambara` column.",
        "preview": "{n} pair(s) ready to import (preview shows the first 50).",
        "import": "Import",
        "added": "{inserted} new sentence(s) added ({skipped} skipped as duplicates/invalid).",
        "list_caption": "{total} sentence(s) in total (latest 200 shown).",
    },
}


def t(key: str, **kw) -> str:
    return STR[st.session_state.get("lang", DEFAULT_LANG)][key].format(**kw)


def lang_picker():
    """Call once at the top of every page: language radio in the sidebar, remembered across pages."""
    st.session_state.setdefault("lang", DEFAULT_LANG)
    st.sidebar.radio(
        "🌐 Langue / Language",
        ["fr", "en"],
        key="lang",
        format_func={"fr": "Français", "en": "English"}.get,
        horizontal=True,
    )
