import streamlit as st
import pandas as pd
from router import route_question, classify_question
from sql_agent import run_sql_query
from rag_agent import answer_from_knowledge

st.set_page_config(page_title="CrickIQ", page_icon="🏏")

ACCENT = "#DD3240"  # single accent used for focus ring + send button, keep in sync

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&family=Inter:wght@400;500;600&display=swap');

html, body, [class*="css"] {{
    font-family: 'Inter', sans-serif;
}}

h1 {{
    font-family: 'Space Grotesk', sans-serif !important;
    font-weight: 700 !important;
    letter-spacing: -0.02em;
}}


/* Base message row */
[data-testid="stChatMessage"] {{
    display: flex;
    align-items: flex-start;
    gap: 10px;
    margin-bottom: 22px;
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 0 !important;
}}

[data-testid="stChatMessage"] > div {{
    margin: 0 !important;
}}

[data-testid="stChatMessageAvatarUser"],
[data-testid="stChatMessageAvatarAssistant"] {{
    width: 30px !important;
    height: 30px !important;
    min-width: 30px !important;
    border-radius: 50% !important;
    display: flex !important;
    align-items: center;
    justify-content: center;
    font-size: 15px !important;
    overflow: hidden;
    flex-shrink: 0;
}}
[data-testid="stChatMessageAvatarAssistant"] {{
    background: #2a2118;
}}
[data-testid="stChatMessageAvatarUser"] {{
    background: #3a1518;
    order: 2;
}}

[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {{
    justify-content: flex-end;
}}
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) > div:last-child {{
    order: 1;
    background: #2f2f33;
    color: #f1f1f1;
    border-radius: 20px;
    padding: 10px 16px;
    max-width: 65%;
    flex: 0 1 auto !important;
    width: fit-content;
}}

[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) > div:last-child {{
    background: transparent;
    color: #e5e5e5;
    padding: 4px 0;
    max-width: 90%;
}}

[data-testid="stChatInput"] {{
    display: flex !important;
    align-items: center !important;
    background: #1a1d21 !important;
    border: 1px solid #2f2f33 !important;
    border-radius: 28px !important;
    padding: 4px 6px 4px 20px !important;
    box-shadow: none !important;
    transition: border-color 0.15s ease, box-shadow 0.15s ease;
}}
[data-testid="stChatInput"] > div {{
    display: contents;
}}
[data-testid="stChatInput"]:focus-within {{
    border-color: {ACCENT} !important;
    box-shadow: 0 0 0 2px {ACCENT}55 !important;
}}

[data-testid="stChatInput"] textarea {{
    flex: 1 1 auto !important;
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    outline: none !important;
    padding: 10px 8px !important;
}}

[data-testid="stChatInput"] button {{
    flex: 0 0 auto !important;
    width: 34px !important;
    height: 34px !important;
    margin: 3px 3px 3px 3px !important;
    padding: 0 !important;
    border-radius: 50% !important;
    border: none !important;
    transition: background 0.15s ease, transform 0.15s ease, filter 0.15s ease, box-shadow 0.15s ease;
}}

[data-testid="stChatInput"] button:disabled {{
    background: #33383e !important;
    cursor: not-allowed !important;
    opacity: 0.7;
}}
[data-testid="stChatInput"] button:disabled svg {{
    fill: #6b7280 !important;
}}

[data-testid="stChatInput"] button:not(:disabled) {{
    background: {ACCENT} !important;
}}
[data-testid="stChatInput"] button:not(:disabled) svg {{
    fill: #0e0f11 !important;
}}

[data-testid="stChatInput"] button:not(:disabled):hover {{
    transform: scale(1.06);
    filter: brightness(1.08);
    box-shadow: 0 0 18px {ACCENT}66;
}}

[data-testid="stDataFrame"] {{
    border-radius: 14px;
    overflow: hidden;
}}

