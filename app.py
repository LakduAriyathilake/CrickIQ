import streamlit as st
from router import route_question, classify_question
from sql_agent import run_sql_query
from rag_agent import answer_from_knowledge

st.set_page_config(page_title="CrickIQ", page_icon="🏏")
st.title("🏏 CrickIQ")
st.caption("Hybrid RAG + Text-to-SQL Cricket Analytics Assistant — Men's & Women's T20 World Cup data")

# Keep chat history across interactions within a session
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display past messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# Chat input box at the bottom
user_question = st.chat_input("Ask about T20 World Cup stats or cricket rules...")

if user_question:
    # Show the user's message immediately
    st.session_state.messages.append({"role": "user", "content": user_question})
    with st.chat_message("user"):
        st.write(user_question)

    # Process and show the assistant's response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            category = classify_question(user_question)

            if "STATS" in category:
                columns, rows = run_sql_query(user_question)
                if rows is None or isinstance(rows, str):
                    answer = f"Sorry, I couldn't answer that: {rows}"
                else:
                    def format_value(v):
                        if isinstance(v, (int, float)) or hasattr(v, '__float__'):
                            try:
                                return f"{float(v):.2f}"
                            except (ValueError, TypeError):
                                return str(v)
                        return str(v)

                    header = " | ".join(columns)
                    lines = [" | ".join(format_value(v) for v in row) for row in rows]
                    answer = f"**{header}**\n\n" + "\n\n".join(lines)
            else:
                answer = answer_from_knowledge(user_question)

        st.write(answer)

    st.session_state.messages.append({"role": "assistant", "content": answer})