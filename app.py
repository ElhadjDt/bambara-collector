import logging

import streamlit as st

import core
from i18n import lang_picker, t

st.set_page_config(page_title="Bambara 🎙️", page_icon="🎙️")
ss = st.session_state
lang_picker()

# ---- state --------------------------------------------------------------------
ss.setdefault("nonce", 0)        # changing it gives us a fresh, empty recorder widget
ss.setdefault("count", 0)        # recordings sent during this session
ss.setdefault("prompt", None)    # sentence currently shown in "read a sentence" mode
ss.setdefault("bambara_txt", "")
ss.setdefault("french_txt", "")
if ss.pop("reset", False):       # runs *before* the widgets exist, so we may clear them
    ss.nonce += 1
    ss.bambara_txt = ""
    ss.french_txt = ""
    ss.prompt = None

st.title(t("title"))
if ss.pop("flash", False):
    st.success(t("saved"))

with st.sidebar:
    st.header(t("progress"))
    stats = core.get_stats()
    if stats:
        st.metric(t("m_recordings"), stats["recordings"])
        st.metric(t("m_hours"), f"{stats['hours']:.1f}")
        st.metric(t("m_speakers"), stats["speakers"])
        st.metric(t("m_left"), stats["left"])
    st.caption(t("sent_session", n=ss.count))

# ---- 1. speaker id ------------------------------------------------------------
st.subheader(t("h_speaker"))
st.caption(t("speaker_help"))
speaker = st.text_input(t("speaker_label"), key="speaker_id", placeholder="AT199503", max_chars=10).strip().upper()
speaker_ok = bool(core.SPEAKER_RE.match(speaker))
if speaker and not speaker_ok:
    st.warning(t("speaker_bad"))

# ---- 2. text ------------------------------------------------------------------
st.subheader(t("h_text"))
mode_labels = {"read": t("mode_read"), "own": t("mode_own")}
mode = st.radio("mode", list(mode_labels), key="mode", format_func=mode_labels.get,
                label_visibility="collapsed")

prompt_id = None
if mode == "read":
    if ss.prompt is None:
        try:
            ss.prompt = core.next_prompt()
            if ss.prompt is None:
                st.info(t("no_prompts"))
        except Exception:
            logging.exception("next_prompt failed")
            st.error(t("load_fail"))
    if ss.prompt:
        st.markdown(f"### {ss.prompt['bambara']}")
        if ss.prompt.get("french"):
            st.caption(ss.prompt["french"])
        if st.button(t("skip")):
            ss.prompt = None
            st.rerun()
        bambara_text = ss.prompt["bambara"]
        french_text = ss.prompt.get("french") or ""
        prompt_id = ss.prompt["id"]
    else:
        bambara_text = french_text = ""
else:
    def add_char():
        c = ss.get("pick")
        if c:
            ss.bambara_txt += c
        ss.pick = None

    st.text_area(t("bam_label"), key="bambara_txt", height=100)
    st.pills(t("pills"), core.SPECIAL_CHARS, key="pick", on_change=add_char)
    st.text_area(t("fr_label"), key="french_txt", height=80)
    bambara_text, french_text = ss.bambara_txt, ss.french_txt
    wrong = [c for c in "èéêëòóôõñ" if c in bambara_text]
    if wrong:
        st.warning(t("wrong_chars", chars=" ".join(wrong)))

# ---- 3. record ----------------------------------------------------------------
st.subheader(t("h_record"))
st.caption(t("record_help"))
audio = st.audio_input(
    t("record_label"), sample_rate=core.SAMPLE_RATE, key=f"rec_{ss.nonce}", label_visibility="collapsed"
)
consent = st.checkbox(t("consent"), key="consent")

if st.button(t("submit"), type="primary"):
    missing = []
    if not speaker_ok:
        missing.append(t("m_speaker_item"))
    if not bambara_text.strip():
        missing.append(t("m_bambara_item"))
    if audio is None:
        missing.append(t("m_audio_item"))
    if not consent:
        missing.append(t("m_consent_item"))
    if missing:
        st.error(t("missing", items=", ".join(missing)))
    else:
        error = None
        with st.spinner(t("uploading")):
            try:
                core.save_recording(audio.getvalue(), speaker, bambara_text, french_text, prompt_id)
            except core.UserError as e:
                error = t(f"err_{e.code}", min=core.MIN_SEC, max=core.MAX_SEC)
            except Exception:
                logging.exception("save_recording failed")
                error = t("err_server")
        if error:
            st.error(error)
        else:
            ss.count += 1
            ss.flash = True
            ss.reset = True
            core.get_stats.clear()
            st.rerun()
