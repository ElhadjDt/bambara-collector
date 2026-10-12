import hmac
import logging

import pandas as pd
import streamlit as st

import core
from i18n import lang_picker, t

st.set_page_config(page_title="Admin", page_icon="🗂️")
lang_picker()
st.title(t("admin_title"))
st.caption(t("admin_caption"))

pw = st.text_input(t("admin_pw"), type="password")
if not pw:
    st.stop()
if not hmac.compare_digest(pw.encode(), st.secrets["ADMIN_PASSWORD"].encode()):
    st.error(t("admin_wrong"))
    st.stop()


def send(rows):
    try:
        received, inserted = core.add_prompts(rows)
        st.success(t("added", inserted=inserted, skipped=received - inserted))
        core.get_stats.clear()
    except Exception:
        logging.exception("add_prompts failed")
        st.error(t("err_server"))


tab_one, tab_bulk, tab_list = st.tabs([t("tab_one"), t("tab_bulk"), t("tab_list")])

with tab_one:
    with st.form("one", clear_on_submit=True):
        bam = st.text_area(t("bambara"))
        fr = st.text_area(t("french"))
        if st.form_submit_button(t("add")) and bam.strip():
            send([{"bambara": bam, "french": fr}])

with tab_bulk:
    st.markdown(t("paste_help"))
    pasted = st.text_area(t("paste_label"), height=160, placeholder="I ni ce | Bonjour\nI ka kɛnɛ wa? | Comment vas-tu ?")
    st.markdown(t("csv_help"))
    csv = st.file_uploader("CSV", type=["csv"])

    rows = []
    for line in pasted.splitlines():
        if line.strip():
            b, _, f = line.partition("|")
            rows.append({"bambara": b.strip(), "french": f.strip()})
    if csv is not None:
        df = pd.read_csv(csv, dtype=str, encoding="utf-8-sig", keep_default_na=False)
        if "bambara" not in df.columns:
            st.error(t("csv_no_col"))
        else:
            rows += df.reindex(columns=["bambara", "french"], fill_value="").to_dict("records")

    if rows:
        st.dataframe(pd.DataFrame(rows).head(50))
        st.caption(t("preview", n=len(rows)))
        if st.button(t("import"), type="primary"):
            send(rows)

with tab_list:
    try:
        total, items = core.list_prompts(200)
        st.caption(t("list_caption", total=total))
        st.dataframe(pd.DataFrame(items))
    except Exception:
        logging.exception("list_prompts failed")
        st.error(t("err_server"))