/* Compact "stat card" for small (1-2 row) results — label above value */
.stat-card-wrap {{
    display: flex;
    flex-direction: column;
    gap: 10px;
    margin: 4px 0;
}}
.stat-card {{
    display: flex;
    flex-wrap: wrap;
    gap: 24px;
    background: #1a1d21;
    border: 1px solid #2f2f33;
    border-radius: 14px;
    padding: 14px 20px;
}}
.stat-field {{
    display: flex;
    flex-direction: column;
    gap: 2px;
    min-width: 70px;
}}
.stat-label {{
    font-size: 11px;
    color: #8b94a3;
    text-transform: uppercase;
    letter-spacing: 0.04em;
}}
.stat-value {{
    font-size: 15px;
    color: #f1f1f1;
    font-weight: 600;
}}
</style>
""", unsafe_allow_html=True)


st.title("🏏 CrickIQ")
st.caption("Hybrid RAG + Text-to-SQL Cricket Analytics Assistant — Men's & Women's T20 World Cup data")


def render_stat_cards(df: pd.DataFrame):
    """Renders a small (1-2 row) result as clean label/value cards instead of
    a full data table or a cramped run-on line of bullets."""
    html = ['<div class="stat-card-wrap">']
    for _, row in df.iterrows():
        html.append('<div class="stat-card">')
        for col in df.columns:
            html.append(
                f'<div class="stat-field">'
                f'<span class="stat-label">{col}</span>'
                f'<span class="stat-value">{row[col]}</span>'
                f'</div>'
            )
        html.append('</div>')
    html.append('</div>')
    st.markdown("".join(html), unsafe_allow_html=True)


def render_answer(content):
    """Central rendering used both for a fresh answer and when redrawing
    chat history, so both look identical."""
    if isinstance(content, pd.DataFrame):
        df = content
        if len(df) == 1 and len(df.columns) == 1:
            st.write(str(df.iloc[0, 0]))
        elif len(df) <= 2:
            render_stat_cards(df)
        else:
            st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.write(content)


if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        render_answer(msg["content"])

user_question = st.chat_input("Ask about T20 World Cup stats or cricket rules...")

if user_question:
    st.session_state.messages.append({"role": "user", "content": user_question})
    with st.chat_message("user"):
        st.write(user_question)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            category = classify_question(user_question)

        if "STATS" in category:
                columns, rows = run_sql_query(user_question)
                if rows is None or isinstance(rows, str):
                    print(f"[SQL ERROR]: {rows}")
                    # Distinguish a rate-limit hit (sql_agent.py prefixes it
                    # with "RATE_LIMIT") from a genuinely out-of-scope question,
                    # since the two need different messages for the user.
                    if rows and rows.startswith("RATE_LIMIT"):
                        answer = ("I'm getting a lot of requests right now and hit a temporary "
                                  "usage limit. Please try again in a few minutes.")
                    else:
                        answer = ("I couldn't find that in the data — this assistant only covers "
                                    "ICC Men's and Women's T20 World Cup matches, not other tournaments, "
                                    "formats, or players/matches outside that scope.")
                    st.write(answer)
                elif len(rows) == 0 or all(v is None for v in rows[0]):
                    answer = ("I couldn't find that in the data — this assistant only covers "
                                "ICC Men's and Women's T20 World Cup matches, not other tournaments, "
                                "formats, or players/matches outside that scope.")
                    st.write(answer)
                else:
                    df = pd.DataFrame(rows, columns=columns)
                    for col in df.columns:
                        if df[col].apply(lambda x: isinstance(x, (int, float)) or hasattr(x, '__float__')).all():
                            try:
                                df[col] = df[col].astype(float)
                                # Whole-number columns (win counts, draws, etc.) should
                                # display as clean integers, not "10.0" — only genuinely
                                # fractional stats (strike rate, economy rate) keep decimals.
                                if (df[col].dropna() % 1 == 0).all():
                                    df[col] = df[col].astype(int)
                                else:
                                    df[col] = df[col].round(2)
                            except (ValueError, TypeError):
                                pass
                    render_answer(df)
                    answer = df
        else:
                answer = answer_from_knowledge(user_question)
                st.write(answer)

    st.session_state.messages.append({"role": "assistant", "content": answer})