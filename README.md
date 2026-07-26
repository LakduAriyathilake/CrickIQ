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

User question
                         │
                Streamlit Chat UI (app.py)
                         │
                Semantic Router (router.py)
                (Groq / Llama-3.3-70B classifier)
                         │
          ┌──────────────┴──────────────┐
          │                             │
    STATS question                RULES question
          │                             │
  Text-to-SQL Agent               RAG Agent
  (sql_agent.py)                  (rag_agent.py)
          │                             │
  Groq generates SQL           ChromaDB retrieves
  from schema + domain         top-3 relevant docs
  conventions                          │
          │                    Groq generates answer
  Query runs against           grounded in retrieved
  PostgreSQL (Supabase)        context only
          │                             │
          └──────────────┬──────────────┘
                         │
                  Formatted answer
                 back to chat UI


---

## Tech Stack

| Layer | Tools |
|---|---|
| Data engineering | Python, pandas, Google Colab |
| Database | PostgreSQL (hosted on Supabase) |
| Vector store | ChromaDB (persistent, local) |
| Embeddings | sentence-transformers (`all-MiniLM-L6-v2`) |
| LLM | Groq API — Llama-3.3-70B-Versatile |
| Orchestration | SQLAlchemy, python-dotenv |
| UI | Streamlit |

---

## Data Pipeline

1. **Source**: [Cricsheet.org](https://cricsheet.org) — ICC Men's & Women's T20 World Cup, ball-by-ball JSON data.
2. **ETL** (Google Colab): parsed raw JSON into two structured tables —
   `matches` (398 rows) and `deliveries` (~92,000 rows) — with a shared `gender`
   column so both competitions live in one unified schema instead of two
   disconnected datasets.
3. **Load**: cleaned data loaded into PostgreSQL via Supabase (connection pooler,
   for IPv4 compatibility with cloud notebooks).
4. **Validation**: hand-written SQL queries (powerplay strike rate, death-overs
   economy, venue analysis, head-to-head records) were run and manually verified
   against known cricket outcomes — these became the ground truth benchmark for
   validating the Text-to-SQL agent's generated queries.

---

## Project Structure

CrickIQ/
├── app.py # Streamlit chat UI
├── router.py # Semantic router (STATS vs RULES classification)
├── sql_agent.py # Text-to-SQL agent + domain-grounded schema prompt
├── rag_agent.py # RAG agent (retrieval + grounded generation)
├── build_knowledge_base.py # Embeds knowledge_base/*.txt into ChromaDB
├── populate_knowledge_base.py # Generates the knowledge base .txt files
├── test_retrieval.py # Retrieval quality diagnostic script
├── knowledge_base/ # 12 cricket rules/concept documents
├── requirements.txt
├── .gitignore
└── README.md

---

## Setup & Running Locally

### 1. Clone and set up environment
```bash
git clone https://github.com/LakduAriyathilake/CrickIQ.git
cd CrickIQ
python -m venv venv
venv\Scripts\activate      # Windows
# source venv/bin/activate # Mac/Linux
pip install -r requirements.txt
```

### 2. Configure secrets
Create a `.env` file in the project root:

GROQ_API_KEY=your_groq_api_key
DATABASE_URL=your_postgresql_connection_string

### 3. Build the knowledge base
```bash
python populate_knowledge_base.py
python build_knowledge_base.py
```

### 4. Run the app
```bash
streamlit run app.py
```

---

## Key Engineering Decisions

- **Unified schema, not separate datasets**: men's and women's data share one
  schema with a `gender` column, rather than two separate tables/databases —
  this lets every query and every UI question work across both competitions
  without duplicated logic.
- **Domain-grounded SQL prompting**: rather than trusting the LLM to infer
  cricket-specific conventions (e.g. strike rate formula, minimum sample sizes),
  the schema prompt explicitly encodes these — validated by comparing generated
  SQL results against hand-written, manually-verified queries.
- **Anti-hallucination RAG**: the RAG agent is explicitly instructed to answer
  using only retrieved context, and retrieves the top-3 candidate documents
  (not just the top-1) to stay robust to imperfect embedding rankings.
- **Player name matching**: since Cricsheet stores names as initials + surname
  (e.g. `S Mandhana`), the SQL agent is instructed to match player names via
  partial, case-insensitive search on the surname rather than exact match.

---

## Future Improvements

- Add ODI and Test match data alongside T20 World Cup data
- Expand the knowledge base with more nuanced rules (DRS edge cases, fielding
  restrictions across formats)
- Add a lightweight caching layer for repeated SQL queries
- Deploy to Streamlit Community Cloud for a public live demo link