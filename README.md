# 🏏 CrickIQ — Hybrid RAG + Text-to-SQL Cricket Analytics Assistant

CrickIQ is a hybrid agentic system that answers cricket questions in natural language,
covering both the **ICC Men's T20 World Cup** and **ICC Women's T20 World Cup** in a
single unified dataset. A semantic router decides whether a question needs live
statistical analysis or conceptual/rules knowledge, then delegates to the
appropriate engine:

- **Text-to-SQL Agent** — converts natural language into PostgreSQL queries, run
  against a real ball-by-ball database (398 matches, ~92,000 deliveries).
- **RAG Agent** — retrieves from a ChromaDB knowledge base of cricket rules and
  concepts, then generates a grounded answer using only the retrieved context.
- **Semantic Router** — a lightweight LLM classification step that picks the right
  engine per question, so the system handles "who has the best economy rate in
  death overs?" and "what is the DLS method?" equally well from the same chat box.

---

## Demo

Ask things like:

- `Best economy rate in death overs`
- `Best strike rate in powerplay for women's matches`
- `What is the DLS method?`
- `How does a super over work?`

Each question is classified, routed, and answered live — stats questions return
real query results from the database; rules questions return explanations grounded
in the knowledge base (not the model's general training knowledge).

---

## Architecture